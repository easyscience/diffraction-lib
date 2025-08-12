"""
Uncomment `# !pip ...` and `# ed.download_from_repository ...` lines in Jupyter
notebooks so they become `!pip ...` and `ed.download_from_repository ...` respectively.

- Operates only on code cells (does not touch outputs/metadata/markdown).
- Matches lines that start with optional whitespace, then `# !pip`
  (e.g., "  # !pip install ...").
- Also matches lines that start with optional whitespace, then
  `# ed.download_from_repository` (e.g., "  # ed.download_from_repository(...)").
- Rewrites to keep the original indentation and replace the leading
  "# !pip" with "!pip", and "# ed.download_from_repository" with "ed.download_from_repository".
- Processes one or more paths (files or directories) given as CLI args,
  recursively for directories.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import nbformat

# Regex: beginning-of-line, capture leading whitespace, then "#", spaces, then "!pip"
_PIP_PATTERN = re.compile(r'^(\s*)#\s*!pip\b')
# Regex: beginning-of-line, capture leading whitespace, then "#", spaces, then "ed.download_from_repository"
_ED_PATTERN = re.compile(r'^(\s*)#\s*ed\.download_from_repository\b')


def fix_cell_source(src: str) -> tuple[str, int]:
    """
    Replace lines starting with optional whitespace + '# !pip' with '!pip',
    and lines starting with optional whitespace + '# ed.download_from_repository'
    with 'ed.download_from_repository'.
    Returns the updated source and number of replacements performed.
    """
    changed = 0
    new_lines: list[str] = []
    for line in src.splitlines(keepends=False):
        orig_line = line
        # Replace # !pip
        if _PIP_PATTERN.match(line):
            line = _PIP_PATTERN.sub(r'\1!pip', line, count=1)
        # Replace # ed.download_from_repository
        if _ED_PATTERN.match(line):
            line = _ED_PATTERN.sub(r'\1ed.download_from_repository', line, count=1)
        if line != orig_line:
            changed += 1
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
    ap.add_argument(
        'paths',
        nargs='+',
        help='Notebook files or directories to process',
    )
    ap.add_argument(
        '--dry-run',
        action='store_true',
        help='Report changes without writing files',
    )
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
