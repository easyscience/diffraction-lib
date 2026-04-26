# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

"""Integration tests for the Plotter facade on a fitted project."""


def test_plot_meas(lbco_fitted_project):
    project = lbco_fitted_project
    project.display.plotter.plot_meas(expt_name='hrpt')


def test_plot_calc(lbco_fitted_project):
    project = lbco_fitted_project
    project.display.plotter.plot_calc(expt_name='hrpt')


def test_plot_meas_vs_calc(lbco_fitted_project):
    project = lbco_fitted_project
    project.display.plotter.plot_meas_vs_calc(expt_name='hrpt')


def test_plot_meas_with_range(lbco_fitted_project):
    project = lbco_fitted_project
    project.display.plotter.plot_meas(expt_name='hrpt', x_min=20, x_max=80)


def test_plot_meas_vs_calc_with_range(lbco_fitted_project):
    project = lbco_fitted_project
    project.display.plotter.plot_meas_vs_calc(expt_name='hrpt', x_min=20, x_max=80)
