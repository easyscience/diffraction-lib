# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from collections import UserList
import csv
from types import SimpleNamespace


def test_module_import():
    import easydiffraction.project.project as MUT

    expected_module_name = 'easydiffraction.project.project'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_project_help(capsys):
    from easydiffraction.project.project import Project

    p = Project()
    p.help()
    out = capsys.readouterr().out
    assert 'experiments' in out
    assert 'analysis' in out
    assert 'report' in out


def test_project_verbosity_default():
    from easydiffraction.project.project import Project

    p = Project()
    assert p.verbosity.fit.value == 'full'


def test_project_verbosity_setter():
    from easydiffraction.project.project import Project

    p = Project()
    p.verbosity = 'short'
    assert p.verbosity.fit.value == 'short'
    p.verbosity = 'silent'
    assert p.verbosity.fit.value == 'silent'
    p.verbosity = 'full'
    assert p.verbosity.fit.value == 'full'


def test_project_verbosity_invalid():
    import pytest

    from easydiffraction.project.project import Project

    p = Project()
    with pytest.raises(ValueError, match="'verbose' is not a valid VerbosityEnum"):
        p.verbosity = 'verbose'


def test_project_free_params_aggregate_structures_and_experiments():
    from easydiffraction.project.project import Project

    project = Project()
    structure_param = object()
    experiment_param = object()
    project._structures = SimpleNamespace(free_parameters=[structure_param])
    project._experiments = SimpleNamespace(free_parameters=[experiment_param])

    assert project.free_parameters == [structure_param, experiment_param]


def test_project_exposes_chart_table_and_display_facades():
    from easydiffraction.project.categories.chart import Chart
    from easydiffraction.project.categories.table import Table
    from easydiffraction.project.display import ProjectDisplay
    from easydiffraction.project.project import Project
    from easydiffraction.report import Report

    project = Project()

    assert isinstance(project.chart, Chart)
    assert isinstance(project.table, Table)
    assert isinstance(project.display, ProjectDisplay)
    assert isinstance(project.report, Report)
    assert hasattr(project.report, 'save')


def test_apply_params_from_csv_resolves_relative_file_paths(tmp_path):
    from easydiffraction.project.project import Project

    project = Project()
    project.info.path = tmp_path / 'project'
    analysis_dir = project.info.path / 'analysis'
    analysis_dir.mkdir(parents=True)
    data_dir = project.info.path / 'experiments' / 'scan'
    data_dir.mkdir(parents=True)
    data_path = data_dir / 'scan_001.dat'
    data_path.write_text('1 2 3\n')

    csv_path = analysis_dir / 'results.csv'
    with csv_path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=['file_path'])
        writer.writeheader()
        writer.writerow({'file_path': 'experiments/scan/scan_001.dat'})

    loaded_paths: list[str] = []

    class Experiment:
        diffrn = SimpleNamespace()

        def _load_ascii_data_to_experiment(self, file_path):
            loaded_paths.append(file_path)

    class Structures(UserList):
        parameters = []

    class Experiments:
        parameters = []

        @staticmethod
        def values():
            return [experiment]

    experiment = Experiment()
    project._structures = Structures()
    project._experiments = Experiments()

    project.apply_params_from_csv(0)

    assert loaded_paths == [str(data_path)]


def test_undo_fit_save_reload_preserves_fit_parameter_controls(tmp_path):
    from easydiffraction.project.project import Project

    project = Project(name='undo_reload')
    project.structures.create(name='lbco')
    structure = project.structures['lbco']
    structure.space_group.name_h_m = 'P m -3 m'
    parameter = structure.cell.length_a
    parameter.free = True
    parameter.value = 3.91
    parameter.uncertainty = 0.04
    parameter.fit_min = 3.8
    parameter.fit_max = 4.0
    parameter._set_fit_bounds_uncertainty_multiplier(4.0)

    project.analysis.fit_parameters.create(
        param_unique_name=parameter.unique_name,
        fit_min=parameter.fit_min,
        fit_max=parameter.fit_max,
        fit_bounds_uncertainty_multiplier=4.0,
        start_value=3.87,
        start_uncertainty=0.02,
    )
    project.analysis.fit_result._set_result_kind('deterministic')
    project.analysis.fit_result._set_success(value=True)
    project.analysis.fit_result._set_message('Fit converged')
    project.analysis.fit_result._set_iterations(12)
    project.analysis.fit_result._set_fitting_time(0.5)
    project.analysis.fit_result._set_reduced_chi_square(1.1)
    project.analysis._set_has_persisted_fit_state(value=True)
    project.save_as(str(tmp_path / 'proj'))

    outcome = project.analysis.undo_fit()
    project.save()
    loaded = Project.load(str(tmp_path / 'proj'))
    loaded_parameter = loaded.structures['lbco'].cell.length_a
    loaded_row = loaded.analysis.fit_parameters[loaded_parameter.unique_name]
    second_outcome = loaded.analysis.undo_fit()

    assert outcome.was_no_op is False
    assert loaded.analysis._has_persisted_fit_state() is False
    assert loaded.analysis.fit_results is None
    assert loaded_row.fit_min.value == 3.8
    assert loaded_row.fit_max.value == 4.0
    assert loaded_row.fit_bounds_uncertainty_multiplier.value == 4.0
    assert loaded_row.start_value.value == 3.87
    assert loaded_row.start_uncertainty.value == 0.02
    assert loaded_parameter.value == 3.87
    assert loaded_parameter.fit_min == 3.8
    assert loaded_parameter.fit_max == 4.0
    assert loaded_parameter.fit_bounds_uncertainty_multiplier == 4.0
    assert loaded_parameter._fit_start_value == 3.87
    assert loaded_parameter._fit_start_uncertainty == 0.02
    assert second_outcome.was_no_op is True


def test_project_save_report_writes_submission_cif(tmp_path):
    from easydiffraction.project.project import Project

    project = Project(name='report_project')
    project.save_as(str(tmp_path / 'proj'))
    project.report.cif = True
    project.save()

    assert not (tmp_path / 'proj' / 'summary.cif').exists()
    assert (tmp_path / 'proj' / 'reports' / 'report_project.cif').is_file()


def test_project_save_rejects_removed_report_keyword(tmp_path):
    import pytest

    from easydiffraction.project.project import Project

    project = Project(name='checked_report')
    project.save_as(str(tmp_path / 'proj'))

    with pytest.raises(TypeError, match="unexpected keyword argument 'report'"):
        project.save(report=True)
