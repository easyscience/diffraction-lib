# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Single source of truth for walking the easydiffraction source tree.

Shared by ``tools/test_structure_check.py`` (the unit-test mirror check)
and ``tools/generate_package_docs.py`` (the package-structure docs), so
the two tools cannot drift on where the source tree lives, which
directories are excluded, or which modules count as source.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src' / 'easydiffraction'
TEST_ROOT = REPO_ROOT / 'tests' / 'unit' / 'easydiffraction'

# Source directories whose contents are excluded entirely (vendored code
# and tooling caches).
EXCLUDED_DIRS: set[str] = {
    '_vendored',
    'vendor',
    '__pycache__',
    '.pytest_cache',
    '.mypy_cache',
    '.ruff_cache',
    '.ipynb_checkpoints',
}

# Source module stems that do not need a dedicated unit-test file.
EXCLUDED_MODULES: set[str] = {
    '__init__',
    '__main__',
}


def iter_source_modules() -> list[Path]:
    """Return non-excluded source modules as paths relative to ``SRC_ROOT``."""
    modules: list[Path] = []
    for py in sorted(SRC_ROOT.rglob('*.py')):
        rel = py.relative_to(SRC_ROOT)
        if any(part in EXCLUDED_DIRS for part in rel.parts):
            continue
        if py.stem in EXCLUDED_MODULES:
            continue
        modules.append(rel)
    return modules
