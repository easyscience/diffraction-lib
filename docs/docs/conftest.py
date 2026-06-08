# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""xfail verification notebooks listed in ``verification/ci_skip.txt``.

``pixi run notebook-tests`` (and the docs-build execution step) collect
every ``*.ipynb`` under ``docs/docs/`` with nbmake. Verification notebook
stems listed in ``verification/ci_skip.txt`` are marked ``xfail`` (not
``skip``): nbmake still **executes** them — so they render in the
documentation and ``--overwrite`` writes their outputs — but a known
discrepancy or pending-feature page is an expected failure rather than a
suite failure. ``strict=False`` keeps a page that happens to pass (for
example one whose agreement check runs with ``raise_on_failure=False``)
from turning into a failure. The script-test runner reads the same file
but skips those stems outright (see ``tools/test_scripts.py``), since the
refinement fits are slow and that runner is the fast regression check.

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
    """Return verification notebook stems allowed to fail in CI."""
    if not _SKIP_FILE.is_file():
        return set()
    stems: set[str] = set()
    for line in _SKIP_FILE.read_text(encoding='utf-8').splitlines():
        entry = line.split('#', 1)[0].strip()
        if entry:
            stems.add(entry)
    return stems


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """xfail listed verification notebooks so they run but cannot fail."""
    allowed = ci_skipped_stems()
    if not allowed:
        return
    for item in items:
        path = Path(str(getattr(item, 'fspath', '')))
        if path.parent.name == 'verification' and path.suffix == '.ipynb' and path.stem in allowed:
            reason = f"Verification page '{path.stem}' is allowed to fail in CI (ci_skip.txt)"
            item.add_marker(pytest.mark.xfail(reason=reason, strict=False))
