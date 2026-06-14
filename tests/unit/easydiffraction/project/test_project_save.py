# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause


def test_project_save_uses_cwd_when_no_explicit_path(monkeypatch, tmp_path, capsys):
    # ProjectInfo.path defaults to None; save() requires save_as() first
    from easydiffraction.project.project import Project

    monkeypatch.chdir(tmp_path)
    p = Project()
    p.report.html = False
    p.save_as(str(tmp_path))
    out = capsys.readouterr().out
    # It should announce saving and create the three core files
    assert 'Saving project' in out
    assert (tmp_path / 'project.edifa').exists()
    assert (tmp_path / 'analysis' / 'analysis.edifa').exists()
    assert not (tmp_path / 'summary.cif').exists()
    assert not (tmp_path / 'reports').exists()


def test_project_save_as_writes_core_files(tmp_path, monkeypatch):
    from easydiffraction.analysis.analysis import Analysis
    from easydiffraction.project.project import Project
    from easydiffraction.project.project_metadata import ProjectMetadata

    # Monkeypatch as_cif producers to avoid heavy internals
    monkeypatch.setattr(ProjectMetadata, 'as_cif', property(lambda self: 'info'))
    monkeypatch.setattr(Analysis, 'as_cif', property(lambda self: 'analysis'))

    p = Project(name='p1')
    p.report.html = False
    target = tmp_path / 'proj_dir'
    p.save_as(str(target))

    # Assert expected files/dirs exist
    assert (target / 'project.edifa').is_file()
    assert (target / 'analysis' / 'analysis.edifa').is_file()
    assert not (target / 'summary.cif').exists()
    assert not (target / 'reports').exists()
    assert (target / 'structures').is_dir()
    assert (target / 'experiments').is_dir()


def test_project_save_lists_existing_analysis_results_csv(tmp_path, monkeypatch, capsys):
    from easydiffraction.analysis.analysis import Analysis
    from easydiffraction.project.project import Project
    from easydiffraction.project.project_metadata import ProjectMetadata

    monkeypatch.setattr(ProjectMetadata, 'as_cif', property(lambda self: 'info'))
    monkeypatch.setattr(Analysis, 'as_cif', property(lambda self: 'analysis'))

    target = tmp_path / 'proj_dir'
    analysis_dir = target / 'analysis'
    analysis_dir.mkdir(parents=True)
    (analysis_dir / 'results.csv').write_text('file_path\nscan_001.xye\n')

    p = Project(name='p1')
    p.metadata.path = target
    p.save()

    out = capsys.readouterr().out
    assert 'analysis.edifa' in out
    assert 'results.csv' in out


def test_project_save_as_overwrites_existing_directory_by_default(tmp_path, monkeypatch):
    from easydiffraction.analysis.analysis import Analysis
    from easydiffraction.project.project import Project
    from easydiffraction.project.project_metadata import ProjectMetadata

    monkeypatch.setattr(ProjectMetadata, 'as_cif', property(lambda self: 'info'))
    monkeypatch.setattr(Analysis, 'as_cif', property(lambda self: 'analysis'))

    target = tmp_path / 'proj_dir'
    stale_file = target / 'stale.txt'
    target.mkdir()
    stale_file.write_text('stale')

    project = Project(name='p1')
    project.save_as(str(target))

    assert not stale_file.exists()
    assert (target / 'project.edifa').is_file()


def test_project_save_as_preserves_existing_directory_when_disabled(tmp_path, monkeypatch):
    from easydiffraction.analysis.analysis import Analysis
    from easydiffraction.project.project import Project
    from easydiffraction.project.project_metadata import ProjectMetadata

    monkeypatch.setattr(ProjectMetadata, 'as_cif', property(lambda self: 'info'))
    monkeypatch.setattr(Analysis, 'as_cif', property(lambda self: 'analysis'))

    target = tmp_path / 'proj_dir'
    stale_file = target / 'stale.txt'
    target.mkdir()
    stale_file.write_text('stale')

    project = Project(name='p1')
    project.save_as(
        str(target),
        overwrite=False,
    )

    assert stale_file.exists()
    assert (target / 'project.edifa').is_file()


def test_project_save_omits_empty_fit_state_sections(tmp_path):
    from easydiffraction.project.project import Project

    project = Project(name='no_fit_state')
    project.save_as(str(tmp_path / 'proj'))

    analysis_cif = (tmp_path / 'proj' / 'analysis' / 'analysis.edifa').read_text()

    assert '_fit_parameter.parameter_unique_name' not in analysis_cif
    assert '_fit_result.result_kind' not in analysis_cif
