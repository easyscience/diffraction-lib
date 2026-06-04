# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import pytest


def test_report_factory_default_and_create():
    from easydiffraction.project.categories.report.default import Report
    from easydiffraction.project.categories.report.factory import ReportFactory

    assert ReportFactory.default_tag() == 'default'
    assert 'default' in ReportFactory.supported_tags()

    report = ReportFactory.create('default')

    assert isinstance(report, Report)


def test_report_factory_rejects_unknown_tag():
    from easydiffraction.project.categories.report.factory import ReportFactory

    with pytest.raises(ValueError, match=r"Unsupported type: 'missing'"):
        ReportFactory.create('missing')
