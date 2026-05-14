# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from typer.testing import CliRunner

runner = CliRunner()


def test_module_import():
    import easydiffraction.__main__ as MUT

    expected_module_name = 'easydiffraction.__main__'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_cli_version_invokes_show_version(monkeypatch, capsys):
    import easydiffraction as ed
    import easydiffraction.__main__ as main_mod

    called = {'ok': False}

    def fake_show_version():
        print('VERSION_OK')
        called['ok'] = True

    monkeypatch.setattr(ed, 'show_version', fake_show_version)
    result = runner.invoke(main_mod.app, ['--version'])
    assert result.exit_code == 0
    assert called['ok']
    assert 'VERSION_OK' in result.stdout


def test_cli_help_shows_and_exits_zero():
    import easydiffraction.__main__ as main_mod

    result = runner.invoke(main_mod.app, ['--help'])
    assert result.exit_code == 0
    assert 'EasyDiffraction command-line interface' in result.stdout


def test_cli_subcommands_call_utils(monkeypatch):
    import easydiffraction as ed
    import easydiffraction.__main__ as main_mod

    logs = []
    monkeypatch.setattr(ed, 'list_tutorials', lambda: logs.append('LIST'))
    monkeypatch.setattr(
        ed,
        'download_all_tutorials',
        lambda destination='tutorials', overwrite=False: logs.append('DOWNLOAD_ALL'),
    )
    monkeypatch.setattr(
        ed,
        'download_tutorial',
        lambda id, destination='tutorials', overwrite=False: logs.append(f'DOWNLOAD_{id}'),
    )

    res1 = runner.invoke(main_mod.app, ['list-tutorials'])
    res2 = runner.invoke(main_mod.app, ['download-all-tutorials'])
    res3 = runner.invoke(main_mod.app, ['download-tutorial', '1'])

    assert res1.exit_code == 0
    assert res2.exit_code == 0
    assert res3.exit_code == 0
    assert logs == ['LIST', 'DOWNLOAD_ALL', 'DOWNLOAD_1']


def test_cli_fit_loads_and_fits(monkeypatch, tmp_path):
    import easydiffraction.__main__ as main_mod
    from easydiffraction.project.project import Project

    calls = []

    class FakeInfo:
        _path = '/some/path'

    class FakeExperiment:
        name = 'exp1'

    class FakeProject:
        info = FakeInfo()
        experiments = [FakeExperiment()]

        class _analysis:
            @staticmethod
            def fit():
                calls.append('FIT')

            class display:
                @staticmethod
                def fit_results():
                    calls.append('DISPLAY')

        analysis = _analysis()

        class _display:
            class _fit:
                @staticmethod
                def results():
                    calls.append('DISPLAY')

                @staticmethod
                def correlations():
                    calls.append('PLOT_CORR')

            fit = _fit()

            @staticmethod
            def pattern(expt_name, **kwargs):
                del kwargs
                calls.append(f'PLOT_{expt_name}_False')

        display = _display()

    fake_project = FakeProject()

    # Create a minimal project directory so load doesn't fail on path check
    proj_dir = tmp_path / 'proj'
    proj_dir.mkdir()
    (proj_dir / 'project.cif').write_text('_project.id test\n')

    monkeypatch.setattr(Project, 'load', staticmethod(lambda dir_path: fake_project))

    result = runner.invoke(main_mod.app, ['fit', str(proj_dir)])
    assert result.exit_code == 0
    assert calls == ['FIT', 'DISPLAY', 'PLOT_CORR', 'PLOT_exp1_False']


def test_cli_fit_dry_clears_path(monkeypatch, tmp_path):
    import easydiffraction.__main__ as main_mod
    from easydiffraction.project.project import Project

    class FakeInfo:
        _path = '/some/path'

    class FakeExperiment:
        name = 'exp1'

    class FakeProject:
        info = FakeInfo()
        experiments = [FakeExperiment()]

        class _analysis:
            @staticmethod
            def fit():
                pass

            class display:
                @staticmethod
                def fit_results():
                    pass

        analysis = _analysis()

        class _display:
            class _fit:
                @staticmethod
                def results():
                    pass

                @staticmethod
                def correlations():
                    pass

            fit = _fit()

            @staticmethod
            def pattern(expt_name, **kwargs):
                del expt_name, kwargs

        display = _display()

    fake_project = FakeProject()

    proj_dir = tmp_path / 'proj'
    proj_dir.mkdir()
    (proj_dir / 'project.cif').write_text('_project.id test\n')

    monkeypatch.setattr(Project, 'load', staticmethod(lambda dir_path: fake_project))

    result = runner.invoke(main_mod.app, ['fit', '--dry', str(proj_dir)])
    assert result.exit_code == 0
    assert fake_project.info._path is None
