# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import gemmi


def test_rendering_defaults():
    from easydiffraction.display.plotting import PlotterEngineEnum
    from easydiffraction.display.tables import TableEngineEnum
    from easydiffraction.project.categories.rendering.default import Rendering

    rendering = Rendering()

    assert rendering.type_info.tag == 'default'
    assert rendering._identity.category_code == 'rendering'
    assert rendering.chart_engine.value == 'auto'
    assert rendering.table_engine.value == 'auto'
    assert rendering.plotter.engine in [member.value for member in PlotterEngineEnum]
    assert rendering.tabler.engine in [member.value for member in TableEngineEnum]


def test_rendering_plotter_binds_parent():
    from easydiffraction.project.categories.rendering.default import Rendering

    rendering = Rendering()
    parent = object()
    rendering._parent = parent

    plotter = rendering.plotter

    assert plotter._project is parent


def test_rendering_setters_update_engines():
    from easydiffraction.display.plotting import PlotterEngineEnum
    from easydiffraction.display.tables import TableEngineEnum
    from easydiffraction.project.categories.rendering.default import Rendering

    rendering = Rendering()

    rendering.chart_engine = 'plotly'
    rendering.table_engine = 'rich'

    assert rendering.chart_engine.value == 'plotly'
    assert rendering.plotter.engine == 'plotly'
    assert rendering.table_engine.value == 'rich'
    assert rendering.tabler.engine == 'rich'

    rendering.chart_engine = 'auto'
    rendering.table_engine = 'auto'

    assert rendering.chart_engine.value == 'auto'
    assert rendering.table_engine.value == 'auto'
    assert rendering.plotter.engine == PlotterEngineEnum.default().value
    assert rendering.tabler.engine == TableEngineEnum.default().value


def test_rendering_from_cif_restores_types():
    from easydiffraction.project.categories.rendering.default import Rendering

    rendering = Rendering()
    block = gemmi.cif.read_string(
        'data_test\n_rendering.chart_engine plotly\n_rendering.table_engine rich\n',
    ).sole_block()

    rendering.from_cif(block)

    assert rendering.chart_engine.value == 'plotly'
    assert rendering.table_engine.value == 'rich'
