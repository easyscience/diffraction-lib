# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import os

import numpy as np


def test_module_import():
    import easydiffraction.display.plotters.ascii as MUT

    expected_module_name = 'easydiffraction.display.plotters.ascii'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_ascii_plotter_plot_minimal(capsys):
    from easydiffraction.display.plotters.ascii import AsciiPlotter

    x = np.array([0.0, 1.0, 2.0])
    y = np.array([1.0, 2.0, 3.0])
    p = AsciiPlotter()
    p.plot_powder(x=x, y_series=[y], labels=['meas'], axes_labels=['x', 'y'], title='T', height=5)
    out = capsys.readouterr().out
    assert 'Displaying data for selected x-range' in out


def test_ascii_plotter_plot_supports_max_posterior_legend(capsys):
    from easydiffraction.display.plotters.ascii import AsciiPlotter

    x = np.array([0.0, 1.0, 2.0])
    y_meas = np.array([1.0, 2.0, 3.0])
    y_map = np.array([0.5, 1.5, 2.5])
    plotter = AsciiPlotter()

    plotter.plot_powder(
        x=x,
        y_series=[y_meas, y_map],
        labels=['meas', 'posterior'],
        axes_labels=['x', 'y'],
        title='Posterior predictive',
        height=5,
    )

    out = capsys.readouterr().out
    assert 'Measured (Imeas)' in out
    assert 'Best posterior sample' in out


def test_ascii_plotter_plot_single_crystal_uses_detected_terminal_width(monkeypatch, capsys):
    from easydiffraction.display.plotters import ascii as ascii_mod
    from easydiffraction.display.plotters.ascii import AsciiPlotter

    monkeypatch.setattr(
        ascii_mod.shutil,
        'get_terminal_size',
        lambda fallback: os.terminal_size((44, 24)),
    )

    p = AsciiPlotter()
    p.plot_single_crystal(
        x_calc=np.array([1.0, 2.0, 3.0]),
        y_meas=np.array([1.1, 1.9, 3.2]),
        y_meas_su=np.array([0.1, 0.1, 0.1]),
        axes_labels=['F²calc', 'F²meas'],
        title='SC width test',
        height=6,
    )

    out = capsys.readouterr().out
    assert f'└{"─" * 26}' in out


def test_ascii_plotter_plot_single_crystal(capsys):
    from easydiffraction.display.plotters.ascii import AsciiPlotter

    x_calc = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y_meas = np.array([1.1, 1.9, 3.2, 3.8, 5.1])
    y_meas_su = np.array([0.1, 0.1, 0.1, 0.1, 0.1])

    p = AsciiPlotter()
    p.plot_single_crystal(
        x_calc=x_calc,
        y_meas=y_meas,
        y_meas_su=y_meas_su,
        axes_labels=['F²calc', 'F²meas'],
        title='SC Test',
        height=10,
    )
    out = capsys.readouterr().out
    # Verify title and axes labels appear
    assert 'SC Test' in out
    assert 'F²calc' in out
    assert 'F²meas' in out
    # Verify scatter points are plotted (● character)
    assert '●' in out
    # Verify diagonal reference line (· character)
    assert '·' in out


def test_ascii_plotter_plot_powder_meas_vs_calc_announces_plotly_only_bragg_row(capsys):
    from easydiffraction.display.plotters.ascii import AsciiPlotter
    from easydiffraction.display.plotters.base import BraggTickSet
    from easydiffraction.display.plotters.base import PowderMeasVsCalcSpec

    plotter = AsciiPlotter()
    plotter.plot_powder_meas_vs_calc(
        plot_spec=PowderMeasVsCalcSpec(
            x=np.array([0.0, 1.0, 2.0]),
            y_meas=np.array([3.0, 4.0, 5.0]),
            y_calc=np.array([2.5, 4.5, 4.0]),
            y_resid=np.array([0.5, -0.5, 1.0]),
            bragg_tick_sets=(
                BraggTickSet(
                    phase_id='phase-a',
                    x=np.array([0.5]),
                    h=np.array([1]),
                    k=np.array([0]),
                    ell=np.array([1]),
                    f_squared_calc=np.array([100.0]),
                    f_calc=np.array([10.0]),
                ),
            ),
            axes_labels=['2θ (degree)', 'Intensity (arb. units)'],
            title='Powder plot',
            residual_height_fraction=0.25,
            bragg_peaks_height_fraction=0.15,
            height=8,
        ),
    )

    out = capsys.readouterr().out
    assert 'Legend:' in out
    assert 'Residual (Imeas - Icalc)' in out
    assert 'Bragg peak subplot rows are available with the Plotly engine only.' in out


def test_ascii_plotter_plot_limits_oversized_series_to_detected_terminal_width(monkeypatch):
    from easydiffraction.display.plotters import ascii as ascii_mod
    from easydiffraction.display.plotters.ascii import ASCII_CHART_LEFT_PADDING
    from easydiffraction.display.plotters.ascii import ASCII_CHART_MIN_POINT_COUNT
    from easydiffraction.display.plotters.ascii import ASCII_CHART_OFFSET
    from easydiffraction.display.plotters.ascii import AsciiPlotter

    captured: dict[str, object] = {}

    def fake_plot(series, config):
        captured['call'] = (series, config)
        return 'chart'

    monkeypatch.setattr(
        ascii_mod.shutil,
        'get_terminal_size',
        lambda fallback: os.terminal_size((44, 24)),
    )
    monkeypatch.setattr(ascii_mod.asciichartpy, 'plot', fake_plot)

    AsciiPlotter().plot_powder(
        x=np.arange(256, dtype=float),
        y_series=[np.linspace(0.0, 1.0, 256)],
        labels=['density'],
        axes_labels=['x', 'y'],
        title='Width test',
        height=5,
    )

    series, config = captured['call']
    assert len(series[0]) == max(
        ASCII_CHART_MIN_POINT_COUNT,
        44 - ASCII_CHART_OFFSET - ASCII_CHART_LEFT_PADDING,
    )
    assert series[0][0] > 0.0
    assert config['offset'] == ASCII_CHART_OFFSET


