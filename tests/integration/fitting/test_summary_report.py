# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

"""Integration tests for report generation and CIF export."""


def test_report_save(lbco_fitted_project, tmp_path):
    project = lbco_fitted_project
    project.save_as(str(tmp_path / 'proj'))
    project.report.cif = True
    report_paths = project.report.save()
    report_path = report_paths[0]

    assert len(report_paths) == 1
    assert report_path.is_file()
    assert report_path.read_text(encoding='utf-8').startswith('data_global\n')
