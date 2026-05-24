# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import gemmi


def test_chart_defaults():
    from easydiffraction.display.plotting import PlotterEngineEnum
    from easydiffraction.project.categories.chart.default import Chart

    chart = Chart()

    assert chart.type_info.tag == 'default'
    assert chart._identity.category_code == 'chart'
    assert chart.type == 'auto'
    assert chart.plotter.engine in [member.value for member in PlotterEngineEnum]


def test_chart_plotter_binds_parent():
    from easydiffraction.project.categories.chart.default import Chart

    chart = Chart()
    parent = object()
    chart._parent = parent

    plotter = chart.plotter

    assert plotter._project is parent


def test_chart_selector_updates_engine():
    from easydiffraction.display.plotting import PlotterEngineEnum
    from easydiffraction.project.categories.chart.default import Chart

    chart = Chart()

    chart._set_type('plotly')

    assert chart.type == 'plotly'
    assert chart.plotter.engine == 'plotly'

    chart._set_type('auto')

    assert chart.type == 'auto'
    assert chart.plotter.engine == PlotterEngineEnum.default().value


def test_chart_from_cif_restores_type():
    from easydiffraction.project.categories.chart.default import Chart

    chart = Chart()
    block = gemmi.cif.read_string(
        'data_test\n_chart.type plotly\n',
    ).sole_block()

    chart.from_cif(block)

    assert chart.type == 'plotly'