def test_ascii_plotter_plot_interpolates_smaller_series_to_detected_terminal_width(monkeypatch):
    from easydiffraction.display.plotters import ascii as ascii_mod
    from easydiffraction.display.plotters.ascii import ASCII_CHART_LEFT_PADDING
    from easydiffraction.display.plotters.ascii import ASCII_CHART_MIN_POINT_COUNT
    from easydiffraction.display.plotters.ascii import ASCII_CHART_OFFSET
    from easydiffraction.display.plotters.ascii import AsciiPlotter

    captured: dict[str, object] = {}

    def fake_plot(series, config):
        captured['call'] = (series, config)
        return 'chart'

    monkeypatch.setattr(
        ascii_mod.shutil,
        'get_terminal_size',
        lambda fallback: os.terminal_size((44, 24)),
    )
    monkeypatch.setattr(ascii_mod.asciichartpy, 'plot', fake_plot)

    AsciiPlotter().plot_powder(
        x=np.arange(4, dtype=float),
        y_series=[np.array([0.0, 1.0, 0.0, 1.0])],
        labels=['density'],
        axes_labels=['x', 'y'],
        title='Interpolation test',
        height=5,
    )

    series, config = captured['call']
    assert len(series[0]) == max(
        ASCII_CHART_MIN_POINT_COUNT,
        44 - ASCII_CHART_OFFSET - ASCII_CHART_LEFT_PADDING,
    )
    assert series[0][0] == 0.0
    assert series[0][-1] == 1.0
    assert config['offset'] == ASCII_CHART_OFFSET


def test_ascii_plotter_plot_uses_fallback_width_when_terminal_size_unavailable(monkeypatch):
    from easydiffraction.display.plotters import ascii as ascii_mod
    from easydiffraction.display.plotters.ascii import ASCII_CHART_FALLBACK_POINT_COUNT
    from easydiffraction.display.plotters.ascii import ASCII_CHART_OFFSET
    from easydiffraction.display.plotters.ascii import AsciiPlotter

    captured: dict[str, object] = {}

    def fake_plot(series, config):
        captured['call'] = (series, config)
        return 'chart'

    monkeypatch.setattr(
        ascii_mod.shutil,
        'get_terminal_size',
        lambda fallback: os.terminal_size(fallback),
    )
    monkeypatch.setattr(ascii_mod.asciichartpy, 'plot', fake_plot)

    AsciiPlotter().plot_powder(
        x=np.arange(256, dtype=float),
        y_series=[np.linspace(0.0, 1.0, 256)],
        labels=['density'],
        axes_labels=['x', 'y'],
        title='Fallback width test',
        height=5,
    )

    series, config = captured['call']
    assert len(series[0]) == ASCII_CHART_FALLBACK_POINT_COUNT
    assert config['offset'] == ASCII_CHART_OFFSET


def test_ascii_plotter_plot_scatter_uses_detected_terminal_width(monkeypatch):
    from easydiffraction.display.plotters import ascii as ascii_mod
    from easydiffraction.display.plotters.ascii import ASCII_CHART_LEFT_PADDING
    from easydiffraction.display.plotters.ascii import ASCII_CHART_MIN_POINT_COUNT
    from easydiffraction.display.plotters.ascii import ASCII_CHART_OFFSET
    from easydiffraction.display.plotters.ascii import AsciiPlotter

    captured: dict[str, object] = {}

    def fake_plot(series, config):
        captured['call'] = (series, config)
        return 'chart'

    monkeypatch.setattr(
        ascii_mod.shutil,
        'get_terminal_size',
        lambda fallback: os.terminal_size((44, 24)),
    )
    monkeypatch.setattr(ascii_mod.asciichartpy, 'plot', fake_plot)

    AsciiPlotter().plot_scatter(
        x=np.arange(4, dtype=float),
        y=np.array([0.0, 1.0, 0.0, 1.0]),
        sy=np.array([0.1, 0.1, 0.1, 0.1]),
        axes_labels=['x', 'y'],
        title='Scatter width test',
        height=5,
    )

    series, config = captured['call']
    assert len(series[0]) == max(
        ASCII_CHART_MIN_POINT_COUNT,
        44 - ASCII_CHART_OFFSET - ASCII_CHART_LEFT_PADDING,
    )
    assert config['colors'] == [ascii_mod.asciichartpy.blue]


def test_ascii_plotter_plot_scatter_sorts_by_x_before_resampling(monkeypatch):
    from easydiffraction.display.plotters import ascii as ascii_mod
    from easydiffraction.display.plotters.ascii import AsciiPlotter

    captured: dict[str, object] = {}

    def fake_plot(series, config):
        captured['call'] = (series, config)
        return 'chart'

    monkeypatch.setattr(AsciiPlotter, '_chart_point_count', lambda: 4)
    monkeypatch.setattr(ascii_mod.asciichartpy, 'plot', fake_plot)

    AsciiPlotter().plot_scatter(
        x=np.array([400.0, 300.0, 200.0, 100.0]),
        y=np.array([4.0, 3.0, 2.0, 1.0]),
        sy=np.array([0.1, 0.1, 0.1, 0.1]),
        axes_labels=['Temperature', 'Parameter value'],
        title='Scatter order test',
        height=5,
    )

    series, _config = captured['call']
    assert series[0] == [1.0, 2.0, 3.0, 4.0]
