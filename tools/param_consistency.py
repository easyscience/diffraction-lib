"""Check and fix consistency between Parameter/Descriptor definitions
and their public property docstrings and type annotations.

Usage:
    python param_consistency.py --check                # validate (exit code 0/1)
    python param_consistency.py --fix                  # auto-fix docstrings and type hints
    python param_consistency.py src/mypackage/ --check  # scan only a specific directory

Template (see docs/architecture/architecture.md §9.8 for the full spec)
-----------------------------------------------------------------------
Given ``description='Length of the a axis of the unit cell.'``,
``units='Å'``, and type ``Parameter``:

Getter::

    @property
    def length_a(self) -> Parameter:
        \"""Length of the a axis of the unit cell.

        Returns:
            Parameter: Length of the a axis of the unit cell (Å).
        \"""
        return self._length_a

Setter::

    @length_a.setter
    def length_a(self, value: float) -> None:
        \"""Set the length of the a axis of the unit cell.

        Args:
            value (float): Length of the a axis of the unit cell (Å).
        \"""
        self._length_a.value = value

Rules:
- ``{desc}`` = description without trailing period (single source of truth).
- ``{units}`` = units string; omit ``({units})`` when absent or empty.
- Getter return annotation: the descriptor class name.
- Setter value annotation: ``float`` for numeric, ``str`` for string.
- Setter return annotation: ``None``.
- Setter ``Args`` uses the **actual parameter name** (conventionally
  ``value``).

Exit code 0 when all checks pass (or fix succeeds), 1 otherwise.
"""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SRC_ROOT = Path(__file__).resolve().parents[1] / 'src' / 'easydiffraction'

_DESCRIPTOR_TYPES = frozenset({'Parameter', 'NumericDescriptor', 'StringDescriptor'})
_NUMERIC_TYPES = frozenset({'Parameter', 'NumericDescriptor'})

# Canonical setter value annotation per descriptor family.
_SETTER_ANN: dict[str, str] = {
    'Parameter': 'float',
    'NumericDescriptor': 'float',
    'StringDescriptor': 'str',
}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class DescriptorInfo:
    """Descriptor definition extracted from ``__init__``."""

    attr_name: str  # e.g. '_length_a'
    prop_name: str  # e.g. 'length_a'
    type_name: str  # 'Parameter' | 'NumericDescriptor' | 'StringDescriptor'
    description: str  # e.g. 'Length of the a axis of the unit cell.'
    units: str | None  # e.g. 'Å', or None / '' for unitless


@dataclass
class PropertyInfo:
    """Property getter / setter AST nodes."""

    name: str
    getter: ast.FunctionDef
    setter: ast.FunctionDef | None = None


@dataclass
class Edit:
    """A source-level edit: replace ``lines[start:end]`` with *new_text*.

    When ``start == end`` the edit is an insertion before that line.
    """

    start: int  # 0-based inclusive
    end: int  # 0-based exclusive
    new_text: str


@dataclass
class FileResult:
    """Analysis result for one source file."""

    path: Path
    issues: list[str] = field(default_factory=list)
    edits: list[Edit] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Template helpers
# ---------------------------------------------------------------------------


def _strip_dot(s: str) -> str:
    """Remove a single trailing period and surrounding whitespace."""
    s = s.rstrip()
    if s.endswith('.'):
        s = s[:-1].rstrip()
    return s


def _getter_docstring(
    desc: str,
    units: str | None,
    type_name: str,
    indent: str,
) -> str:
    """Build the expected getter docstring."""
    d = _strip_dot(desc)
    ret = f'{d} ({units}).' if units else f'{d}.'
    return (
        f'{indent}"""{d}.\n'
        f'\n'
        f'{indent}Returns:\n'
        f'{indent}    {type_name}: {ret}\n'
        f'{indent}"""\n'
    )


def _setter_docstring(
    desc: str,
    units: str | None,
    param_name: str,
    value_type: str,
    indent: str,
) -> str:
    """Build the expected setter docstring."""
    d = _strip_dot(desc)
    lower = d[0].lower() + d[1:]
    arg = f'{d} ({units}).' if units else f'{d}.'
    return (
        f'{indent}"""Set the {lower}.\n'
        f'\n'
        f'{indent}Args:\n'
        f'{indent}    {param_name} ({value_type}): {arg}\n'
        f'{indent}"""\n'
    )


