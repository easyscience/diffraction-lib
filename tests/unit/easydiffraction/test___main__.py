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
    monkeypatch.setattr(ed, 'list_data', lambda: logs.append('LIST_DATA'))
    monkeypatch.setattr(
        ed,
        'download_data',
        lambda name, destination='data', overwrite=False: logs.append(
            f'DATA_{name}_{destination}_{overwrite}'
        ),
    )
    monkeypatch.setattr(ed, 'list_tutorials', lambda: logs.append('LIST'))
    monkeypatch.setattr(
        ed,
        'download_all_tutorials',
        lambda destination='tutorials', overwrite=False: logs.append('DOWNLOAD_ALL'),
    )
    monkeypatch.setattr(
        ed,
        'download_tutorial',
        lambda name, destination='tutorials', overwrite=False: logs.append(f'DOWNLOAD_{name}'),
    )

    res0 = runner.invoke(main_mod.app, ['list-data'])
    res1 = runner.invoke(
        main_mod.app,
        ['download-data', 'proj-lbco-hrpt', '--destination', 'projects'],
    )
    res2 = runner.invoke(main_mod.app, ['list-tutorials'])
    res3 = runner.invoke(main_mod.app, ['download-all-tutorials'])
    res4 = runner.invoke(main_mod.app, ['download-tutorial', 'refine-lbco-hrpt-from-cif'])

    assert res0.exit_code == 0
    assert res1.exit_code == 0
    assert res2.exit_code == 0
    assert res3.exit_code == 0
    assert res4.exit_code == 0
    assert logs == [
        'LIST_DATA',
        'DATA_proj-lbco-hrpt_projects_False',
        'LIST',
        'DOWNLOAD_ALL',
        'DOWNLOAD_refine-lbco-hrpt-from-cif',
    ]


def test_cli_removed_report_commands_are_unknown(tmp_path):
    import easydiffraction.__main__ as main_mod

    project_dir = tmp_path / 'proj'

    save_result = runner.invoke(main_mod.app, ['save', str(project_dir)])
    save_report_result = runner.invoke(main_mod.app, ['save-report', str(project_dir)])

    assert save_result.exit_code != 0
    assert save_report_result.exit_code != 0
    assert "No such command 'save'" in save_result.output
    assert "No such command 'save-report'" in save_report_result.output


def test_cli_project_first_argument_normalization_supports_global_data_commands():
    import easydiffraction.__main__ as main_mod

    assert main_mod._normalized_cli_args(['list-data']) == ['list-data']
    assert main_mod._normalized_cli_args(['download-data', '30']) == ['download-data', '30']


def test_cli_project_first_argument_normalization_excludes_removed_report_commands():
    import easydiffraction.__main__ as main_mod

    assert main_mod._normalized_cli_args(['project-dir', 'save']) == ['project-dir', 'save']
    assert main_mod._normalized_cli_args(['project-dir', 'save-report']) == [
        'project-dir',
        'save-report',
    ]


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
    (proj_dir / 'project.edi').write_text('_project.id test\n')

    monkeypatch.setattr(Project, 'load', staticmethod(lambda dir_path: fake_project))

    result = runner.invoke(main_mod.app, ['fit', str(proj_dir)])
    assert result.exit_code == 0
    assert calls == ['FIT', 'DISPLAY', 'PLOT_CORR', 'PLOT_exp1_False']


def test_cli_fit_skips_fit_reports_for_sequential_mode(monkeypatch, tmp_path):
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
            class _fitting_mode:
                type = 'sequential'

            fitting_mode = _fitting_mode()

            @staticmethod
            def fit():
                calls.append('FIT')

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

    proj_dir = tmp_path / 'proj'
    proj_dir.mkdir()
    (proj_dir / 'project.edi').write_text('_project.id test\n')

    monkeypatch.setattr(Project, 'load', staticmethod(lambda dir_path: fake_project))

    result = runner.invoke(main_mod.app, ['fit', str(proj_dir)])
    assert result.exit_code == 0
    assert calls == ['FIT', 'PLOT_exp1_False']


