# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

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
    assert "Help for 'Project'" in out
    assert 'experiments' in out
    assert 'analysis' in out
    assert 'summary' in out


def test_project_verbosity_default():
    from easydiffraction.project.project import Project

    p = Project()
    assert p.verbosity == 'full'


def test_project_verbosity_setter():
    from easydiffraction.project.project import Project

    p = Project()
    p.verbosity = 'short'
    assert p.verbosity == 'short'
    p.verbosity = 'silent'
    assert p.verbosity == 'silent'
    p.verbosity = 'full'
    assert p.verbosity == 'full'


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
