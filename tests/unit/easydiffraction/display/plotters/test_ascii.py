# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

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

    plotter = AsciiPlotter()
    plotter.plot_powder_meas_vs_calc(
        x=np.array([0.0, 1.0, 2.0]),
        y_meas=np.array([3.0, 4.0, 5.0]),
        y_calc=np.array([2.5, 4.5, 4.0]),
        y_resid=np.array([0.5, -0.5, 1.0]),
        bragg_tick_sets=(
            BraggTickSet(
                structure_id='phase-a',
                x=np.array([0.5]),
                h=np.array([1]),
                k=np.array([0]),
                l=np.array([1]),
                intensity=np.array([100.0]),
            ),
        ),
        axes_labels=['2θ (degree)', 'Intensity (arb. units)'],
        title='Powder plot',
        residual_height_fraction=0.25,
        bragg_peaks_height_fraction=0.15,
        height=8,
    )

    out = capsys.readouterr().out
    assert 'Legend:' in out
    assert 'Residual (Imeas - Icalc)' in out
    assert 'Bragg peak subplot rows are available with the Plotly engine only.' in out
