"""
Uncomment `# !pip ...` lines in Jupyter notebooks so they become `!pip ...`.

- Operates only on code cells (does not touch outputs/metadata/markdown).
- Matches lines that start with optional whitespace, then `# !pip` (e.g., "  # !pip install ...").
- Rewrites to keep the original indentation and replace the leading "# !pip" with "!pip".
- Processes one or more paths (files or directories) given as CLI args, recursively for directories.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import nbformat

# Regex: beginning-of-line, capture leading whitespace, then "#", spaces, then "!pip"
_PATTERN = re.compile(r'^(\s*)#\s*!pip\b')


def fix_cell_source(src: str) -> tuple[str, int]:
    """
    Replace lines starting with optional whitespace + '# !pip' with '!pip'.
    Returns the updated source and number of replacements performed.
    """
    changed = 0
    new_lines: list[str] = []
    for line in src.splitlines(keepends=False):
        m = _PATTERN.match(line)
        if m:
            # Replace only the first '# !pip' at the beginning, preserve the rest of the line
            # e.g., "  # !pip install foo" -> "  !pip install foo"
            new_line = _PATTERN.sub(r'\1!pip', line, count=1)
            if new_line != line:
                changed += 1
            new_lines.append(new_line)
        else:
            new_lines.append(line)
    return ('\n'.join(new_lines), changed)


def process_notebook(path: Path) -> int:
    """
    Process a single .ipynb file. Returns number of lines changed.
    """
    nb = nbformat.read(path, as_version=4)
    total_changes = 0
    for cell in nb.cells:
        if cell.cell_type != 'code':
            continue
        new_src, changes = fix_cell_source(cell.source or '')
        if changes:
            cell.source = new_src
            total_changes += changes
    if total_changes:
        nbformat.write(nb, path)
    return total_changes


def iter_notebooks(paths: list[Path]):
    for p in paths:
        if p.is_dir():
            yield from (q for q in p.rglob('*.ipynb') if q.is_file())
        elif p.is_file() and p.suffix == '.ipynb':
            yield p


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Uncomment '# !pip ...' to '!pip ...' in code cells of .ipynb notebooks.")
    ap.add_argument('paths', nargs='+', help='Notebook files or directories to process')
    ap.add_argument('--dry-run', action='store_true', help='Report changes without writing files')
    args = ap.parse_args(argv)

    targets = list(iter_notebooks([Path(p) for p in args.paths]))
    if not targets:
        print('No .ipynb files found.', file=sys.stderr)
        return 1

    total_files = 0
    total_changes = 0
    for nb_path in targets:
        changes = process_notebook(nb_path) if not args.dry_run else 0
        if args.dry_run:
            # For dry-run, compute changes without writing
            nb = nbformat.read(nb_path, as_version=4)
            changes = 0
            for cell in nb.cells:
                if cell.cell_type != 'code':
                    continue
                _, c = fix_cell_source(cell.source or '')
                changes += c
        if changes:
            action = 'UPDATED' if not args.dry_run else 'WOULD UPDATE'
            print(f'{action}: {nb_path} ({changes} line(s))')
            total_files += 1
            total_changes += changes

    if total_files == 0:
        print('No changes needed.')
    else:
        print(f'Done. Files changed: {total_files}, lines changed: {total_changes}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
