# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Skip verification notebooks listed in ``ci_skip.txt`` during nbmake.

``pixi run notebook-tests`` (and the docs-build execution step) collect
every ``*.ipynb`` under this directory with nbmake. Notebook stems listed
in ``ci_skip.txt`` are marked skipped so a known-failing verification page
does not block CI while it is being fixed; the page is still committed and
shown in the documentation. The script-test runner reads the same file
(see ``tools/test_scripts.py``).
"""

from __future__ import annotations

from pathlib import Path

import pytest

_SKIP_FILE = Path(__file__).parent / 'ci_skip.txt'


def ci_skipped_stems() -> set[str]:
    """Return verification notebook stems to skip in CI."""
    if not _SKIP_FILE.is_file():
        return set()
    stems: set[str] = set()
    for line in _SKIP_FILE.read_text(encoding='utf-8').splitlines():
        entry = line.split('#', 1)[0].strip()
        if entry:
            stems.add(entry)
    return stems


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Mark CI-skipped verification notebooks as skipped."""
    skipped = ci_skipped_stems()
    if not skipped:
        return
    here = Path(__file__).parent
    for item in items:
        path = Path(str(getattr(item, 'fspath', '')))
        if path.parent == here and path.suffix == '.ipynb' and path.stem in skipped:
            reason = f"Verification page '{path.stem}' is skipped in CI (ci_skip.txt)"
            item.add_marker(pytest.mark.skip(reason=reason))
