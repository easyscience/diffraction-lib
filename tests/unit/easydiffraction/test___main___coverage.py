# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from typer.testing import CliRunner

runner = CliRunner()


# ---------------------------------------------------------------------------
# _normalized_cli_args: project-first rewriting and pass-through branches
# ---------------------------------------------------------------------------


def test_normalized_cli_args_rewrites_project_first_command():
    """A leading project dir + project command is rewritten command-first."""
    import easydiffraction.__main__ as main_mod

    assert main_mod._normalized_cli_args(['my_proj', 'fit']) == ['fit', 'my_proj']
    assert main_mod._normalized_cli_args(['my_proj', 'display']) == ['display', 'my_proj']
    assert main_mod._normalized_cli_args(['my_proj', 'undo']) == ['undo', 'my_proj']


def test_normalized_cli_args_rewrite_preserves_trailing_args():
    """Trailing options after the project command survive the rewrite."""
    import easydiffraction.__main__ as main_mod

    assert main_mod._normalized_cli_args(['my_proj', 'fit', '--dry']) == [
        'fit',
        'my_proj',
        '--dry',
    ]


def test_normalized_cli_args_too_few_args_passthrough():
    """Fewer than two args are returned unchanged."""
    import easydiffraction.__main__ as main_mod

    assert main_mod._normalized_cli_args([]) == []
    assert main_mod._normalized_cli_args(['fit']) == ['fit']


def test_normalized_cli_args_option_first_passthrough():
    """A leading option (starts with '-') is never rewritten."""
    import easydiffraction.__main__ as main_mod

    assert main_mod._normalized_cli_args(['--version', 'fit']) == ['--version', 'fit']


def test_normalized_cli_args_global_command_first_passthrough():
    """A leading global command is never treated as a project dir."""
    import easydiffraction.__main__ as main_mod

    assert main_mod._normalized_cli_args(['fit', 'my_proj']) == ['fit', 'my_proj']
    assert main_mod._normalized_cli_args(['list-data', 'extra']) == ['list-data', 'extra']


def test_normalized_cli_args_second_arg_not_project_command_passthrough():
    """A non-project second arg leaves the project-first dir untouched."""
    import easydiffraction.__main__ as main_mod

    assert main_mod._normalized_cli_args(['my_proj', 'list-data']) == ['my_proj', 'list-data']


# ---------------------------------------------------------------------------
# Small helper accessors (_project_fit_mode, _project_result_kind, _project_name)
# ---------------------------------------------------------------------------


def test_project_fit_mode_resolves_type():
    """The fitting-mode type is read off analysis.fitting_mode."""
    import easydiffraction.__main__ as main_mod

    class FitMode:
        type = 'joint'

    class Analysis:
        fitting_mode = FitMode()

    class Project:
        analysis = Analysis()

    assert main_mod._project_fit_mode(Project()) == 'joint'


def test_project_fit_mode_missing_returns_none():
    """A missing fitting_mode yields None rather than raising."""
    import easydiffraction.__main__ as main_mod

    class Analysis:
        pass

    class Project:
        analysis = Analysis()

    assert main_mod._project_fit_mode(Project()) is None


def test_project_result_kind_resolves_value():
    """The result kind value is read off analysis.fit_result.result_kind."""
    import easydiffraction.__main__ as main_mod

    class ResultKind:
        value = 'bayesian'

    class FitResult:
        result_kind = ResultKind()

    class Analysis:
        fit_result = FitResult()

    class Project:
        analysis = Analysis()

    assert main_mod._project_result_kind(Project()) == 'bayesian'


def test_project_result_kind_missing_returns_none():
    """A missing fit_result yields None rather than raising."""
    import easydiffraction.__main__ as main_mod

    class Analysis:
        pass

    class Project:
        analysis = Analysis()

    assert main_mod._project_result_kind(Project()) is None


def test_project_name_prefers_name_attribute():
    """_project_name returns the project name when present."""
    import easydiffraction.__main__ as main_mod

    class Project:
        name = 'real_name'

    assert main_mod._project_name(Project(), 'fallback') == 'real_name'


def test_project_name_uses_fallback_when_name_empty_or_missing():
    """_project_name falls back when the name is empty or absent."""
    import easydiffraction.__main__ as main_mod

    class NoName:
        name = None

    class Empty:
        name = ''

    class Missing:
        pass

    assert main_mod._project_name(NoName(), 'fallback') == 'fallback'
    assert main_mod._project_name(Empty(), 'fallback') == 'fallback'
    assert main_mod._project_name(Missing(), 'fallback') == 'fallback'


# ---------------------------------------------------------------------------
# run_cli: argv default and explicit-args paths
# ---------------------------------------------------------------------------


def test_run_cli_uses_explicit_args(monkeypatch):
    """run_cli forwards normalized explicit args to the Typer app."""
    import easydiffraction.__main__ as main_mod

    seen = {}
    monkeypatch.setattr(main_mod, 'app', lambda args: seen.setdefault('args', args))

    main_mod.run_cli(['my_proj', 'fit', '--dry'])

    assert seen['args'] == ['fit', 'my_proj', '--dry']


