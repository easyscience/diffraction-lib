# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause


def test_project_load_raises_on_missing_directory(tmp_path):
    import pytest

    from easydiffraction.project.project import Project

    missing_dir = tmp_path / 'nonexistent'
    with pytest.raises(FileNotFoundError, match='not found'):
        Project.load(str(missing_dir))


def test_project_load_reads_project_info(tmp_path):
    from easydiffraction.project.project import Project

    p = Project(name='myproj', title='My Title', description='A description')
    p.save_as(str(tmp_path / 'proj'))

    loaded = Project.load(str(tmp_path / 'proj'))
    assert loaded.name == 'myproj'
    assert loaded.metadata.title == 'My Title'
    assert loaded.metadata.description == 'A description'
    assert loaded.metadata.path is not None
