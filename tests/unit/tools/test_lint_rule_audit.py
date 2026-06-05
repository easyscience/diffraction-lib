# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for tools/lint_rule_audit.py aggregation logic (no Ruff run)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_audit():
    repo_root = Path(__file__).resolve().parents[3]
    module_path = repo_root / 'tools' / 'lint_rule_audit.py'
    spec = importlib.util.spec_from_file_location('lint_rule_audit', module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _records():
    """Synthetic Ruff JSON records covering every scope and fix kind."""
    return [
        {'code': 'D100', 'message': 'Missing module docstring', 'filename': 'src/easydiffraction/a.py', 'fix': None},
        {'code': 'D100', 'message': 'Missing module docstring', 'filename': 'src/easydiffraction/b.py', 'fix': None},
        {'code': 'I001', 'message': 'Import block un-sorted', 'filename': 'tests/unit/x.py', 'fix': {'applicability': 'safe'}},
        {'code': 'T201', 'message': '`print` found', 'filename': 'src/easydiffraction/c.py', 'fix': {'applicability': 'unsafe'}},
        {'code': 'W505', 'message': 'Doc line too long', 'filename': 'docs/docs/tutorials/ed-1.py', 'fix': None},
        {'code': 'RUF100', 'message': 'Unused noqa', 'filename': 'docs/dev/plans/p.py', 'fix': {'applicability': 'display'}},
    ]


def test_scope_classifies_each_tree():
    module = _load_audit()
    assert module.scope('src/easydiffraction/x.py') == 'src'
    assert module.scope('tests/unit/x.py') == 'tests'
    assert module.scope('docs/docs/tutorials/ed-1.py') == 'tutorials'
    # Other docs paths are NOT tutorials.
    assert module.scope('docs/dev/plans/foo.py') == 'other'
    assert module.scope('docs/mkdocs.yml') == 'other'
    assert module.scope('tools/x.py') == 'other'
    assert module.scope('') == 'other'


def test_scope_handles_absolute_paths():
    module = _load_audit()
    inside = str(module.REPO_ROOT / 'src' / 'easydiffraction' / 'x.py')
    assert module.scope(inside) == 'src'
    # Absolute path outside the repo root cannot be relativised.
    assert module.scope('/somewhere/else/x.py') == 'other'


def test_family_strips_numeric_suffix():
    module = _load_audit()
    assert module.family('PLC0415') == 'PLC'
    assert module.family('D100') == 'D'
    assert module.family('A002') == 'A'
    assert module.family('SLF001') == 'SLF'
    assert module.family('W505') == 'W'


def test_aggregate_counts_totals_scopes_and_fixability():
    module = _load_audit()
    summary = module.aggregate(_records())

    assert summary['D100']['total'] == 2
    assert summary['D100']['src'] == 2
    assert summary['D100']['family'] == 'D'
    assert summary['D100']['message'] == 'Missing module docstring'

    assert summary['I001']['tests'] == 1
    assert summary['I001']['fix_safe'] == 1
    assert summary['I001']['fix_unsafe'] == 0

    assert summary['T201']['src'] == 1
    assert summary['T201']['fix_unsafe'] == 1
    assert summary['T201']['fix_safe'] == 0

    assert summary['W505']['tutorials'] == 1

    # 'docs/dev/...' is 'other', and a 'display' fix counts as neither
    # safe nor unsafe.
    assert summary['RUF100']['other'] == 1
    assert summary['RUF100']['fix_safe'] == 0
    assert summary['RUF100']['fix_unsafe'] == 0


def test_aggregate_handles_empty_records():
    module = _load_audit()
    assert module.aggregate([]) == {}


def test_format_table_reports_header_rules_and_footer_totals():
    module = _load_audit()
    table = module.format_table(module.aggregate(_records()))
    assert 'RULE' in table
    assert 'D100' in table
    # 6 records, 5 distinct rules, 1 safe fix, 1 unsafe fix.
    assert 'Total: 6 violations across 5 rules' in table
    assert '1 safe-fixable' in table
    assert '1 need --unsafe-fixes' in table


def test_format_table_handles_empty_summary():
    module = _load_audit()
    table = module.format_table({})
    assert 'Total: 0 violations across 0 rules' in table