def test_run_cli_defaults_to_sys_argv(monkeypatch):
    """run_cli reads sys.argv[1:] when no args are passed."""
    import sys

    import easydiffraction.__main__ as main_mod

    seen = {}
    monkeypatch.setattr(main_mod, 'app', lambda args: seen.setdefault('args', args))
    monkeypatch.setattr(sys, 'argv', ['easydiffraction', 'list-data'])

    main_mod.run_cli()

    assert seen['args'] == ['list-data']


# ---------------------------------------------------------------------------
# main callback: no subcommand prints help and exits zero
# ---------------------------------------------------------------------------


def test_cli_no_subcommand_enters_help_branch():
    """No subcommand reaches the help branch of the main callback.

    The callback calls ``app.get_help(ctx)`` on the Typer instance,
    which currently raises ``AttributeError`` (Typer has no
    ``get_help``); the test pins the observed behaviour so the branch
    on lines 162-164 is exercised. Source is intentionally left
    untouched.
    """
    import easydiffraction.__main__ as main_mod

    result = runner.invoke(main_mod.app, [])

    assert isinstance(result.exception, AttributeError)
    assert 'get_help' in str(result.exception)


# ---------------------------------------------------------------------------
# display command: drives _display_project_outputs across its three branches
# ---------------------------------------------------------------------------


def _make_recording_display(calls):
    class _Fit:
        @staticmethod
        def results():
            calls.append('RESULTS')

        @staticmethod
        def correlations():
            calls.append('CORR')

        @staticmethod
        def series():
            calls.append('SERIES')

    class _Posterior:
        @staticmethod
        def pairs():
            calls.append('PAIRS')

        @staticmethod
        def distribution():
            calls.append('DIST')

        @staticmethod
        def predictive(expt_name):
            calls.append(f'PRED_{expt_name}')

    class _Display:
        fit = _Fit()
        posterior = _Posterior()

        @staticmethod
        def pattern(expt_name):
            calls.append(f'PATTERN_{expt_name}')

    return _Display()


def test_display_command_default_branch(monkeypatch):
    """Non-sequential, non-bayesian display shows results, corr, patterns."""
    import easydiffraction.__main__ as main_mod

    calls = []

    class Experiment:
        name = 'exp1'

    class Analysis:
        pass  # no fitting_mode, no fit_result -> default branch

    class Project:
        analysis = Analysis()
        experiments = [Experiment()]
        display = _make_recording_display(calls)

    monkeypatch.setattr(main_mod, '_load_project', lambda project_dir: Project())

    result = runner.invoke(main_mod.app, ['display', 'whatever'])

    assert result.exit_code == 0
    assert calls == ['RESULTS', 'CORR', 'PATTERN_exp1']


def test_display_command_sequential_branch(monkeypatch):
    """Sequential mode renders the fit series then patterns and returns."""
    import easydiffraction.__main__ as main_mod

    calls = []

    class FitMode:
        type = 'sequential'

    class Analysis:
        fitting_mode = FitMode()

    class Experiment:
        name = 'expA'

    class Project:
        analysis = Analysis()
        experiments = [Experiment()]
        display = _make_recording_display(calls)

    monkeypatch.setattr(main_mod, '_load_project', lambda project_dir: Project())

    result = runner.invoke(main_mod.app, ['display', 'whatever'])

    assert result.exit_code == 0
    assert calls == ['SERIES', 'PATTERN_expA']


def test_display_command_bayesian_branch_plotly(monkeypatch):
    """Bayesian results with the plotly engine render pairs + posterior."""
    import easydiffraction.__main__ as main_mod

    calls = []

    class ResultKind:
        value = 'bayesian'

    class FitResult:
        result_kind = ResultKind()

    class Analysis:
        fit_result = FitResult()  # no fitting_mode -> not sequential

    class Experiment:
        name = 'expB'

    class Plotter:
        engine = 'plotly'

    class RenderingPlot:
        plotter = Plotter()

    class Project:
        analysis = Analysis()
        experiments = [Experiment()]
        rendering_plot = RenderingPlot()
        display = _make_recording_display(calls)

    monkeypatch.setattr(main_mod, '_load_project', lambda project_dir: Project())

    result = runner.invoke(main_mod.app, ['display', 'whatever'])

    assert result.exit_code == 0
    assert calls == ['RESULTS', 'CORR', 'PAIRS', 'DIST', 'PRED_expB', 'PATTERN_expB']


