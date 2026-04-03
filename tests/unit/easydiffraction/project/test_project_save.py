# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause


def test_project_save_uses_cwd_when_no_explicit_path(monkeypatch, tmp_path, capsys):
    # ProjectInfo.path defaults to None; save() requires save_as() first
    from easydiffraction.project.project import Project

    monkeypatch.chdir(tmp_path)
    p = Project()
    p.save_as(str(tmp_path))
    out = capsys.readouterr().out
    # It should announce saving and create the three core files
    assert 'Saving project' in out
    assert (tmp_path / 'project.cif').exists()
    assert (tmp_path / 'analysis' / 'analysis.cif').exists()
    assert (tmp_path / 'summary.cif').exists()


def test_project_save_as_writes_core_files(tmp_path, monkeypatch):
    from easydiffraction.analysis.analysis import Analysis
    from easydiffraction.project.project import Project
    from easydiffraction.project.project_info import ProjectInfo
    from easydiffraction.summary.summary import Summary

    # Monkeypatch as_cif producers to avoid heavy internals
    monkeypatch.setattr(ProjectInfo, 'as_cif', lambda self: 'info')
    monkeypatch.setattr(Analysis, 'as_cif', lambda self: 'analysis')
    monkeypatch.setattr(Summary, 'as_cif', lambda self: 'summary')

    p = Project(name='p1')
    target = tmp_path / 'proj_dir'
    p.save_as(str(target))

    # Assert expected files/dirs exist
    assert (target / 'project.cif').is_file()
    assert (target / 'analysis' / 'analysis.cif').is_file()
    assert (target / 'summary.cif').is_file()
    assert (target / 'structures').is_dir()
    assert (target / 'experiments').is_dir()
