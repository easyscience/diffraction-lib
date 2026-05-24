# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import pytest


def test_chart_factory_default_and_create():
    from easydiffraction.project.categories.chart.default import Chart
    from easydiffraction.project.categories.chart.factory import ChartFactory

    assert ChartFactory.default_tag() == 'default'
    assert 'default' in ChartFactory.supported_tags()

    chart = ChartFactory.create('default')

    assert isinstance(chart, Chart)


def test_chart_factory_rejects_unknown_tag():
    from easydiffraction.project.categories.chart.factory import ChartFactory

    with pytest.raises(ValueError, match=r"Unsupported type: 'missing'"):
        ChartFactory.create('missing')
