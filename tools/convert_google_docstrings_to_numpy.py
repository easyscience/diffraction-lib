#!/usr/bin/env python3
"""Convert Google-style Python docstrings to numpydoc style."""

from __future__ import annotations

import ast
import inspect
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
PRESERVE_BLOCK_SECTIONS = {'Examples', 'Notes'}
GENERIC_ITEM_SECTIONS = {'Raises', 'Returns', 'Yields'}
GENERIC_ITEM_RE = re.compile(
    r'(?<!\S)(?P<label>[A-Za-z_][A-Za-z0-9_\.\[\], \|\(\)]{0,80}?)\s*:'
)


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


def _strip_blank_edges(lines: list[str]) -> list[str]:
    start = 0
    end = len(lines)
    while start < end and not lines[start].strip():
        start += 1
    while end > start and not lines[end - 1].strip():
        end -= 1
    return lines[start:end]


def _collapse_whitespace(lines: list[str]) -> str:
    return ' '.join(line.strip() for line in lines if line.strip())


def _repair_named_items(block_lines: list[str], names: list[str]) -> list[str] | None:
    flat = _collapse_whitespace(block_lines)
    if not flat or not names:
        return None

    label_pattern = '|'.join(re.escape(name) for name in sorted(set(names), key=len, reverse=True))
    item_re = re.compile(
        rf'(?<!\S)(?P<label>\*{{0,2}}(?:{label_pattern})(?:\s*\([^)]*\))?)\s*:'
    )
    matches = list(item_re.finditer(flat))
    if not matches or matches[0].start() != 0:
        return None

    repaired: list[str] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(flat)
        description = flat[start:end].strip()
        repaired.append(f'    {match.group("label")}: {description}' if description else f'    {match.group("label")}:')
    return repaired


def _repair_generic_items(block_lines: list[str]) -> list[str] | None:
    flat = _collapse_whitespace(block_lines)
    if not flat:
        return None

    matches = list(GENERIC_ITEM_RE.finditer(flat))
    if not matches or matches[0].start() != 0:
        return None

    repaired: list[str] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(flat)
        description = flat[start:end].strip()
        repaired.append(f'    {match.group("label")}: {description}' if description else f'    {match.group("label")}:')
    return repaired


def _repair_section(section: str, block_lines: list[str], names: list[str]) -> list[str]:
    stripped = _strip_blank_edges(block_lines)
    if not stripped:
        return []

    if section in SECTION_KINDS_WITH_ITEMS:
        repaired = _repair_named_items(stripped, names)
        if repaired is not None:
            return repaired

    if section in GENERIC_ITEM_SECTIONS:
        repaired = _repair_generic_items(stripped)
        if repaired is not None:
            return repaired

    if section in PRESERVE_BLOCK_SECTIONS:
        return [f'    {line}' if line else '' for line in stripped]

    flat = _collapse_whitespace(stripped)
    return [f'    {flat}'] if flat else []


def _repair_inline_sections(docstring: str, names: list[str]) -> str:
    cleaned = inspect.cleandoc(docstring.replace('\r\n', '\n'))
    lines = cleaned.split('\n')
    out: list[str] = []
    index = 0

    while index < len(lines):
        raw_line = lines[index]
        heading = GOOGLE_SECTION_RE.match(raw_line)
        if heading is None:
            out.append(raw_line.rstrip())
            index += 1
            continue

        section = heading.group('section')
        section_name = 'Args' if section == 'Arguments' else section
        out.append(f'{section_name}:')

        block_lines: list[str] = []
        rest = heading.group('rest')
        if rest:
            block_lines.append(rest)

        index += 1
        while index < len(lines):
            next_line = lines[index]
            if GOOGLE_SECTION_RE.match(next_line):
                break
            if (
                section_name not in PRESERVE_BLOCK_SECTIONS
                and not next_line.strip()
                and index + 1 < len(lines)
                and lines[index + 1].strip()
                and GOOGLE_SECTION_RE.match(lines[index + 1]) is None
            ):
                break
            block_lines.append(next_line.rstrip())
            index += 1

        out.extend(_repair_section(section_name, block_lines, names))

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


def _has_section_heading(docstring: str, section: str) -> bool:
    return re.search(rf'(?m)^[ \t]*{re.escape(section)}:\s*(?:\S.*)?$', docstring) is not None


def _is_safe_conversion(docstring: str, parsed) -> bool:
    if '::' in docstring:
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
        if _has_section_heading(docstring, section) and expected_kind not in kinds:
            return False

    return True


def _tidy_numpydoc_output(docstring: str) -> str:
    tidied = docstring.strip('\n')
    tidied = re.sub(r'\n{3,}', '\n\n', tidied)
    tidied = re.sub(r'(?m)^([^\n]+)\n(-+)\n\n( +\S)', r'\1\n\2\n\3', tidied)
    return tidied


def _convert_docstring(docstring: str, names: list[str]) -> str | None:
    cleaned = inspect.cleandoc(docstring)
    if not _looks_google(cleaned):
        return None

    repaired = _repair_inline_sections(cleaned, names)

    try:
        parsed = parse(repaired, style=DocstringStyle.GOOGLE)
    except Exception:
        return None

    if not _is_safe_conversion(repaired, parsed):
        return None

    converted = _tidy_numpydoc_output(compose(parsed, style=DocstringStyle.NUMPYDOC))
    return converted if converted != cleaned else None


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
