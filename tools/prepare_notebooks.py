#!/usr/bin/env python3
"""
Uncomment `# !pip ...` and `# ed.download_from_repository ...` lines in Jupyter
notebooks so they become `!pip ...` and `ed.download_from_repository ...` respectively.

Additionally, adjust cell metadata and tags according to DMSC Summer School rules:
- If a cell has the `dmsc-school-hint` or `solution` tag, add
  `{"jupyter": {"source_hidden": true}}` so it is collapsed by default.
- If a cell has the `remove-cell` tag, replace it with `hide_in_docs`.
- If a cell has the `non-editable` tag, set `editable: false` in metadata.
- Remove all tags except `hide_in_docs`.

Notes:
- Operates only on code cells for uncommenting (does not touch markdown sources),
  but processes metadata/tags for ALL cells.
- Matches lines that start with optional whitespace, then `# !pip`
  (e.g., "  # !pip install ...").
- Also matches lines that start with optional whitespace, then
  `# ed.download_from_repository` (e.g., "  # ed.download_from_repository(...)").
- Rewrites to keep the original indentation and replace the leading
  "# !pip" with "!pip", and "# ed.download_from_repository" with "ed.download_from_repository".
- Processes one or more paths (files or directories) given as CLI args,
  recursively for directories.

New CLI options:
- `--remove-cell true|false` to control how cells tagged `remove-cell` are handled:
  remove entirely (true) or map tag to `hide_in_docs` (false, default).
- `--strip-solution true|false` to control handling of cells tagged `solution`:
  replace content with placeholder (true) or collapse via source_hidden (false, default).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import nbformat
from nbformat.validator import normalize

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


def fix_cell_metadata(cell, *, remove_cell: bool, strip_solution: bool) -> tuple[int, bool]:
    """
    Apply tag/metadata rules:
      - 'dmsc-school-hint' or 'solution' -> jupyter.source_hidden = True (unless strip_solution is True)
      - 'remove-cell' -> either remove cell (if remove_cell=True) or rename to 'hide_in_docs'
      - 'non-editable' -> editable = False
      - keep only 'hide_in_docs' tag, drop all others (unless cell removed)
      - if strip_solution=True and 'solution' tag present, replace source with placeholder instead of collapsing
    Returns (number of changes applied, remove_this_cell flag).
    """
    changed = 0
    remove_flag = False
    md = cell.metadata

    # Normalize tags list
    tags = list(md.get('tags', []))

    # Check for remove-cell tag and remove_cell flag
    if 'remove-cell' in tags:
        if remove_cell:
            # Mark cell for removal
            remove_flag = True
            # Count change if tags existed (since removal is a change)
            if tags:
                changed += 1
            # Skip further processing for this cell
            return changed, remove_flag
        else:
            # rename remove-cell -> hide_in_docs (without duplicating)
            new_tags = []
            seen_hide = 'hide_in_docs' in tags
            for t in tags:
                if t == 'remove-cell':
                    if not seen_hide:
                        new_tags.append('hide_in_docs')
                        seen_hide = True
                else:
                    new_tags.append(t)
            if new_tags != tags:
                tags = new_tags
                changed += 1

    # Handle 'solution' tag with strip_solution flag
    if strip_solution and ('solution' in tags):
        if getattr(cell, 'source', None) != '# Insert your solution:':
            cell.source = '# Insert your solution:'
            changed += 1
        # Do not add jupyter.source_hidden in this case
    else:
        # Add jupyter.source_hidden when hint or solution tag present
        if ('dmsc-school-hint' in tags) or ('solution' in tags):
            jup = md.get('jupyter', {})
            if jup.get('source_hidden') is not True:
                jup['source_hidden'] = True
                md['jupyter'] = jup
                changed += 1

    # 3) add editable: false for non-editable tag
    if 'non-editable' in tags:
        if md.get('editable') is not False:
            md['editable'] = False
            changed += 1

    # 4) keep only 'hide_in_docs' and drop empty tag arrays from metadata, unless removing cell
    if not remove_flag:
        keep = ['hide_in_docs'] if 'hide_in_docs' in tags else []

        if keep:  # we want to keep only 'hide_in_docs'
            if md.get('tags') != keep:
                md['tags'] = keep
                changed += 1
        else:
            # remove empty tags key if present
            if 'tags' in md:
                # count as change if previously non-empty
                if md['tags']:
                    changed += 1
                md.pop('tags', None)

    return changed, remove_flag


def process_notebook(path: Path, *, remove_cell: bool, strip_solution: bool) -> int:
    """
    Process a single .ipynb file.
    - Uncomment magic/commented lines in code cells.
    - Adjust cell metadata/tags as per school rules.
    Returns number of changes made.
    """
    nb = nbformat.read(path, as_version=4)
    total_changes = 0
    new_cells = []
    for cell in nb.cells:
        # Source-only changes for code cells
        if cell.cell_type == 'code':
            new_src, changes = fix_cell_source(cell.source or '')
            if changes:
                cell.source = new_src
                total_changes += changes
        # Metadata/tag changes for all cells
        md_changes, remove_it = fix_cell_metadata(cell, remove_cell=remove_cell, strip_solution=strip_solution)
        total_changes += md_changes
        if not remove_it:
            new_cells.append(cell)
    nb.cells = new_cells

    # Normalize/add missing IDs if needed, even when no source/metadata changes were made
    need_normalize = any('id' not in cell for cell in nb.cells)
    if total_changes or need_normalize:
        normalize(nb)
        nbformat.write(nb, path)
    return total_changes + (1 if need_normalize and not total_changes else 0)


def iter_notebooks(paths: list[Path]):
    for p in paths:
        if p.is_dir():
            yield from (q for q in p.rglob('*.ipynb') if q.is_file())
        elif p.is_file() and p.suffix == '.ipynb':
            yield p


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Uncomment '# !pip ...' and '# ed.download_from_repository ...' in code cells, "
            "and adjust cell metadata/tags (collapse hints/solutions, map 'remove-cell' "
            "to 'hide_in_docs' or remove cells, keep only 'hide_in_docs', and mark 'non-editable' cells as not editable)."
        )
    )
    ap.add_argument('paths', nargs='+', help='Notebook files or directories to process')
    ap.add_argument('--dry-run', action='store_true', help='Report changes without writing files')
    ap.add_argument(
        '--remove-cell',
        dest='remove_cell',
        type=lambda s: str(s).lower() == 'true',
        default=False,
        help='true: remove cells tagged "remove-cell"; false (default): map tag to hide_in_docs',
    )
    ap.add_argument(
        '--strip-solution',
        dest='strip_solution',
        type=lambda s: str(s).lower() == 'true',
        default=False,
        help='true: replace content of cells tagged "solution" with placeholder; false (default): collapse via source_hidden',
    )
    args = ap.parse_args(argv)

    targets = list(iter_notebooks([Path(p) for p in args.paths]))
    if not targets:
        print('No .ipynb files found.', file=sys.stderr)
        return 1

    total_files = 0
    total_changes = 0
    for nb_path in targets:
        changes = 0
        if args.dry_run:
            nb = nbformat.read(nb_path, as_version=4)
            for cell in nb.cells:
                if cell.cell_type == 'code':
                    _, c = fix_cell_source(cell.source or '')
                    changes += c
                md_c, remove_it = fix_cell_metadata(cell, remove_cell=args.remove_cell, strip_solution=args.strip_solution)
                changes += md_c
                if remove_it:
                    changes += 1  # count removal as a change
        else:
            changes = process_notebook(nb_path, remove_cell=args.remove_cell, strip_solution=args.strip_solution)

        if changes:
            action = 'WOULD UPDATE' if args.dry_run else 'UPDATED'
            print(f'{action}: {nb_path} ({changes} change(s))')
            total_files += 1
            total_changes += changes

    if total_files == 0:
        print('No changes needed.')
    else:
        print(f'Done. Files changed: {total_files}, total changes: {total_changes}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
