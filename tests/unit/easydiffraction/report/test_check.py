# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for IUCr report validation helpers."""

from __future__ import annotations


def test_check_report_surfaces_parse_errors(tmp_path):
    from easydiffraction.report.check import check_report

    result = check_report(tmp_path / 'missing.cif')

    assert result.ok is False
    assert len(result.errors) == 1
    assert result.errors[0].startswith('Failed to parse report CIF:')


def test_check_report_warns_for_unknown_non_extension_tags(tmp_path):
    from easydiffraction.report.check import check_report

    report_path = tmp_path / 'report.cif'
    report_path.write_text(
        'data_test\n'
        '_audit.creation_method EasyDiffraction\n'
        '_easydiffraction_custom.value 1\n'
        '_unknown.bad 2',
        encoding='utf-8',
    )
    dictionary_path = tmp_path / 'core.dic'
    dictionary_path.write_text(
        'data_core\nsave__audit.creation_method\nsave_',
        encoding='utf-8',
    )

    result = check_report(report_path, dictionary_paths=(dictionary_path,))

    assert 'Unknown IUCr tag: _unknown.bad' in result.warnings
    assert all('_easydiffraction_custom.value' not in warning for warning in result.warnings)
