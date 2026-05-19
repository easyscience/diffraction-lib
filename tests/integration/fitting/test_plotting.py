# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

"""Integration tests for ``project.display.pattern``."""


def test_pattern_auto(lbco_fitted_project):
    project = lbco_fitted_project
    project.display.pattern(expt_name='hrpt')


def test_pattern_measured(lbco_fitted_project):
    project = lbco_fitted_project
    project.display.pattern(expt_name='hrpt', include='measured')


def test_pattern_measured_vs_calculated(lbco_fitted_project):
    project = lbco_fitted_project
    project.display.pattern(expt_name='hrpt', include=('measured', 'calculated'))


def test_pattern_with_range(lbco_fitted_project):
    project = lbco_fitted_project
    project.display.pattern(expt_name='hrpt', x_min=20, x_max=80)


def test_show_pattern_options(lbco_fitted_project):
    project = lbco_fitted_project
    project.display.show_pattern_options(expt_name='hrpt')
