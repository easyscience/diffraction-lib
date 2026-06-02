"""
Sync the canonical vendored Three.js into the docs assets.

MkDocs can only serve files under ``docs/docs``, so the canonical
Three.js snapshot — which ships in the wheel from ``src/`` — is copied
into ``docs/docs/assets/javascripts/vendor/threejs/`` for the site to
serve. That docs copy is generated (git-ignored); the single source of
truth is ``src/``. Plotly needs no sync: its docs-only bundle already
lives under ``docs/docs/assets``.

Run automatically before ``mkdocs build``/``serve`` via the
``docs-sync-vendored-js`` pixi task; the asset names come from the same
pinned table as ``tools/bump_vendored_js.py``.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from bump_vendored_js import THREEJS

_REPO_ROOT = Path(__file__).resolve().parent.parent
_DOCS_VENDOR_DIR = Path('docs/docs/assets/javascripts/vendor/threejs')


def sync() -> int:
    """
    Copy the canonical Three.js files into the docs assets.

    Returns
    -------
    int
        ``0`` on success; ``1`` if a canonical source file is missing.
    """
    src_dir = _REPO_ROOT / THREEJS.dest_dir
    dest_dir = _REPO_ROOT / _DOCS_VENDOR_DIR
    dest_dir.mkdir(parents=True, exist_ok=True)
    for asset in THREEJS.assets:
        source = src_dir / asset.filename
        if not source.is_file():
            print(f'missing canonical source: {THREEJS.dest_dir / asset.filename}')
            print('Run `pixi run vendor-update-js` first.')
            return 1
        shutil.copy2(source, dest_dir / asset.filename)
        print(f'  synced {_DOCS_VENDOR_DIR / asset.filename}')
    return 0


if __name__ == '__main__':
    sys.exit(sync())
