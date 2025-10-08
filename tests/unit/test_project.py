import datetime
import os
import pathlib
import time
from unittest.mock import MagicMock, ANY
from unittest.mock import patch

from easydiffraction.analysis.analysis import Analysis
from easydiffraction.experiments.experiments import Experiments
from easydiffraction.project import Project
from easydiffraction.project import ProjectInfo
from easydiffraction.sample_models.sample_models import SampleModels
from easydiffraction.summary import Summary


def _normalize_posix(p: pathlib.Path) -> str:
    """Return a normalized POSIX-style path string with a leading '/'.

    This makes tests robust across Windows and POSIX when using paths like
    '/test/path' that, on Windows, become '\\test\\path'. We avoid relying on
    drive letters or platform-specific semantics for these synthetic test paths.
    """
    s = str(p).replace('\\', '/')
    if not s.startswith('/'):
        s = '/' + s.lstrip('/')
    return s

# ------------------------------------------
# Tests for ProjectInfo
# ------------------------------------------


def test_project_info_initialization():
    project_info = ProjectInfo()

    # Assertions
    assert project_info.name == 'untitled_project'
    assert project_info.title == 'Untitled Project'
    assert project_info.description == ''
    assert project_info.path == pathlib.Path.cwd()
    assert isinstance(project_info.created, datetime.datetime)
    assert isinstance(project_info.last_modified, datetime.datetime)


def test_project_info_setters():
    project_info = ProjectInfo()

    # Set values
    project_info.name = 'test_project'
    project_info.title = 'Test Project'
    project_info.description = 'This is a test project.'
    project_info.path = '/test/path'

    # Assertions
    assert project_info.name == 'test_project'
    assert project_info.title == 'Test Project'
    assert project_info.description == 'This is a test project.'
    # Use POSIX form for cross-platform consistency (Windows vs POSIX separators)
    assert _normalize_posix(project_info.path) == '/test/path'


def test_project_info_update_last_modified():
    project_info = ProjectInfo()
    initial_last_modified = project_info.last_modified

    # Add a small delay to ensure the timestamps differ
    time.sleep(0.001)
    project_info.update_last_modified()

    # Assertions
    assert project_info.last_modified > initial_last_modified


def test_project_info_as_cif():
    project_info = ProjectInfo()
    project_info.name = 'test_project'
    project_info.title = 'Test Project'
    project_info.description = 'This is a test project.'

    cif = project_info.as_cif

    # Assertions
    assert '_project.id               test_project' in cif
    assert "_project.title            'Test Project'" in cif
    assert "_project.description      'This is a test project.'" in cif


@patch('builtins.print')
def test_project_info_show_as_cif(mock_print):
    project_info = ProjectInfo()
    project_info.name = 'test_project'
    project_info.title = 'Test Project'
    project_info.description = 'This is a test project.'

    project_info.show_as_cif()

    # Assertions
    mock_print.assert_called()


# ------------------------------------------
# Tests for Project
# ------------------------------------------


def test_project_initialization():
    with (
        patch('easydiffraction.sample_models.sample_models.SampleModels'),
        patch('easydiffraction.experiments.experiments.Experiments'),
        patch('easydiffraction.analysis.analysis.Analysis'),
        patch('easydiffraction.summary.Summary'),
    ):
        project = Project()  # Directly assign the instance to a variable

    # Assertions
    assert project.name == 'untitled_project'
    assert isinstance(project.sample_models, SampleModels)
    assert isinstance(project.experiments, Experiments)
    assert isinstance(project.analysis, Analysis)
    assert isinstance(project.summary, Summary)


@patch('builtins.print')
def test_project_load(mock_print):
    with (
        patch('easydiffraction.sample_models.sample_models.SampleModels'),
        patch('easydiffraction.experiments.experiments.Experiments'),
        patch('easydiffraction.analysis.analysis.Analysis'),
        patch('easydiffraction.summary.Summary'),
    ):
        project = Project()  # Directly assign the instance to a variable

    project.load('/test/path')

    # Assertions
    # path is normalised/stored as a pathlib.Path
    assert _normalize_posix(project.info.path) == '/test/path'
    assert 'Loading project 📦 from /test/path' in mock_print.call_args_list[0][0][0]


@patch('builtins.print')
@patch('pathlib.Path.open', new_callable=MagicMock)
@patch('pathlib.Path.mkdir')
def test_project_save(mock_mkdir, mock_open, mock_print):
    with (
        patch('easydiffraction.sample_models.sample_models.SampleModels'),
        patch('easydiffraction.experiments.experiments.Experiments'),
        patch('easydiffraction.analysis.analysis.Analysis'),
        patch('easydiffraction.summary.Summary'),
    ):
        project = Project()  # Directly assign the instance to a variable

    project.info.path = '/test/path'
    project.save()

    # Assertions
    # Bound Path.mkdir call does not pass the path object itself as first arg
    mock_mkdir.assert_any_call(parents=True, exist_ok=True)
    # Bound Path.open receives only the mode (path is bound); ensure at least one write call
    mock_open.assert_any_call('w')


@patch('builtins.print')
@patch('pathlib.Path.open', new_callable=MagicMock)
@patch('pathlib.Path.mkdir')
def test_project_save_as(mock_mkdir, mock_open, mock_print):
    with (
        patch('easydiffraction.sample_models.sample_models.SampleModels'),
        patch('easydiffraction.experiments.experiments.Experiments'),
        patch('easydiffraction.analysis.analysis.Analysis'),
        patch('easydiffraction.summary.Summary'),
    ):
        project = Project()  # Directly assign the instance to a variable

    project.save_as('new_project_path')

    # Assertions
    assert project.info.path.name == 'new_project_path'
    mock_mkdir.assert_any_call(parents=True, exist_ok=True)
    mock_open.assert_any_call('w')


def test_project_sample_models():
    with (
        patch('easydiffraction.sample_models.sample_models.SampleModels'),
        patch('easydiffraction.experiments.experiments.Experiments'),
        patch('easydiffraction.analysis.analysis.Analysis'),
        patch('easydiffraction.summary.Summary'),
    ):
        project = Project()  # Directly assign the instance to a variable

    sample_models = MagicMock()
    project.sample_models = sample_models

    # Assertions
    assert project.sample_models == sample_models


def test_project_experiments():
    with (
        patch('easydiffraction.sample_models.sample_models.SampleModels'),
        patch('easydiffraction.experiments.experiments.Experiments'),
        patch('easydiffraction.analysis.analysis.Analysis'),
        patch('easydiffraction.summary.Summary'),
    ):
        project = Project()  # Directly assign the instance to a variable

    experiments = MagicMock()
    project.experiments = experiments

    # Assertions
    assert project.experiments == experiments
