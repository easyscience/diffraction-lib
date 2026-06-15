# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Remove saved tutorial output projects before regenerating them.

The tutorials save their projects under ``<artifact-root>/projects/``
with slug-derived names such as ``refine-lbco-hrpt-from-cif``. Removing
them before the tutorial tests guarantees the tutorial-output checks see
only freshly written projects, so a stale artifact cannot mask a
tutorial that no longer saves its project.

Only the tutorial-saved directories are removed; downloaded project
archives keep their ``proj-`` data-category names (e.g.
``proj-lbco-hrpt`` from ``download_data``) and are preserved so they
need not be re-downloaded. This proj-exclusion mirrors the
``generate_baseline.py`` collection rule, so any stale non-``proj-``
directory (including old ``ed_*`` artifacts) is cleared.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

_DEFAULT_ARTIFACT_ROOT = Path('tmp') / 'tutorials'


def main() -> None:
    """Remove every non-``proj-`` project directory under the artifact root."""
    configured = os.environ.get('EASYDIFFRACTION_ARTIFACT_ROOT')
    root = Path(configured) if configured else _DEFAULT_ARTIFACT_ROOT
    projects_dir = root / 'projects'

    removed = 0
    if projects_dir.is_dir():
        for path in sorted(projects_dir.iterdir()):
            # Keep downloaded ``proj-`` archives; remove tutorial-saved ones.
            if path.is_dir() and not path.name.startswith('proj-'):
                shutil.rmtree(path)
                removed += 1

    print(f'Removed {removed} saved tutorial project(s) under {projects_dir}')


if __name__ == '__main__':
    main()
