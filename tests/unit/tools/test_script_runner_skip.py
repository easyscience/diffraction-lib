# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for the verification-page skip scan in tools/test_scripts.py."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_runner():
    repo_root = Path(__file__).resolve().parents[3]
    module_path = repo_root / 'tools' / 'test_scripts.py'
    spec = importlib.util.spec_from_file_location('script_runner_under_test', module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_runner = _load_runner()

_REAL_CALL = (
    'verify.assert_patterns_agree(\n'
    "    [('a vs b', ref, cand)],\n"
    '    known_discrepancy=True,\n'
    "    reason='x',\n"
    ')\n'
)


def test_calls_known_discrepancy_detects_literal_keyword():
    assert _runner._calls_known_discrepancy(_REAL_CALL) is True


def test_calls_known_discrepancy_ignores_comment_mention():
    source = '# known_discrepancy=True in a comment\nverify.assert_patterns_agree([])\n'
    assert _runner._calls_known_discrepancy(source) is False


def test_calls_known_discrepancy_ignores_string_mention():
    source = "note = 'known_discrepancy=True'\nverify.assert_patterns_agree([])\n"
    assert _runner._calls_known_discrepancy(source) is False


def test_calls_known_discrepancy_ignores_false_value():
    source = 'verify.assert_patterns_agree([], known_discrepancy=False)\n'
    assert _runner._calls_known_discrepancy(source) is False


def test_calls_known_discrepancy_syntax_error_not_detected():
    # A page that fails to parse must not be silently skipped, so the
    # script runner executes it and surfaces the error.
    assert _runner._calls_known_discrepancy('def (:\n') is False


def test_tags_raises_exception_on_cell_marker():
    source = '# %% tags=["raises-exception"]\nraise RuntimeError\n'
    assert _runner._tags_raises_exception(source) is True


def test_tags_raises_exception_ignores_plain_comment():
    source = '# mentions raises-exception in prose\nx = 1\n'
    assert _runner._tags_raises_exception(source) is False


def test_verification_skip_reason_skips_known_discrepancy(tmp_path):
    page = tmp_path / 'verification' / 'pd.py'
    page.parent.mkdir()
    page.write_text(_REAL_CALL, encoding='utf-8')
    reason = _runner._verification_skip_reason(page)
    assert reason is not None
    assert 'known_discrepancy' in reason


def test_verification_skip_reason_skips_raises_exception(tmp_path):
    page = tmp_path / 'verification' / 'pd.py'
    page.parent.mkdir()
    page.write_text('# %% tags=["raises-exception"]\nraise RuntimeError\n', encoding='utf-8')
    reason = _runner._verification_skip_reason(page)
    assert reason is not None
    assert 'raises-exception' in reason


def test_verification_skip_reason_runs_regated_page(tmp_path):
    page = tmp_path / 'verification' / 'pd.py'
    page.parent.mkdir()
    page.write_text("verify.assert_patterns_agree([('a', ref, cand)])\n", encoding='utf-8')
    assert _runner._verification_skip_reason(page) is None


def test_verification_skip_reason_never_skips_tutorials(tmp_path):
    page = tmp_path / 'tutorials' / 'pd.py'
    page.parent.mkdir()
    page.write_text(_REAL_CALL, encoding='utf-8')
    assert _runner._verification_skip_reason(page) is None
