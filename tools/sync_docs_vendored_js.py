"""
Sync the canonical JavaScript runtimes into the docs assets.

MkDocs can only serve files under ``docs/docs``, so the canonical
snapshots — which ship in the wheel from ``src/`` — are copied into
``docs/docs/assets/javascripts/`` for the site to serve. Those docs
copies are generated (git-ignored); the single source of truth is
``src/``. This covers:

* Three.js (``vendor/threejs/``) — structure views,
* the Plotly cartesian bundle (``vendor/plotly/``) — interactive plots,
* ``ed-figures.js`` — the shared figure loader used by both the docs
  site and live notebooks.

Run automatically before ``mkdocs build``/``serve`` via the
``docs-sync-vendored-js`` pixi task; the vendored asset names come from
the same pinned table as ``tools/bump_vendored_js.py``.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from bump_vendored_js import PLOTLY
from bump_vendored_js import THREEJS

_REPO_ROOT = Path(__file__).resolve().parent.parent
_DOCS_JS_DIR = Path('docs/docs/assets/javascripts')

# The shared figure loader is project code (not a fetched third-party
# snapshot), so it lives outside the vendor tree.
_ED_FIGURES_SOURCE = Path('src/easydiffraction/display/plotters/assets/ed-figures.js')
_ED_FIGURES_DEST = _DOCS_JS_DIR / 'ed-figures.js'


def _copy(source: Path, dest: Path) -> bool:
    """
    Copy one canonical file into the docs assets.

    Parameters
    ----------
    source : Path
        Repo-relative canonical source path.
    dest : Path
        Repo-relative docs destination path.

    Returns
    -------
    bool
        ``True`` on success; ``False`` if the source is missing.
    """
    absolute_source = _REPO_ROOT / source
    if not absolute_source.is_file():
        print(f'missing canonical source: {source}')
        print('Run `pixi run vendor-update-js` first.')
        return False
    absolute_dest = _REPO_ROOT / dest
    absolute_dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(absolute_source, absolute_dest)
    print(f'  synced {dest}')
    return True


def sync() -> int:
    """
    Copy the canonical runtimes and loader into the docs assets.

    Returns
    -------
    int
        ``0`` on success; ``1`` if any canonical source file is missing.
    """
    ok = True
    for runtime in (THREEJS, PLOTLY):
        docs_dir = _DOCS_JS_DIR / 'vendor' / runtime.dest_dir.name
        for asset in runtime.assets:
            ok = _copy(runtime.dest_dir / asset.filename, docs_dir / asset.filename) and ok
    ok = _copy(_ED_FIGURES_SOURCE, _ED_FIGURES_DEST) and ok
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(sync())