def test_cli_fit_dry_clears_path(monkeypatch, tmp_path):
    import easydiffraction.__main__ as main_mod
    from easydiffraction.project.project import Project

    class FakeInfo:
        _path = '/some/path'

    class FakeExperiment:
        name = 'exp1'

    class FakeProject:
        metadata = FakeInfo()
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
    (proj_dir / 'project.edi').write_text('_project.id test\n')

    monkeypatch.setattr(Project, 'load', staticmethod(lambda dir_path: fake_project))

    result = runner.invoke(main_mod.app, ['fit', '--dry', str(proj_dir)])
    assert result.exit_code == 0
    assert fake_project.metadata._path is None


def test_cli_undo_noop_exits_zero_and_does_not_save(monkeypatch, tmp_path):
    import easydiffraction.__main__ as main_mod
    from easydiffraction.analysis import UndoFitOutcome

    calls: list[str] = []

    class FakeAnalysis:
        @staticmethod
        def undo_fit():
            calls.append('UNDO')
            return UndoFitOutcome(
                restored_parameter_names=(),
                cleared_fit_result=False,
                cleared_sidecar=False,
                was_no_op=True,
            )

    class FakeProject:
        name = 'demo_project'
        analysis = FakeAnalysis()

        @staticmethod
        def save():
            calls.append('SAVE')

    proj_dir = tmp_path / 'proj'
    monkeypatch.setattr(main_mod, '_load_project', lambda project_dir: FakeProject())

    result = runner.invoke(main_mod.app, ['undo', str(proj_dir)])

    assert result.exit_code == 0
    assert calls == ['UNDO']
    assert "No fit to undo for 'demo_project'. Project state is unchanged." in result.stdout


def test_cli_undo_dry_uses_outcome_summary_without_saving(monkeypatch, tmp_path):
    import easydiffraction.__main__ as main_mod
    from easydiffraction.analysis import UndoFitOutcome

    calls: list[str] = []

    class FakeAnalysis:
        @staticmethod
        def undo_fit():
            calls.append('UNDO')
            return UndoFitOutcome(
                restored_parameter_names=('a', 'b'),
                cleared_fit_result=True,
                cleared_sidecar=True,
                was_no_op=False,
            )

    class FakeProject:
        name = 'demo_project'
        analysis = FakeAnalysis()

        @staticmethod
        def save():
            calls.append('SAVE')

    proj_dir = tmp_path / 'proj'
    monkeypatch.setattr(main_mod, '_load_project', lambda project_dir: FakeProject())

    result = runner.invoke(main_mod.app, ['undo', '--dry', str(proj_dir)])

    assert result.exit_code == 0
    assert calls == ['UNDO']
    assert "Would undo last fit for 'demo_project'" in result.stdout
    assert '2 parameters would be restored to pre-fit values' in result.stdout
    assert 'analysis.fit_results would be cleared' in result.stdout
    assert 'analysis/results.h5 (Bayesian sidecar) would be cleared' in result.stdout


def test_cli_undo_saves_after_real_rollback(monkeypatch, tmp_path):
    import easydiffraction.__main__ as main_mod
    from easydiffraction.analysis import UndoFitOutcome

    calls: list[str] = []

    class FakeAnalysis:
        @staticmethod
        def undo_fit():
            calls.append('UNDO')
            return UndoFitOutcome(
                restored_parameter_names=('a',),
                cleared_fit_result=True,
                cleared_sidecar=False,
                was_no_op=False,
            )

    class FakeProject:
        name = 'demo_project'
        analysis = FakeAnalysis()

        @staticmethod
        def save():
            calls.append('SAVE')

    proj_dir = tmp_path / 'proj'
    monkeypatch.setattr(main_mod, '_load_project', lambda project_dir: FakeProject())

    result = runner.invoke(main_mod.app, ['undo', str(proj_dir)])

    assert result.exit_code == 0
    assert calls == ['UNDO', 'SAVE']
    assert 'Restored 1 parameters to their pre-fit values.' in result.stdout
    assert 'Cleared analysis.fit_results.' in result.stdout
    assert f'Saved project to {proj_dir}.' in result.stdout
