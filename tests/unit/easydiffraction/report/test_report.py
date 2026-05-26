# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from types import SimpleNamespace


def _project(tmp_path):
    return SimpleNamespace(
        name='report_project',
        info=SimpleNamespace(path=tmp_path),
        structures={},
        experiments={},
        analysis=SimpleNamespace(
            minimizer=SimpleNamespace(type='lmfit'),
            fit_result=SimpleNamespace(),
        ),
    )


def test_report_save_writes_submission_cif(tmp_path):
    from easydiffraction.report.report import Report

    report = Report(_project(tmp_path))

    report_path = report.save()

    assert report_path == tmp_path / 'reports' / 'report_project.cif'
    assert report_path.is_file()
    assert report_path.read_text(encoding='utf-8').startswith('data_global\n')


def test_report_save_check_runs_validation(tmp_path, monkeypatch):
    from easydiffraction.report.report import Report

    report = Report(_project(tmp_path))
    checked_paths = []

    def fake_check(*, path=None):
        checked_paths.append(path)

    monkeypatch.setattr(report, 'check', fake_check)

    report_path = report.save(check=True)

    assert checked_paths == [report_path]


def test_report_show_report_prints_sections(capsys):
    from easydiffraction.report.report import Report

    class Info:
        title = 'T'
        description = ''

    class Project:
        def __init__(self):
            self.info = Info()
            self.structures = {}  # empty mapping to exercise loops safely
            self.experiments = {}  # empty mapping to exercise loops safely

            class A:
                class Minimizer:
                    type = 'lmfit'

                minimizer = Minimizer()

                class R:
                    reduced_chi_square = 0.0

                fit_results = R()

            self.analysis = A()

    report = Report(Project())
    report.show_report()
    out = capsys.readouterr().out
    # Verify that all top-level sections appear (titles are uppercased by formatter)
    assert 'PROJECT INFO' in out
    assert 'CRYSTALLOGRAPHIC DATA' in out
    assert 'EXPERIMENTS' in out
    assert 'FITTING' in out


def test_report_help(capsys):
    from easydiffraction.report.report import Report

    class P:
        pass

    report = Report(P())
    report.help()
    out = capsys.readouterr().out
    assert 'save()' in out
    assert 'check()' in out
    assert 'show_report()' in out
    assert 'show_project_info()' in out
    assert 'show_fitting_details()' in out


def test_module_import():
    import easydiffraction.report.report as MUT

    expected_module_name = 'easydiffraction.report.report'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name
