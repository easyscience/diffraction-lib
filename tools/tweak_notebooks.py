"""Post-process generated tutorial notebooks.

Usage::
        python tools/tweak_notebooks.py tutorials/ [more_paths ...]

Inserts a bootstrap code cell as the first cell of every notebook. The
bootstrap cell:
- Checks if ``easydiffraction`` is importable; if not, installs it.
- Adds the tag ``hide-in-docs``.
- Idempotent: skipped if already present and identical.

Also sorts each notebook's jupytext ``cell_metadata_filter`` so its entry
order stays stable across runs and does not create noisy diffs.
"""

from __future__ import annotations

import sys
from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell
from nbformat.validator import normalize

from easydiffraction.utils import _is_dev_version
from easydiffraction.utils import stripped_package_version

PACKAGE_NAME = 'easydiffraction'


def _get_pip_install_specifier() -> str:
    """Get the pip install specifier for easydiffraction.

    Returns a version-pinned specifier for tagged releases (e.g.,
    'easydiffraction==0.8.0'), or an unpinned specifier for development
    versions ('easydiffraction').
    """
    if _is_dev_version(PACKAGE_NAME):
        return f'{PACKAGE_NAME}'

    version = stripped_package_version(PACKAGE_NAME)
    return f'{PACKAGE_NAME}=={version}'


def _get_bootstrap_source() -> str:
    """Generate the bootstrap source code with the appropriate version
    specifier.
    """
    pip_specifier = _get_pip_install_specifier()
    return (
        '# Check whether easydiffraction is installed; install it if needed.\n'
        '# Required for remote environments such as Google Colab.\n'
        'import importlib.util\n'
        '\n'
        "if importlib.util.find_spec('easydiffraction') is None:\n"
        f"    %pip install {pip_specifier}"
    )

BOOTSTRAP_TAG = 'hide-in-docs'


def iter_notebooks(paths: list[Path]):
    for p in paths:
        if p.is_dir():
            yield from (q for q in p.rglob('*.ipynb') if q.is_file())
        elif p.is_file() and p.suffix == '.ipynb':
            yield p


def has_bootstrap_first_cell(nb, bootstrap_source: str) -> bool:
    """Return True if the first cell exactly matches our bootstrap
    cell.
    """
    if not nb.cells:
        return False
    first = nb.cells[0]
    if first.cell_type != 'code':
        return False
    if (first.source or '') != bootstrap_source:
        return False
    tags = (first.metadata or {}).get('tags', [])
    return BOOTSTRAP_TAG in tags


def ensure_bootstrap(nb, bootstrap_source: str) -> bool:
    """Ensure the bootstrap cell exists as the very first cell.

    Returns True if a modification was made.
    """
    if has_bootstrap_first_cell(nb, bootstrap_source):
        return False

    cell = new_code_cell(
        source=bootstrap_source,
        metadata={'tags': [BOOTSTRAP_TAG]},
    )
    nb.cells.insert(0, cell)
    return True


def normalize_cell_metadata_filter(nb) -> bool:
    """Sort the jupytext ``cell_metadata_filter`` for a stable order.

    jupytext derives this filter from an unordered set, so multi-entry
    values (e.g. ``title,tags``) can swap order between runs and produce
    noisy diffs. Sort the positive entries alphabetically and keep any
    ``-``-prefixed directives (e.g. ``-all``) last.

    Returns True if the stored value changed.
    """
    jupytext_meta = nb.metadata.get('jupytext')
    if not isinstance(jupytext_meta, dict):
        return False
    current = jupytext_meta.get('cell_metadata_filter')
    if not isinstance(current, str):
        return False
    entries = [part.strip() for part in current.split(',') if part.strip()]
    positives = sorted(entry for entry in entries if not entry.startswith('-'))
    negatives = sorted(entry for entry in entries if entry.startswith('-'))
    normalized = ','.join(positives + negatives)
    if normalized == current:
        return False
    jupytext_meta['cell_metadata_filter'] = normalized
    return True


def process_notebook(path: Path, bootstrap_source: str) -> list[str]:
    nb = nbformat.read(path, as_version=4)

    # Remove all 'tags' metadata from cells
    for cell in nb.cells:
        if 'tags' in cell.metadata:
            cell.metadata.pop('tags')

    reasons: list[str] = []
    if ensure_bootstrap(nb, bootstrap_source):
        reasons.append('inserted bootstrap cell')
    if normalize_cell_metadata_filter(nb):
        reasons.append('sorted cell_metadata_filter')

    # Normalize to ensure cell ids exist and structure is valid
    if reasons or any('id' not in c for c in nb.cells):
        normalize(nb)
        nbformat.write(nb, path)
    return reasons


def main(argv: list[str]) -> int:
    if not argv:
        print('Usage: python tools/tweak_notebooks.py <paths...>', file=sys.stderr)
        return 2

    targets = list(iter_notebooks([Path(p) for p in argv]))
    if not targets:
        print('No .ipynb files found.', file=sys.stderr)
        return 1

    # Generate the bootstrap source once with the current version
    bootstrap_source = _get_bootstrap_source()
    pip_specifier = _get_pip_install_specifier()
    print(f'Using pip install specifier: {pip_specifier}')

    updated = 0
    for nb_path in targets:
        reasons = process_notebook(nb_path, bootstrap_source)
        if reasons:
            print(f'UPDATED: {nb_path} ({"; ".join(reasons)})')
            updated += 1

    if updated == 0:
        print('No changes needed.')
    else:
        print(f'Done. Files changed: {updated}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
