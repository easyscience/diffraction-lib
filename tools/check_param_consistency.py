"""Check consistency between Parameter/Descriptor definitions and their
public properties.

Three checks are performed for every public property whose getter
returns a GenericDescriptorBase subclass instance:

1. **Docstring vs description** – The first sentence of the property
   getter docstring must match the ``description`` string of the
   backing Parameter/Descriptor (case-insensitive, ignoring trailing
   punctuation).

2. **Getter return-type annotation vs backing attribute type** – The
   annotation on the getter (e.g. ``-> Parameter``) must be the exact
   class (or a superclass) of the object stored in ``self._<name>``.

3. **Setter value-type annotation vs descriptor data type** – For
   numeric descriptors the setter ``value`` argument must be annotated
   ``float`` (per PEP 484, ``int`` is implicitly accepted wherever
   ``float`` is declared).  For string descriptors it must be ``str``.

The script instantiates every concrete ``CategoryItem`` subclass found
under ``src/easydiffraction/`` and introspects properties at runtime.

Exit code 0 when all checks pass, 1 otherwise.
"""

from __future__ import annotations

import contextlib
import importlib
import inspect
import pkgutil
import re
import sys
from pathlib import Path
from typing import get_type_hints

# ---------------------------------------------------------------------------
# Bootstrap: make sure the package is importable
# ---------------------------------------------------------------------------

_repo = Path(__file__).resolve().parents[1]
_src = _repo / 'src'
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from easydiffraction.core.category import CategoryCollection  # noqa: E402
from easydiffraction.core.category import CategoryItem  # noqa: E402
from easydiffraction.core.variable import GenericDescriptorBase  # noqa: E402
from easydiffraction.core.variable import GenericNumericDescriptor  # noqa: E402
from easydiffraction.core.variable import GenericStringDescriptor  # noqa: E402

# ---------------------------------------------------------------------------
# Discovery helpers
# ---------------------------------------------------------------------------


def _import_all_submodules(package_name: str) -> None:
    """Recursively import every submodule of *package_name*."""
    package = importlib.import_module(package_name)
    prefix = package.__name__ + '.'
    for _importer, modname, _ispkg in pkgutil.walk_packages(package.__path__, prefix=prefix):
        with contextlib.suppress(Exception):
            importlib.import_module(modname)


def _concrete_subclasses(base):
    """Return all non-abstract subclasses of *base* (deep)."""
    result = set()
    for sub in base.__subclasses__():
        if not inspect.isabstract(sub):
            result.add(sub)
        result.update(_concrete_subclasses(sub))
    return result


def _safe_instantiate(cls):
    """Try to call ``cls()`` with no arguments.  Return None on failure."""
    try:
        return cls()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

_TRAILING_PUNCT = re.compile(r'[.\s]+$')
_MARKDOWN_EMPHASIS = re.compile(r'\*{1,2}([^*]+)\*{1,2}')
_RST_ROLE = re.compile(r':[a-z]+:`([^`]+)`')
_DOUBLE_BACKTICK = re.compile(r'``([^`]+)``')
_UNICODE_DASHES = re.compile(r'[\u2013\u2014]')  # en-dash, em-dash


def _normalise(text: str) -> str:
    """Lower-case, strip markdown/rst formatting, normalise dashes and
    trailing punctuation."""
    t = _MARKDOWN_EMPHASIS.sub(r'\1', text)
    t = _RST_ROLE.sub(r'\1', t)
    t = _DOUBLE_BACKTICK.sub(r'\1', t)
    t = _UNICODE_DASHES.sub('-', t)
    return _TRAILING_PUNCT.sub('', t.strip()).lower()


def _first_sentence(docstring: str | None) -> str:
    """Extract the first paragraph / sentence from a docstring."""
    if not docstring:
        return ''
    first_para = docstring.strip().split('\n\n')[0]
    return ' '.join(line.strip() for line in first_para.splitlines())


# ---------------------------------------------------------------------------
# Expected setter annotation per descriptor family
# ---------------------------------------------------------------------------

_NUMERIC_SETTER_TYPES = {'float', 'int | float', 'int|float'}
_STRING_SETTER_TYPES = {'str'}


# ---------------------------------------------------------------------------
# Main checking logic
# ---------------------------------------------------------------------------