def _normalize_docstring_src(text: str) -> str:
    """Normalize docstring source for comparison.

    Handles formatting transformations that must not cause false
    negatives:

    * **Summary wrapping** — ``docformatter`` may wrap long summary
      paragraphs; continuation lines are collapsed into one line.
    * **First-character capitalisation** — ``docformatter`` capitalises
      the first letter of the summary; comparison is case-insensitive.
    * **Hyphen word-breaks** — wrapping at hyphens produces
      ``"foo-\\nbar"``; the dangling space is collapsed.
    * **Section continuation lines** — ``docformatter`` may wrap long
      ``Returns:`` / ``Args:`` content lines; continuation lines are
      rejoined so that wrapped and single-line forms compare equal.
    """
    parts = text.split('\n\n', 1)
    # -- Summary paragraph --
    summary = ' '.join(parts[0].split()).lower()
    summary = summary.replace('- ', '-')
    summary = summary.replace('""" ', '"""')
    if len(parts) <= 1:
        return summary

    # -- Structured section (Returns / Args) --
    # Join continuation lines back into their parent line so that
    # wrapping differences do not cause false negatives.
    section_lines = parts[1].splitlines()
    merged: list[str] = []
    for raw in section_lines:
        stripped = raw.strip()
        # A continuation line is non-empty, doesn't start a recognised
        # keyword or the closing triple-quote, and appears right after
        # a content line (not a blank or section header).
        is_continuation = (
            stripped
            and merged
            and merged[-1].strip()
            and not stripped.startswith(('Returns:', 'Args:', '"""'))
            and not merged[-1].strip().endswith(':')
        )
        if is_continuation:
            merged[-1] = merged[-1].rstrip() + ' ' + stripped
        else:
            merged.append(raw)
    return summary + '\n\n' + '\n'.join(merged)


# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------


def _call_name(node: ast.Call) -> str | None:
    """Return the simple name of a Call's function."""
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _kwarg_str(call: ast.Call, name: str) -> str | None:
    """Extract a string-valued keyword argument from *call*."""
    for kw in call.keywords:
        if (
            kw.arg == name
            and isinstance(kw.value, ast.Constant)
            and isinstance(kw.value.value, str)
        ):
            return kw.value.value
    return None


def _ann_str(ann: ast.expr | None) -> str | None:
    """Return the annotation as a source-level string."""
    if ann is None:
        return None
    if isinstance(ann, ast.Name):
        return ann.id
    if isinstance(ann, ast.Constant) and isinstance(ann.value, str):
        return ann.value  # forward reference
    return ast.unparse(ann)


def _body_indent(func: ast.FunctionDef, lines: list[str]) -> str:
    """Compute the indentation string for the function body."""
    def_line = lines[func.lineno - 1]
    return ' ' * (len(def_line) - len(def_line.lstrip()) + 4)


def _def_line_range(func: ast.FunctionDef, lines: list[str]) -> tuple[int, int]:
    """Return 0-based ``[start, end)`` of the ``def`` statement."""
    start = func.lineno - 1
    for i in range(start, min(start + 10, len(lines))):
        if lines[i].rstrip().endswith(':'):
            return start, i + 1
        if func.body and i + 1 >= func.body[0].lineno:
            break
    return start, start + 1


def _docstring_range(func: ast.FunctionDef) -> tuple[str | None, int, int]:
    """Return ``(text, start_0, end_exclusive_0)`` of the docstring."""
    if not func.body:
        return None, -1, -1
    first = func.body[0]
    if (
        isinstance(first, ast.Expr)
        and isinstance(first.value, ast.Constant)
        and isinstance(first.value.value, str)
    ):
        # end_lineno is 1-based inclusive → 0-based exclusive is the same int
        return first.value.value, first.lineno - 1, first.end_lineno
    return None, -1, -1


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------


