# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import gemmi


def test_rendering_plot_defaults():
    from easydiffraction.display.plotting import PlotterEngineEnum
    from easydiffraction.project.categories.rendering_plot.default import RenderingPlot

    rendering_plot = RenderingPlot()

    assert rendering_plot.type_info.tag == 'default'
    assert rendering_plot._identity.category_code == 'rendering_plot'
    assert rendering_plot.type == 'auto'
    assert rendering_plot.plotter.engine in [member.value for member in PlotterEngineEnum]


def test_rendering_plot_plotter_binds_parent():
    from easydiffraction.project.categories.rendering_plot.default import RenderingPlot

    rendering_plot = RenderingPlot()
    parent = object()
    rendering_plot._parent = parent

    plotter = rendering_plot.plotter

    assert plotter._project is parent


def test_rendering_plot_selector_updates_engine():
    from easydiffraction.display.plotting import PlotterEngineEnum
    from easydiffraction.project.categories.rendering_plot.default import RenderingPlot

    rendering_plot = RenderingPlot()

    rendering_plot._set_type('plotly')

    assert rendering_plot.type == 'plotly'
    assert rendering_plot.plotter.engine == 'plotly'

    rendering_plot._set_type('auto')

    assert rendering_plot.type == 'auto'
    assert rendering_plot.plotter.engine == PlotterEngineEnum.default().value


def test_rendering_plot_from_cif_restores_type():
    from easydiffraction.project.categories.rendering_plot.default import RenderingPlot

    rendering_plot = RenderingPlot()

    swapped: list[tuple[str, dict]] = []

    class _Parent:
        def _swap_rendering_plot(self, new_type, *, strict):
            swapped.append((new_type, {'strict': strict}))
            rendering_plot._set_type(new_type, strict=strict)

    rendering_plot._parent = _Parent()
    block = gemmi.cif.read_string(
        'data_test\n_rendering_plot.type plotly\n',
    ).sole_block()

    rendering_plot.from_cif(block)

    assert swapped == [('plotly', {'strict': False})]
    assert rendering_plot.type == 'plotly'


def test_rendering_plot_invalid_type_assignment_raises():
    import pytest

    from easydiffraction.project.categories.rendering_plot.default import RenderingPlot

    rendering_plot = RenderingPlot()
    initial_type = rendering_plot.type

    with pytest.raises(ValueError, match='Unsupported rendering_plot type'):
        rendering_plot._set_type('bogus-engine')

    assert rendering_plot.type == initial_type


def test_rendering_plot_from_cif_tolerates_invalid_type(monkeypatch):
    from easydiffraction.project.categories.rendering_plot import default as rendering_plot_mod
    from easydiffraction.project.categories.rendering_plot.default import RenderingPlot

    rendering_plot = RenderingPlot()
    rendering_plot._parent = type(
        'P',
        (),
        {'_swap_rendering_plot': lambda self, t, *, strict: rendering_plot._set_type(t, strict=strict)},
    )()
    block = gemmi.cif.read_string(
        'data_test\n_rendering_plot.type bogus-engine\n',
    ).sole_block()

    warnings: list[str] = []
    monkeypatch.setattr(rendering_plot_mod.log, 'warning', warnings.append)
    rendering_plot.from_cif(block)

    assert rendering_plot.type == 'auto'
    assert any('Unsupported rendering_plot type' in w for w in warnings)
