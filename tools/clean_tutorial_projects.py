# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Remove saved tutorial output projects before regenerating them.

The tutorials save their projects under ``<artifact-root>/projects/``
with names matching ``ed_<n>_<name>``. Removing them before the
tutorial tests guarantees the tutorial-output checks see only freshly
written projects, so a stale artifact cannot mask a tutorial that no
longer saves its project.

Only the ``ed_*`` output directories are removed; downloaded input
projects (e.g. ``ed-36`` from ``download_data``) keep their hyphenated
names and are preserved so they need not be re-downloaded.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

_DEFAULT_ARTIFACT_ROOT = Path('tmp') / 'tutorials'


def main() -> None:
    """Remove every ``projects/ed_*`` directory under the artifact root."""
    configured = os.environ.get('EASYDIFFRACTION_ARTIFACT_ROOT')
    root = Path(configured) if configured else _DEFAULT_ARTIFACT_ROOT
    projects_dir = root / 'projects'

    removed = 0
    if projects_dir.is_dir():
        for path in sorted(projects_dir.glob('ed_*')):
            if path.is_dir():
                shutil.rmtree(path)
                removed += 1

    print(f'Removed {removed} saved tutorial project(s) under {projects_dir}')


if __name__ == '__main__':
    main()
