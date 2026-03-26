"""Check consistency between Parameter/Descriptor definitions and their
public properties.

Three checks are performed for every public property whose getter
returns a GenericDescriptorBase subclass instance:

1. **Docstring vs description** – The first sentence of the property
   getter docstring must match the ``description`` string of the
   backing Parameter/Descriptor (case-insensitive, ignoring trailing
   punctuation and markup).

2. **Getter return-type annotation vs backing attribute type** – The
   annotation on the getter (e.g. ``-> Parameter``) must resolve to a
   type (or union containing a type) that the runtime object is an
   instance of.  Union, Optional, and Annotated wrappers are
   decomposed structurally.

3. **Setter value-type annotation vs descriptor data type** – For
   numeric descriptors the setter ``value`` argument must be annotated
   with a type drawn from ``{int, float}`` (per PEP 484 numeric
   tower, ``float`` alone is the canonical form).  For string
   descriptors it must be ``str``.  Annotations are decomposed
   structurally, so ``float``, ``int | float``, ``float | int`` are
   all accepted for numeric descriptors.

The script instantiates every concrete ``CategoryItem`` and
``CategoryCollection`` subclass found under ``src/easydiffraction/``
and introspects properties at runtime.

Exit code 0 when all checks pass, 1 otherwise.  Import and
instantiation failures are reported explicitly rather than silently
skipped.
"""

from __future__ import annotations

import contextlib
import importlib
import inspect
import pkgutil
import re
import sys
import types
from pathlib import Path
from typing import Union
from typing import get_args
from typing import get_origin
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
# Known intermediate bases that require constructor arguments and have
# no descriptor-backed properties of their own.  Their concrete leaves
# (PdCwlData, PdTofData, TotalData, etc.) *are* checked.
# If a class is skipped and NOT listed here, the check fails.
# ---------------------------------------------------------------------------

_KNOWN_INTERMEDIATE_BASES: frozenset[str] = frozenset({
    'PdDataBase',
    'TotalDataBase',
})


# ---------------------------------------------------------------------------
# Discovery helpers
# ---------------------------------------------------------------------------


def _import_all_submodules(package_name: str) -> list[str]:
    """Recursively import every submodule of *package_name*.

    Returns:
        List of module names that failed to import.
    """
    package = importlib.import_module(package_name)
    prefix = package.__name__ + '.'
    failed: list[str] = []
    for _importer, modname, _ispkg in pkgutil.walk_packages(package.__path__, prefix=prefix):
        try:
            importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001
            failed.append(f'{modname}: {exc}')
    return failed


def _concrete_subclasses(base: type) -> set[type]:
    """Return all non-abstract subclasses of *base* (deep)."""
    result: set[type] = set()
    for sub in base.__subclasses__():
        if not inspect.isabstract(sub):
            result.add(sub)
        result.update(_concrete_subclasses(sub))
    return result


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

_TRAILING_PUNCT = re.compile(r'[.\s]+$')
_MARKDOWN_EMPHASIS = re.compile(r'\*{1,2}([^*]+)\*{1,2}')
_RST_ROLE = re.compile(r':[a-z]+:`([^`]+)`')
_DOUBLE_BACKTICK = re.compile(r'``([^`]+)``')
_UNICODE_DASHES = re.compile(r'[\u2013\u2014]')  # en-dash, em-dash


