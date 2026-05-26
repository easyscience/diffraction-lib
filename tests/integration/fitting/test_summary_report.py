# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

"""Integration tests for report generation and CIF export."""


def test_show_report(lbco_fitted_project):
    project = lbco_fitted_project
    project.report.show_report()


def test_show_project_info(lbco_fitted_project):
    project = lbco_fitted_project
    project.report.show_project_info()


def test_show_crystallographic_data(lbco_fitted_project):
    project = lbco_fitted_project
    project.report.show_crystallographic_data()


def test_show_experimental_data(lbco_fitted_project):
    project = lbco_fitted_project
    project.report.show_experimental_data()


def test_show_fitting_details(lbco_fitted_project):
    project = lbco_fitted_project
    project.report.show_fitting_details()


def test_report_save(lbco_fitted_project, tmp_path):
    project = lbco_fitted_project
    project.save_as(str(tmp_path / 'proj'))
    report_path = project.report.save()
    assert report_path.is_file()
    assert report_path.read_text(encoding='utf-8').startswith('data_global\n')
