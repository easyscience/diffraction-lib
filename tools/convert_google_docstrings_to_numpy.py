#!/usr/bin/env python3
"""Convert Google-style Python docstrings to numpydoc style."""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

from docstring_parser import DocstringStyle
from docstring_parser import compose
from docstring_parser import parse
from format_docstring.docstring_rewriter import calc_abs_pos
from format_docstring.docstring_rewriter import calc_line_starts
from format_docstring.docstring_rewriter import find_docstring
from format_docstring.docstring_rewriter import rebuild_literal

SECTION_NAMES = (
    'Args',
    'Arguments',
    'Returns',
    'Raises',
    'Yields',
    'Attributes',
    'Examples',
    'Notes',
)
GOOGLE_SECTION_RE = re.compile(
    r'(?m)^(?P<indent>[ \t]*)(?P<section>'
    + '|'.join(SECTION_NAMES)
    + r'):\s*(?P<rest>\S.*)?$'
)
SECTION_KINDS_WITH_ITEMS = {'Args', 'Arguments', 'Attributes'}
RST_ROLE_RE = re.compile(r':[A-Za-z_][A-Za-z0-9_]*:`')


def _iter_python_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_file() and path.suffix == '.py':
            files.append(path)
            continue

        if not path.exists():
            continue

        for file_path in sorted(path.rglob('*.py')):
            if '_vendored' in file_path.parts:
                continue
            if '.pixi' in file_path.parts:
                continue
            files.append(file_path)

    return files


def _collect_names(node: ast.AST) -> list[str]:
    names: list[str] = []

    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        args = list(node.args.posonlyargs) + list(node.args.args)
        args += list(node.args.kwonlyargs)
        names.extend(arg.arg for arg in args)
        if node.args.vararg is not None:
            names.append(node.args.vararg.arg)
        if node.args.kwarg is not None:
            names.append(node.args.kwarg.arg)
        return [name for name in names if name not in {'self', 'cls'}]

    if isinstance(node, ast.ClassDef):
        init_method = next(
            (
                stmt
                for stmt in node.body
                if isinstance(stmt, ast.FunctionDef) and stmt.name == '__init__'
            ),
            None,
        )
        if init_method is not None:
            names.extend(_collect_names(init_method))

        for stmt in node.body:
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                names.append(stmt.target.id)
            elif isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        names.append(target.id)

    return list(dict.fromkeys(names))


def _repair_inline_sections(docstring: str, names: list[str]) -> str:
    repaired = docstring.replace('\r\n', '\n')
    lines = repaired.split('\n')
    out: list[str] = []
    current_section: str | None = None
    section_indent = ''

    for raw_line in lines:
        heading = GOOGLE_SECTION_RE.match(raw_line)
        if heading:
            current_section = heading.group('section')
            section_indent = heading.group('indent')
            section_name = 'Args' if current_section == 'Arguments' else current_section
            out.append(f'{section_indent}{section_name}:')
            rest = heading.group('rest')
            if rest:
                out.append(f'{section_indent}    {rest.strip()}')
            continue

        if current_section is not None and raw_line.strip():
            stripped = raw_line.strip()
            if current_section in SECTION_KINDS_WITH_ITEMS:
                for name in sorted(names, key=len, reverse=True):
                    stripped = re.sub(
                        rf'([ \t]{{2,}})({re.escape(name)}(?:\s*\([^)]*\))?:)',
                        rf'\n{section_indent}    \2',
                        stripped,
                    )
            out.extend(
                (
                    line
                    if line.startswith(f'{section_indent}    ')
                    else f'{section_indent}    {line.strip()}'
                )
                for line in stripped.split('\n')
            )
            continue

        out.append(raw_line)
        if not raw_line.strip():
            continue

        current_section = None
        section_indent = ''

    return '\n'.join(out)


def _looks_google(docstring: str) -> bool:
    return bool(GOOGLE_SECTION_RE.search(docstring))


def _meta_kinds(parsed) -> set[str]:
    kinds: set[str] = set()
    for meta in parsed.meta:
        args = getattr(meta, 'args', None) or []
        if not args:
            continue
        kinds.add(str(args[0]).lower())
    return kinds


def _contains_unparsed_sections(parsed) -> bool:
    for text in (parsed.short_description, parsed.long_description):
        if text and GOOGLE_SECTION_RE.search(text):
            return True
    return False


def _is_safe_conversion(docstring: str, parsed) -> bool:
    if RST_ROLE_RE.search(docstring) or '::' in docstring:
        return False

    kinds = _meta_kinds(parsed)
    if _contains_unparsed_sections(parsed):
        return False

    expectations = {
        'Args': 'param',
        'Arguments': 'param',
        'Attributes': 'attribute',
        'Returns': 'returns',
        'Raises': 'raises',
        'Yields': 'yields',
        'Examples': 'examples',
    }
    for section, expected_kind in expectations.items():
        if section in docstring and expected_kind not in kinds:
            return False

    return True


def _convert_docstring(docstring: str, names: list[str]) -> str | None:
    if not _looks_google(docstring):
        return None

    repaired = _repair_inline_sections(docstring, names)

    try:
        parsed = parse(repaired, style=DocstringStyle.GOOGLE)
    except Exception:
        return None

    if not _is_safe_conversion(repaired, parsed):
        return None

    converted = compose(parsed, style=DocstringStyle.NUMPYDOC)
    return converted if converted != docstring else None


def _format_multiline_docstring(content: str, indent: int) -> str:
    indent_str = ' ' * indent
    lines = content.strip('\n').splitlines()
    body = '\n'.join(f'{indent_str}{line}' if line else '' for line in lines)
    return f'\n{body}\n{indent_str}'


def _convert_file(path: Path) -> bool:
    source_code = path.read_text()
    tree = ast.parse(source_code, type_comments=True)
    line_starts = calc_line_starts(source_code)
    replacements: list[tuple[int, int, str]] = []

    nodes: list[ast.AST] = [tree]
    nodes.extend(ast.walk(tree))

    for node in nodes:
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        docstring_obj = find_docstring(node)
        if docstring_obj is None:
            continue

        value = docstring_obj.value
        end_lineno = getattr(value, 'end_lineno', None)
        end_col_offset = getattr(value, 'end_col_offset', None)
        if end_lineno is None or end_col_offset is None:
            continue

        docstring = ast.get_docstring(node, clean=False)
        if docstring is None:
            continue

        converted = _convert_docstring(docstring, _collect_names(node))
        if converted is None:
            continue

        start = calc_abs_pos(source_code, line_starts, value.lineno, value.col_offset)
        end = calc_abs_pos(source_code, line_starts, end_lineno, end_col_offset)
        original_literal = source_code[start:end]
        leading_indent = getattr(value, 'col_offset', 0)
        formatted = _format_multiline_docstring(converted, leading_indent)
        new_literal = rebuild_literal(original_literal, formatted)
        if new_literal is None or new_literal == original_literal:
            continue

        replacements.append((start, end, new_literal))

    if not replacements:
        return False

    replacements.sort(reverse=True)
    new_source = source_code
    for start, end, replacement in replacements:
        new_source = new_source[:start] + replacement + new_source[end:]

    compile(new_source, str(path), 'exec')
    path.write_text(new_source)
    return True


def main(argv: list[str]) -> int:
    input_paths = [Path(arg) for arg in argv] if argv else [Path('src'), Path('tools')]
    changed = 0

    for path in _iter_python_files(input_paths):
        if _convert_file(path):
            changed += 1
            print(f'Converted {path}')

    print(f'Converted docstrings in {changed} file(s).')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
