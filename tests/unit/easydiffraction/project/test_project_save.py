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
    assert (tmp_path / 'project.edi').exists()
    assert (tmp_path / 'analysis' / 'analysis.edi').exists()
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
    assert (target / 'project.edi').is_file()
    assert (target / 'analysis' / 'analysis.edi').is_file()
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
    assert 'analysis.edi' in out
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
    assert (target / 'project.edi').is_file()


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
    assert (target / 'project.edi').is_file()


def test_project_save_omits_empty_fit_state_sections(tmp_path):
    from easydiffraction.project.project import Project

    project = Project(name='no_fit_state')
    project.save_as(str(tmp_path / 'proj'))

    analysis_cif = (tmp_path / 'proj' / 'analysis' / 'analysis.edi').read_text()

    assert '_fit_parameter.parameter_unique_name' not in analysis_cif
    assert '_fit_result.result_kind' not in analysis_cif


def test_save_as_in_place_preserves_raw_sampler_state(tmp_path):
    """save_as() to the current path keeps the resumable raw chain.

    Regression: a same-path save_as() previously wiped the directory
    (and so the raw dream_state / emcee_chain groups in mcmc.h5) before
    save() rebuilt only the derived arrays, breaking resume on reload.
    """
    import h5py
    import numpy as np

    from easydiffraction.analysis.enums import FitResultKindEnum
    from easydiffraction.project.project import Project

    project = Project(name='resumable')
    project.report.html = False
    target = tmp_path / 'proj'
    project.save_as(str(target))

    # Make the analysis look like a saved Bayesian fit so the sidecar is
    # written rather than deleted as stale.
    analysis = project.analysis
    analysis.minimizer.type = 'bumps (dream)'
    analysis._set_has_persisted_fit_state(value=True)
    analysis.fit_result._set_result_kind(FitResultKindEnum.BAYESIAN.value)
    analysis._persisted_fit_state_sidecar = {
        'posterior': {
            'parameter_samples': np.zeros((2, 2, 1), dtype=float),
            'log_posterior': np.zeros((2, 2), dtype=float),
            'draw_index': np.arange(2, dtype=float),
        }
    }

    # Seed a raw resumable sampler-state group, as a real resume would.
    sidecar_path = target / 'analysis' / 'mcmc.h5'
    with h5py.File(sidecar_path, 'a') as handle:
        state = handle.create_group('dream_state')
        state.create_dataset(
            'param_names',
            data=np.array([b'lbco.cell.length_a']),
        )

    # Save in place (same path as the loaded project).
    project.save_as(str(target))

    with h5py.File(sidecar_path, 'r') as handle:
        assert 'dream_state' in handle  # raw chain survives
        assert 'posterior' in handle  # derived arrays rebuilt
