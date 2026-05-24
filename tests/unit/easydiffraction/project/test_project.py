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
    assert 'summary' in out


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

    project = Project()

    assert isinstance(project.chart, Chart)
    assert isinstance(project.table, Table)
    assert isinstance(project.display, ProjectDisplay)


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
