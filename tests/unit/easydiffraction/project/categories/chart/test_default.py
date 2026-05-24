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

    swapped: list[tuple[str, dict]] = []

    class _Parent:
        def _swap_chart(self, new_type, *, strict):
            swapped.append((new_type, {'strict': strict}))
            chart._set_type(new_type, strict=strict)

    chart._parent = _Parent()
    block = gemmi.cif.read_string(
        'data_test\n_chart.type plotly\n',
    ).sole_block()

    chart.from_cif(block)

    assert swapped == [('plotly', {'strict': False})]
    assert chart.type == 'plotly'


def test_chart_invalid_type_assignment_raises():
    import pytest

    from easydiffraction.project.categories.chart.default import Chart

    chart = Chart()
    initial_type = chart.type

    with pytest.raises(ValueError, match='Unsupported chart type'):
        chart._set_type('bogus-engine')

    assert chart.type == initial_type


def test_chart_from_cif_tolerates_invalid_type(monkeypatch):
    from easydiffraction.project.categories.chart import default as chart_mod
    from easydiffraction.project.categories.chart.default import Chart

    chart = Chart()
    chart._parent = type(
        'P',
        (),
        {'_swap_chart': lambda self, t, *, strict: chart._set_type(t, strict=strict)},
    )()
    block = gemmi.cif.read_string(
        'data_test\n_chart.type bogus-engine\n',
    ).sole_block()

    warnings: list[str] = []
    monkeypatch.setattr(chart_mod.log, 'warning', warnings.append)
    chart.from_cif(block)

    assert chart.type == 'auto'
    assert any('Unsupported chart type' in w for w in warnings)