def _check_class(cls, instance, errors: list[str]) -> None:
    """Run all three checks for *cls* using the given *instance*."""

    # Collect all property objects from the MRO
    props: dict[str, property] = {}
    for base in cls.__mro__:
        for key, val in base.__dict__.items():
            if isinstance(val, property) and not key.startswith('_'):
                props.setdefault(key, val)

    for prop_name, prop_obj in props.items():
        # Retrieve the runtime value
        try:
            val = getattr(instance, prop_name)
        except Exception:  # noqa: BLE001, S112
            continue

        if not isinstance(val, GenericDescriptorBase):
            continue

        getter = prop_obj.fget
        setter = prop_obj.fset
        loc = f'{cls.__name__}.{prop_name}'

        # ---------------------------------------------------------------
        # Check 1: docstring vs description
        # ---------------------------------------------------------------
        description = getattr(val, '_description', None) or ''
        doc = _first_sentence(getter.__doc__) if getter and getter.__doc__ else ''

        if description and not doc:
            errors.append(
                f'{loc}: getter has no docstring, but Parameter description is "{description}"'
            )
        elif description and doc and _normalise(doc) != _normalise(description):
            errors.append(
                f'{loc}: docstring first sentence does not match '
                f'Parameter description.\n'
                f'    docstring:   "{doc}"\n'
                f'    description: "{description}"'
            )

        # ---------------------------------------------------------------
        # Check 2: getter return-type annotation
        # ---------------------------------------------------------------
        if getter is not None:
            hints = {}
            with contextlib.suppress(Exception):
                hints = get_type_hints(getter)
            ret = hints.get('return')

            if ret is None:
                errors.append(
                    f'{loc}: getter has no return-type annotation (expected {type(val).__name__})'
                )
            elif isinstance(ret, type) and not isinstance(val, ret):
                errors.append(
                    f'{loc}: getter return annotation is '
                    f'{ret.__name__}, but runtime object is '
                    f'{type(val).__name__}'
                )

        # ---------------------------------------------------------------
        # Check 3: setter value-type annotation
        # ---------------------------------------------------------------
        if setter is not None:
            hints = {}
            with contextlib.suppress(Exception):
                hints = get_type_hints(setter)

            # The setter's first (non-self) parameter should be 'value'
            sig = inspect.signature(setter)
            params = [p for name, p in sig.parameters.items() if name != 'self']
            if params:
                value_param = params[0]
                ann = value_param.annotation
                if ann is inspect.Parameter.empty:
                    is_numeric = isinstance(val, GenericNumericDescriptor)
                    is_string = isinstance(val, GenericStringDescriptor)
                    expected = 'float' if is_numeric else 'str' if is_string else '?'
                    errors.append(
                        f'{loc}: setter parameter '
                        f'"{value_param.name}" has no type '
                        f'annotation (expected {expected})'
                    )
                else:
                    ann_str = ann.__name__ if isinstance(ann, type) else str(ann)
                    if (
                        isinstance(val, GenericNumericDescriptor)
                        and ann_str.lower() not in _NUMERIC_SETTER_TYPES
                    ):
                        errors.append(
                            f'{loc}: setter annotated '
                            f'"{ann_str}" for a numeric '
                            f'descriptor (expected float)'
                        )
                    elif (
                        isinstance(val, GenericStringDescriptor)
                        and ann_str.lower() not in _STRING_SETTER_TYPES
                    ):
                        errors.append(
                            f'{loc}: setter annotated '
                            f'"{ann_str}" for a string '
                            f'descriptor (expected str)'
                        )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
    """Run all consistency checks and print results."""
    # Import everything so all subclasses are registered
    _import_all_submodules('easydiffraction')

    errors: list[str] = []
    checked = 0

    # Check CategoryItem subclasses
    for cls in sorted(_concrete_subclasses(CategoryItem), key=lambda c: c.__name__):
        instance = _safe_instantiate(cls)
        if instance is None:
            continue
        _check_class(cls, instance, errors)
        checked += 1

    # Also check CategoryCollection subclasses (some hold descriptors)
    for cls in sorted(_concrete_subclasses(CategoryCollection), key=lambda c: c.__name__):
        instance = _safe_instantiate(cls)
        if instance is None:
            continue
        _check_class(cls, instance, errors)
        checked += 1

    # Summary
    print(f'\nChecked {checked} classes')
    if errors:
        print(f'\n❌ {len(errors)} consistency issue(s) found:\n')
        for i, err in enumerate(errors, 1):
            print(f'  {i}. {err}\n')
        return 1
    else:
        print('✅ All parameter-property consistency checks passed.')
        return 0


if __name__ == '__main__':
    sys.exit(main())
