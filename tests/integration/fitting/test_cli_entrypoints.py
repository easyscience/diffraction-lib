# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from typer.testing import CliRunner

runner = CliRunner()


def test_cli_version_invokes_show_version(monkeypatch):
    import easydiffraction as ed
    import easydiffraction.__main__ as main_mod

    called = {'ok': False}

    def fake_show_version() -> None:
        print('VERSION_OK')
        called['ok'] = True

    monkeypatch.setattr(ed, 'show_version', fake_show_version)

    result = runner.invoke(main_mod.app, ['--version'])

    assert result.exit_code == 0
    assert called['ok'] is True
    assert 'VERSION_OK' in result.stdout


def test_cli_help_shows_and_exits_zero():
    import easydiffraction.__main__ as main_mod

    result = runner.invoke(main_mod.app, ['--help'])

    assert result.exit_code == 0
    assert 'EasyDiffraction command-line interface' in result.stdout


def test_cli_subcommands_call_utils(monkeypatch):
    import easydiffraction as ed
    import easydiffraction.__main__ as main_mod

    calls: list[str] = []
    monkeypatch.setattr(ed, 'list_tutorials', lambda: calls.append('LIST'))
    monkeypatch.setattr(
        ed,
        'download_all_tutorials',
        lambda destination='tutorials', overwrite=False: calls.append('DOWNLOAD_ALL'),
    )
    monkeypatch.setattr(
        ed,
        'download_tutorial',
        lambda id, destination='tutorials', overwrite=False: calls.append(f'DOWNLOAD_{id}'),
    )

    list_result = runner.invoke(main_mod.app, ['list-tutorials'])
    download_all_result = runner.invoke(main_mod.app, ['download-all-tutorials'])
    download_one_result = runner.invoke(main_mod.app, ['download-tutorial', '1'])

    assert list_result.exit_code == 0
    assert download_all_result.exit_code == 0
    assert download_one_result.exit_code == 0
    assert calls == ['LIST', 'DOWNLOAD_ALL', 'DOWNLOAD_1']


def test_cli_fit_loads_and_fits(monkeypatch, tmp_path):
    import easydiffraction.__main__ as main_mod
    from easydiffraction.project.project import Project

    calls: list[str] = []

    class FakeMetadata:
        _path = '/some/path'

    class FakeExperiment:
        name = 'exp1'

    class FakeProject:
        metadata = FakeMetadata()
        experiments = [FakeExperiment()]

        class _analysis:
            @staticmethod
            def fit() -> None:
                calls.append('FIT')

            class display:
                @staticmethod
                def fit_results() -> None:
                    calls.append('DISPLAY')

        analysis = _analysis()

        class _display:
            class _fit:
                @staticmethod
                def results() -> None:
                    calls.append('DISPLAY')

                @staticmethod
                def correlations() -> None:
                    calls.append('PLOT_CORR')

            fit = _fit()

            @staticmethod
            def pattern(expt_name: str, **kwargs) -> None:
                del kwargs
                calls.append(f'PLOT_{expt_name}_False')

        display = _display()

    fake_project = FakeProject()

    project_dir = tmp_path / 'proj'
    project_dir.mkdir()
    (project_dir / 'project.edstar').write_text('_metadata.name test\n')

    monkeypatch.setattr(Project, 'load', staticmethod(lambda path: fake_project))

    result = runner.invoke(main_mod.app, ['fit', str(project_dir)])

    assert result.exit_code == 0
    assert calls == ['FIT', 'DISPLAY', 'PLOT_CORR', 'PLOT_exp1_False']


def test_cli_fit_dry_clears_path(monkeypatch, tmp_path):
    import easydiffraction.__main__ as main_mod
    from easydiffraction.project.project import Project

    class FakeMetadata:
        _path = '/some/path'

    class FakeExperiment:
        name = 'exp1'

    class FakeProject:
        metadata = FakeMetadata()
        experiments = [FakeExperiment()]

        class _analysis:
            @staticmethod
            def fit() -> None:
                return None

            class display:
                @staticmethod
                def fit_results() -> None:
                    return None

        analysis = _analysis()

        class _display:
            class _fit:
                @staticmethod
                def results() -> None:
                    return None

                @staticmethod
                def correlations() -> None:
                    return None

            fit = _fit()

            @staticmethod
            def pattern(expt_name: str, **kwargs) -> None:
                del expt_name, kwargs

        display = _display()

    fake_project = FakeProject()

    project_dir = tmp_path / 'proj'
    project_dir.mkdir()
    (project_dir / 'project.edstar').write_text('_metadata.name test\n')

    monkeypatch.setattr(Project, 'load', staticmethod(lambda path: fake_project))

    result = runner.invoke(main_mod.app, ['fit', '--dry', str(project_dir)])

    assert result.exit_code == 0
    assert fake_project.metadata._path is None