def _normalise(text: str) -> str:
    """Lower-case, strip markup formatting, normalise dashes and
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
# Structural type extraction
# ---------------------------------------------------------------------------

# Allowed concrete types for setter annotations
_NUMERIC_ALLOWED: frozenset[type] = frozenset({int, float})
_STRING_ALLOWED: frozenset[type] = frozenset({str})


def _extract_types(annotation: object) -> tuple[type, ...]:
    """Extract concrete type objects from an annotation.

    Handles plain types, ``X | Y`` (types.UnionType),
    ``typing.Union[X, Y]``, and ``typing.Optional[X]``.
    ``NoneType`` members are filtered out.

    Returns:
        Tuple of concrete types, or empty tuple when the annotation
        cannot be decomposed (e.g. ``Any``, unresolved forward ref).
    """
    origin = get_origin(annotation)
    if origin is types.UnionType or origin is Union:
        return tuple(
            a for a in get_args(annotation) if isinstance(a, type) and a is not type(None)
        )
    if isinstance(annotation, type):
        return (annotation,)
    return ()


# ---------------------------------------------------------------------------
# Main checking logic
# ---------------------------------------------------------------------------


def _check_class(cls: type, instance: object, errors: list[str]) -> None:
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
            hints: dict = {}
            with contextlib.suppress(Exception):
                hints = get_type_hints(getter)
            ret = hints.get('return')

            if ret is None:
                errors.append(
                    f'{loc}: getter has no return-type annotation (expected {type(val).__name__})'
                )
            else:
                ret_types = _extract_types(ret)
                if not ret_types:
                    errors.append(
                        f'{loc}: getter return annotation "{ret}" '
                        f'could not be structurally verified '
                        f'(expected {type(val).__name__})'
                    )
                elif not any(isinstance(val, t) for t in ret_types):
                    names = ' | '.join(t.__name__ for t in ret_types)
                    errors.append(
                        f'{loc}: getter return annotation '
                        f'{names} does not match runtime type '
                        f'{type(val).__name__}'
                    )

        # ---------------------------------------------------------------
        # Check 3: setter value-type annotation
        # ---------------------------------------------------------------
        if setter is not None:
            setter_hints: dict = {}
            with contextlib.suppress(Exception):
                setter_hints = get_type_hints(setter)

            sig = inspect.signature(setter)
            params = [p for name, p in sig.parameters.items() if name != 'self']
            if not params:
                continue

            value_param = params[0]
            # Prefer resolved hint over raw signature annotation
            resolved_ann = setter_hints.get(value_param.name)
            raw_ann = value_param.annotation

            if resolved_ann is None and raw_ann is inspect.Parameter.empty:
                is_numeric = isinstance(val, GenericNumericDescriptor)
                is_string = isinstance(val, GenericStringDescriptor)
                expected = 'float' if is_numeric else 'str' if is_string else '?'
                errors.append(
                    f'{loc}: setter parameter '
                    f'"{value_param.name}" has no type '
                    f'annotation (expected {expected})'
                )
            else:
                ann = resolved_ann if resolved_ann is not None else raw_ann
                ann_types = _extract_types(ann)

                if not ann_types:
                    errors.append(
                        f'{loc}: setter annotation "{ann}" could not be structurally verified'
                    )
                elif isinstance(val, GenericNumericDescriptor) and not set(ann_types).issubset(
                    _NUMERIC_ALLOWED
                ):
                    names = ' | '.join(t.__name__ for t in ann_types)
                    errors.append(
                        f'{loc}: setter annotated '
                        f'"{names}" for a numeric '
                        f'descriptor (expected float)'
                    )
                elif isinstance(val, GenericStringDescriptor) and not set(ann_types).issubset(
                    _STRING_ALLOWED
                ):
                    names = ' | '.join(t.__name__ for t in ann_types)
                    errors.append(
                        f'{loc}: setter annotated "{names}" for a string descriptor (expected str)'
                    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
    """Run all consistency checks and print results."""
    # Import everything so all subclasses are registered
    import_failures = _import_all_submodules('easydiffraction')
    if import_failures:
        print(f'\n⚠️  {len(import_failures)} module(s) failed to import:')
        for msg in import_failures:
            print(f'    {msg}')
        print()

    errors: list[str] = []
    checked = 0
    skipped: list[str] = []
    unexpected_skips: list[str] = []

    all_targets: list[type] = []
    for base in (CategoryItem, CategoryCollection):
        for cls in sorted(_concrete_subclasses(base), key=lambda c: c.__name__):
            all_targets.append(cls)

    for cls in all_targets:
        try:
            instance = cls()
        except Exception as exc:  # noqa: BLE001
            name = cls.__name__
            if name in _KNOWN_INTERMEDIATE_BASES:
                skipped.append(f'{name} (expected: {exc})')
            else:
                unexpected_skips.append(f'{name}: {exc}')
            continue

        _check_class(cls, instance, errors)
        checked += 1

    # Report skipped intermediate bases (informational)
    if skipped:
        print(f'ℹ️  {len(skipped)} known intermediate base(s) skipped:')
        for msg in skipped:
            print(f'    {msg}')
        print()

    # Unexpected skips are errors
    if unexpected_skips:
        print(f'❌ {len(unexpected_skips)} class(es) unexpectedly failed to instantiate:')
        for msg in unexpected_skips:
            print(f'    {msg}')
        print('   Add to _KNOWN_INTERMEDIATE_BASES if this is expected, or fix the constructor.\n')

    # Summary
    print(f'Checked {checked} classes')
    if errors or unexpected_skips:
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