def _extract_descriptors(cls: ast.ClassDef) -> dict[str, DescriptorInfo]:
    """Find ``self._xxx = DescriptorType(...)`` assignments in ``__init__``."""
    result: dict[str, DescriptorInfo] = {}

    init = next(
        (n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == '__init__'),
        None,
    )
    if init is None:
        return result

    for stmt in ast.walk(init):
        # Handle both ast.Assign and ast.AnnAssign
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
            target = stmt.targets[0]
            value = stmt.value
        elif isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
            target = stmt.target
            value = stmt.value
        else:
            continue

        # Target must be self._xxx
        if not (
            isinstance(target, ast.Attribute)
            and isinstance(target.value, ast.Name)
            and target.value.id == 'self'
            and target.attr.startswith('_')
        ):
            continue

        if not isinstance(value, ast.Call):
            continue

        name = _call_name(value)
        if name not in _DESCRIPTOR_TYPES:
            continue

        desc_str = _kwarg_str(value, 'description')
        if not desc_str or not _strip_dot(desc_str):
            continue

        units = _kwarg_str(value, 'units') or None
        prop = target.attr.lstrip('_')
        result[prop] = DescriptorInfo(target.attr, prop, name, desc_str, units)

    return result


def _extract_properties(cls: ast.ClassDef) -> dict[str, PropertyInfo]:
    """Find property getters and their setters in *cls*."""
    result: dict[str, PropertyInfo] = {}

    for item in cls.body:
        if not isinstance(item, ast.FunctionDef):
            continue
        for dec in item.decorator_list:
            # @property
            if isinstance(dec, ast.Name) and dec.id == 'property':
                result[item.name] = PropertyInfo(item.name, item)
                break
            # @xxx.setter
            if (
                isinstance(dec, ast.Attribute)
                and dec.attr == 'setter'
                and isinstance(dec.value, ast.Name)
                and dec.value.id in result
            ):
                result[dec.value.id].setter = item
                break

    return result


# ---------------------------------------------------------------------------
# Analysis (shared by --check and --fix)
# ---------------------------------------------------------------------------


def _analyze_file(path: Path) -> FileResult:
    """Analyze one source file and return issues and proposed edits."""
    result = FileResult(path)
    try:
        source = path.read_text(encoding='utf-8')
    except Exception:  # noqa: BLE001
        return result

    lines = source.splitlines(keepends=True)

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return result

    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue

        descriptors = _extract_descriptors(node)
        properties = _extract_properties(node)

        for prop_name, prop in properties.items():
            if prop_name not in descriptors:
                continue
            desc = descriptors[prop_name]
            _analyze_property(node.name, prop, desc, lines, result)

    return result


def _analyze_property(
    cls_name: str,
    prop: PropertyInfo,
    desc: DescriptorInfo,
    lines: list[str],
    result: FileResult,
) -> None:
    """Check a single property against the template, accumulating issues and edits."""
    loc = f'{cls_name}.{prop.name}'
    indent = _body_indent(prop.getter, lines)

    # --- Getter return annotation ---
    actual_ret = _ann_str(prop.getter.returns)
    expected_ret = desc.type_name
    if actual_ret != expected_ret:
        result.issues.append(
            f'{loc}: getter annotation -> {actual_ret} (expected {expected_ret})'
        )
        ds, de = _def_line_range(prop.getter, lines)
        def_indent = lines[ds][: len(lines[ds]) - len(lines[ds].lstrip())]
        new_def = f'{def_indent}def {prop.name}(self) -> {expected_ret}:\n'
        result.edits.append(Edit(ds, de, new_def))

    # --- Getter docstring ---
    expected_doc = _getter_docstring(desc.description, desc.units, desc.type_name, indent)
    actual_doc_text, doc_s, doc_e = _docstring_range(prop.getter)

    if actual_doc_text is None:
        result.issues.append(f'{loc}: getter missing docstring')
        _, def_end = _def_line_range(prop.getter, lines)
        result.edits.append(Edit(def_end, def_end, expected_doc))
    else:
        actual_src = ''.join(lines[doc_s:doc_e])
        if _normalize_docstring_src(actual_src) != _normalize_docstring_src(expected_doc):
            result.issues.append(f'{loc}: getter docstring does not match template')
            result.edits.append(Edit(doc_s, doc_e, expected_doc))

    # --- Setter ---
    if prop.setter is None:
        return

    setter_args = prop.setter.args.args
    setter_param = setter_args[1].arg if len(setter_args) >= 2 else 'value'
    expected_ann = _SETTER_ANN[desc.type_name]

    # Setter def-line annotations (value type + return type)
    actual_val_ann = None
    if len(setter_args) >= 2 and setter_args[1].annotation:
        actual_val_ann = _ann_str(setter_args[1].annotation)

    actual_ret_ann = _ann_str(prop.setter.returns)

    if actual_val_ann != expected_ann or actual_ret_ann != 'None':
        parts: list[str] = []
        if actual_val_ann != expected_ann:
            parts.append(f'value: {actual_val_ann} (expected {expected_ann})')
        if actual_ret_ann != 'None':
            parts.append(f'return: {actual_ret_ann} (expected None)')
        result.issues.append(f'{loc}: setter annotation — {", ".join(parts)}')

        ds, de = _def_line_range(prop.setter, lines)
        def_indent = lines[ds][: len(lines[ds]) - len(lines[ds].lstrip())]
        new_def = f'{def_indent}def {prop.name}(self, {setter_param}: {expected_ann}) -> None:\n'
        result.edits.append(Edit(ds, de, new_def))

    # Setter docstring
    expected_setter_doc = _setter_docstring(
        desc.description, desc.units, setter_param, expected_ann, indent
    )
    actual_setter_doc, sd_s, sd_e = _docstring_range(prop.setter)

    if actual_setter_doc is None:
        result.issues.append(f'{loc}: setter missing docstring')
        _, def_end = _def_line_range(prop.setter, lines)
        result.edits.append(Edit(def_end, def_end, expected_setter_doc))
    else:
        actual_setter_src = ''.join(lines[sd_s:sd_e])
        if _normalize_docstring_src(actual_setter_src) != _normalize_docstring_src(
            expected_setter_doc
        ):
            result.issues.append(f'{loc}: setter docstring does not match template')
            result.edits.append(Edit(sd_s, sd_e, expected_setter_doc))