def test_display_command_bayesian_branch_non_plotly_skips_pairs(monkeypatch):
    """A non-plotly engine skips the pairs plot but keeps the rest."""
    import easydiffraction.__main__ as main_mod

    calls = []

    class ResultKind:
        value = 'bayesian'

    class FitResult:
        result_kind = ResultKind()

    class Analysis:
        fit_result = FitResult()

    class Experiment:
        name = 'expC'

    class Plotter:
        engine = 'matplotlib'

    class RenderingPlot:
        plotter = Plotter()

    class Project:
        analysis = Analysis()
        experiments = [Experiment()]
        rendering_plot = RenderingPlot()
        display = _make_recording_display(calls)

    monkeypatch.setattr(main_mod, '_load_project', lambda project_dir: Project())

    result = runner.invoke(main_mod.app, ['display', 'whatever'])

    assert result.exit_code == 0
    assert 'PAIRS' not in calls
    assert calls == ['RESULTS', 'CORR', 'DIST', 'PRED_expC', 'PATTERN_expC']


# ---------------------------------------------------------------------------
# _display_undo_summary: remaining flag combinations
# ---------------------------------------------------------------------------


def test_undo_dry_without_cleared_flags_skips_optional_lines(monkeypatch):
    """A dry undo with no cleared artifacts omits the optional summary lines."""
    import easydiffraction.__main__ as main_mod
    from easydiffraction.analysis import UndoFitOutcome

    calls = []

    class FakeAnalysis:
        @staticmethod
        def undo_fit():
            return UndoFitOutcome(
                restored_parameter_names=('a',),
                cleared_fit_result=False,
                cleared_sidecar=False,
                was_no_op=False,
            )

    class FakeProject:
        name = 'proj_x'
        analysis = FakeAnalysis()

        @staticmethod
        def save():
            calls.append('SAVE')

    monkeypatch.setattr(main_mod, '_load_project', lambda project_dir: FakeProject())

    result = runner.invoke(main_mod.app, ['undo', '--dry', 'whatever'])

    assert result.exit_code == 0
    assert calls == []  # dry run must not save
    assert '1 parameters would be restored to pre-fit values' in result.stdout
    assert 'analysis.fit_results would be cleared' not in result.stdout
    assert 'Bayesian sidecar) would be cleared' not in result.stdout


def test_undo_real_without_cleared_flags_saves_only(monkeypatch):
    """A real undo with no cleared artifacts still restores and saves."""
    import easydiffraction.__main__ as main_mod
    from easydiffraction.analysis import UndoFitOutcome

    calls = []

    class FakeAnalysis:
        @staticmethod
        def undo_fit():
            return UndoFitOutcome(
                restored_parameter_names=('a', 'b', 'c'),
                cleared_fit_result=False,
                cleared_sidecar=False,
                was_no_op=False,
            )

    class FakeProject:
        name = 'proj_y'
        analysis = FakeAnalysis()

        @staticmethod
        def save():
            calls.append('SAVE')

    monkeypatch.setattr(main_mod, '_load_project', lambda project_dir: FakeProject())

    result = runner.invoke(main_mod.app, ['undo', 'whatever'])

    assert result.exit_code == 0
    assert calls == ['SAVE']
    assert 'Restored 3 parameters to their pre-fit values.' in result.stdout
    assert 'Cleared analysis.fit_results.' not in result.stdout
    assert 'Cleared analysis/mcmc.h5 (Bayesian sidecar).' not in result.stdout


def test_undo_real_with_sidecar_cleared_echoes_sidecar_line(monkeypatch):
    """A real undo that clears the sidecar echoes the sidecar summary line."""
    import easydiffraction.__main__ as main_mod
    from easydiffraction.analysis import UndoFitOutcome

    class FakeAnalysis:
        @staticmethod
        def undo_fit():
            return UndoFitOutcome(
                restored_parameter_names=('a',),
                cleared_fit_result=False,
                cleared_sidecar=True,
                was_no_op=False,
            )

    class FakeProject:
        name = 'proj_z'
        analysis = FakeAnalysis()

        @staticmethod
        def save():
            pass

    monkeypatch.setattr(main_mod, '_load_project', lambda project_dir: FakeProject())

    result = runner.invoke(main_mod.app, ['undo', 'whatever'])

    assert result.exit_code == 0
    assert 'Cleared analysis.fit_results.' not in result.stdout
    assert 'Cleared analysis/mcmc.h5 (Bayesian sidecar).' in result.stdout


def test_undo_falls_back_to_project_dir_when_name_missing(monkeypatch, tmp_path):
    """When the project has no name, the project dir is used in messages."""
    import easydiffraction.__main__ as main_mod
    from easydiffraction.analysis import UndoFitOutcome

    class FakeAnalysis:
        @staticmethod
        def undo_fit():
            return UndoFitOutcome(
                restored_parameter_names=(),
                cleared_fit_result=False,
                cleared_sidecar=False,
                was_no_op=True,
            )

    calls = []

    class FakeProject:
        name = None
        analysis = FakeAnalysis()

        @staticmethod
        def save():
            calls.append('SAVE')

    proj_dir = tmp_path / 'unnamed_proj'
    monkeypatch.setattr(main_mod, '_load_project', lambda project_dir: FakeProject())

    result = runner.invoke(main_mod.app, ['undo', str(proj_dir)])

    assert result.exit_code == 0
    assert calls == []  # no-op must not save
    assert f"No fit to undo for '{proj_dir}'. Project state is unchanged." in result.stdout
