# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations


def test_report_format_enum_values():
    from easydiffraction.report.enums import ReportFormatEnum

    assert [member.value for member in ReportFormatEnum] == [
        'cif',
        'html',
        'tex',
        'pdf',
    ]
