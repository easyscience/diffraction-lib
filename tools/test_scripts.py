# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Test runner for tutorial scripts in the 'tutorials' directory.

This test discovers and executes all Python scripts located under the
'tutorials' directory to ensure they run without errors.

Important: each script must be executed in a fresh Python process.
Running many tutorials in-process (e.g. via runpy) leaks global state
between scripts (notably cached calculator dictionaries keyed only by
model/experiment names), which can cause false failures.
"""

from __future__ import annotations

import ast
import os
import re
import subprocess  # noqa: S404
import sys
from pathlib import Path

import pytest

_repo_root = Path(__file__).resolve().parents[1]
_src_root = _repo_root / 'src'
_VERIFICATION_DIR_NAME = 'verification'

# The fast script runner skips a verification page that statically
# declares a known discrepancy (its agreement assertion is two-sided and
# the refinement fit is slow) or tags a cell as raising before the
# assertion is reached. nbmake still executes both kinds, so no coverage
# is lost here. The in-source flag/tag is the single source of truth;
# there is no external skip list. Detection is narrow on purpose: the
# flag is read from the actual ``assert_patterns_agree`` call via the AST
# (not a loose substring a comment could trip), and the tag only from a
# jupytext ``# %%`` cell marker.
_RAISES_EXCEPTION_TAG_RE = re.compile(r'tags\s*=\s*\[[^\]]*["\']raises-exception["\']')


def _calls_known_discrepancy(source: str) -> bool:
    """True if a real ``assert_patterns_agree(..., known_discrepancy=True)``.

    Parses the source and inspects each ``assert_patterns_agree`` call for
    a literal ``known_discrepancy=True`` keyword, so a comment, string, or
    markdown cell that merely mentions the flag does not trip the skip. A
    page that fails to parse is treated as not-skipped, so script-tests
    runs it and surfaces the error rather than silently skipping.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, 'id', None)
        if name != 'assert_patterns_agree':
            continue
        for keyword in node.keywords:
            if (
                keyword.arg == 'known_discrepancy'
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value is True
            ):
                return True
    return False


def _tags_raises_exception(source: str) -> bool:
    """True if a jupytext ``# %%`` cell marker tags a cell raises-exception."""
    for line in source.splitlines():
        stripped = line.lstrip()
        if stripped.startswith('# %%') and _RAISES_EXCEPTION_TAG_RE.search(stripped):
            return True
    return False


def _verification_skip_reason(script_path: Path) -> str | None:
    """Return why a verification page is skipped by script-tests, or None.

    Skips a page under ``docs/docs/verification`` that statically
    declares ``known_discrepancy=True`` in its agreement call or tags a
    cell ``raises-exception``; nbmake covers both instead. Tutorial
    scripts are never skipped.
    """
    if script_path.parent.name != _VERIFICATION_DIR_NAME:
        return None
    source = script_path.read_text(encoding='utf-8')
    if _calls_known_discrepancy(source):
        return f'{script_path.stem}: known_discrepancy=True (covered by nbmake)'
    if _tags_raises_exception(source):
        return f'{script_path.stem}: raises-exception cell tag (covered by nbmake)'
    return None

# Discover tutorial and verification scripts, excluding checkpoint files
# and pytest conftest modules.
_SCRIPT_DIRS = ('docs/docs/tutorials', 'docs/docs/verification')
TUTORIALS = [
    p
    for directory in _SCRIPT_DIRS
    for p in Path(directory).rglob('*.py')
    if '.ipynb_checkpoints' not in p.parts and p.name != 'conftest.py'
]


@pytest.mark.parametrize('script_path', TUTORIALS)
def test_script_runs(script_path: Path):
    """Execute a tutorial script and fail if it raises an exception.

    Each script is run in the context of __main__ to mimic standalone
    execution.
    """
    skip_reason = _verification_skip_reason(script_path)
    if skip_reason is not None:
        pytest.skip(skip_reason)

    env = os.environ.copy()
    if _src_root.exists():
        existing = env.get('PYTHONPATH', '')
        env['PYTHONPATH'] = (
            str(_src_root) if not existing else str(_src_root) + os.pathsep + existing
        )

    # This is a test harness executing repo-local tutorial scripts.
    # We intentionally use subprocess isolation to prevent cross-test
    # global state leaks (e.g. calculator caches) that can cause false
    # failures when running tutorials in a shared interpreter.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(script_path)],
        cwd=str(_repo_root),
        env=env,
        capture_output=True,
        text=True,
        encoding='utf-8',
    )
    if result.returncode != 0:
        details = (result.stdout or '') + (result.stderr or '')
        pytest.fail(f'{script_path}\n{details.strip()}')
