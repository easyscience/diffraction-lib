# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Skip verification notebooks listed in ``verification/ci_skip.txt``.

``pixi run notebook-tests`` (and the docs-build execution step) collect
every ``*.ipynb`` under ``docs/docs/`` with nbmake. Verification notebook
stems listed in ``verification/ci_skip.txt`` are marked skipped so a
known-failing page does not block CI while it is being fixed; the page is
still committed and shown in the documentation. The script-test runner
reads the same file (see ``tools/test_scripts.py``).

This lives at ``docs/docs/`` rather than beside the notebooks so it is not
swept into the notebook-generation globs, which target the ``tutorials``
and ``verification`` directories directly.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_VERIFICATION_DIR = Path(__file__).parent / 'verification'
_SKIP_FILE = _VERIFICATION_DIR / 'ci_skip.txt'


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
    for item in items:
        path = Path(str(getattr(item, 'fspath', '')))
        if path.parent.name == 'verification' and path.suffix == '.ipynb' and path.stem in skipped:
            reason = f"Verification page '{path.stem}' is skipped in CI (ci_skip.txt)"
            item.add_marker(pytest.mark.skip(reason=reason))
