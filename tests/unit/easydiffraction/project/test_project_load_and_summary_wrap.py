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
    assert loaded.info.title == 'My Title'
    assert loaded.info.description == 'A description'
    assert loaded.info.path is not None


def test_summary_show_project_info_wraps_description(capsys):
    from easydiffraction.summary.summary import Summary

    long_desc = ' '.join(['desc'] * 50)  # long text to trigger wrapping

    class Info:
        title = 'T'
        description = long_desc

    class Project:
        def __init__(self):
            self.info = Info()

    s = Summary(Project())
    s.show_project_info()
    out = capsys.readouterr().out
    # Title and Description paragraph headers present
    assert 'PROJECT INFO' in out
    assert 'Title' in out
    assert 'Description' in out
    # Ensure multiple lines of description were printed (wrapped)
    # Keep the exact word count and verify the presence of line breaks in the description block
    assert out.count('desc') == 50  # all words are present exactly once
    assert '\ndesc ' in out or ' desc\n' in out  # wrapped across lines
