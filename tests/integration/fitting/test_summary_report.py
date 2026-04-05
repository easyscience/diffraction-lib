# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

"""Integration tests for Summary report generation and CIF export."""


def test_show_report(lbco_fitted_project):
    project = lbco_fitted_project
    project.summary.show_report()


def test_show_project_info(lbco_fitted_project):
    project = lbco_fitted_project
    project.summary.show_project_info()


def test_show_crystallographic_data(lbco_fitted_project):
    project = lbco_fitted_project
    project.summary.show_crystallographic_data()


def test_show_experimental_data(lbco_fitted_project):
    project = lbco_fitted_project
    project.summary.show_experimental_data()


def test_show_fitting_details(lbco_fitted_project):
    project = lbco_fitted_project
    project.summary.show_fitting_details()


def test_summary_as_cif(lbco_fitted_project):
    project = lbco_fitted_project
    cif_text = project.summary.as_cif()
    assert isinstance(cif_text, str)
    assert len(cif_text) > 0