# ---------------------------------------------------------------------------
# Apply edits
# ---------------------------------------------------------------------------


def _apply_edits(lines: list[str], edits: list[Edit]) -> list[str]:
    """Apply edits bottom-up to preserve line numbers."""
    sorted_edits = sorted(edits, key=lambda e: e.start, reverse=True)
    result = list(lines)
    for edit in sorted_edits:
        new_lines = edit.new_text.splitlines(keepends=True)
        result[edit.start : edit.end] = new_lines
    return result


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def _collect_py_files(paths: list[str]) -> list[Path]:
    """Resolve *paths* to a sorted list of ``.py`` files.

    Each entry can be a directory (recursively globbed) or a single
    ``.py`` file.  When *paths* is empty, defaults to ``_SRC_ROOT``.
    """
    if not paths:
        return sorted(_SRC_ROOT.rglob('*.py'))

    result: list[Path] = []
    for raw in paths:
        p = Path(raw).resolve()
        if p.is_dir():
            result.extend(p.rglob('*.py'))
        elif p.is_file() and p.suffix == '.py':
            result.append(p)
    return sorted(set(result))


def main() -> int:
    """Run param-consistency check or fix."""
    parser = argparse.ArgumentParser(
        description='Parameter / property consistency: docstrings and type hints.',
    )
    parser.add_argument(
        'paths',
        nargs='*',
        help='Directories or .py files to scan (default: src/easydiffraction/)',
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--check',
        action='store_true',
        help='Validate consistency (default)',
    )
    group.add_argument(
        '--fix',
        action='store_true',
        help='Auto-fix docstrings and type hints in-place',
    )
    args = parser.parse_args()

    py_files = _collect_py_files(args.paths)
    repo_root = Path(__file__).resolve().parents[1]
    total_issues = 0
    total_fixed = 0
    files_touched = 0

    for path in py_files:
        result = _analyze_file(path)
        if not result.issues:
            continue

        try:
            rel = path.relative_to(repo_root)
        except ValueError:
            rel = path

        if args.fix:
            source_lines = path.read_text(encoding='utf-8').splitlines(keepends=True)
            fixed_lines = _apply_edits(source_lines, result.edits)
            path.write_text(''.join(fixed_lines), encoding='utf-8')
            count = len(result.issues)
            total_fixed += count
            files_touched += 1
            print(f'📝 {rel}: fixed {count} issue(s)')
        else:
            for issue in result.issues:
                print(f'  ❌ {rel}: {issue}')
            total_issues += len(result.issues)

    # Summary
    print()
    if args.fix:
        print(f'✅ Fixed {total_fixed} issue(s) in {files_touched} file(s).')
        return 0
    if total_issues:
        print(f'❌ {total_issues} consistency issue(s) found.')
        return 1
    print('✅ All properties match the template.')
    return 0


if __name__ == '__main__':
    sys.exit(main())




