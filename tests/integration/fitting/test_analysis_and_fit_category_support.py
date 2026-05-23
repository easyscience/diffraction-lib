# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import re

ANSI_ESCAPE_RE = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')


def _unstyled_output(text: str) -> str:
    return ANSI_ESCAPE_RE.sub('', text)


def _make_project():
    class ExpCol:
        def __init__(self) -> None:
            self._names: list[str] = []

        @property
        def names(self):
            return self._names

        @property
        def parameters(self):
            return []

        @property
        def fittable_parameters(self):
            return []

        @property
        def free_parameters(self):
            return []

    class Project:
        experiments = ExpCol()
        structures = ExpCol()
        _varname = 'proj'
        verbosity = 'full'

    return Project()


def _make_project_with_names(names: list[str]):
    class ExpCol:
        def __init__(self, names):
            self._names = names

        def __len__(self):
            return len(self._names)

        @property
        def names(self):
            return self._names

        @property
        def parameters(self):
            return []

        @property
        def fittable_parameters(self):
            return []

        @property
        def free_parameters(self):
            return []

    class Project:
        experiments = ExpCol(names)
        structures = ExpCol([])
        _varname = 'proj'
        verbosity = 'full'

    return Project()


def test_fit_mode_enum_members_default_and_descriptions():
    from easydiffraction.analysis.enums import FitModeEnum

    assert FitModeEnum.SINGLE == 'single'
    assert FitModeEnum.JOINT == 'joint'
    assert FitModeEnum.SEQUENTIAL == 'sequential'
    assert FitModeEnum.default() is FitModeEnum.SINGLE
    assert all(member.description() for member in FitModeEnum)


def test_show_supported_fitting_mode_types_for_single_and_multiple_experiments(capsys):
    from easydiffraction.analysis.analysis import Analysis

    single = Analysis(project=_make_project_with_names(['e1']))
    single.show_supported_fitting_mode_types()
    out_single = capsys.readouterr().out
    assert 'Fitting mode types' in out_single
    assert 'single' in out_single
    assert 'joint' in out_single

    multi = Analysis(project=_make_project_with_names(['e1', 'e2']))
    multi.show_supported_fitting_mode_types()
    out_multi = capsys.readouterr().out
    assert 'joint' in out_multi
    assert 'sequential' in out_multi


def test_show_supported_minimizer_types_prints(capsys):
    from easydiffraction.analysis.analysis import Analysis

    analysis = Analysis(project=_make_project_with_names([]))
    analysis.show_supported_minimizer_types()
    out = capsys.readouterr().out
    assert 'Minimizer types' in out
    assert 'lmfit (leastsq)' in out


def test_analysis_help_and_mode_switching(capsys):
    from easydiffraction.analysis.analysis import Analysis

    analysis = Analysis(project=_make_project_with_names(['e1', 'e2']))
    assert analysis.fitting_mode_type == 'single'
    analysis.fitting_mode_type = 'joint'
    assert analysis.fitting_mode_type == 'joint'
    assert len(analysis.joint_fit) == 0

    analysis.help()
    out = _unstyled_output(capsys.readouterr().out)
    assert "Help for 'Analysis'" in out
    assert 'fitting' in out
    assert 'display' in out
    assert 'Properties' in out
    assert 'Methods' in out
    assert 'fit()' in out


def test_display_fit_results_warns_when_no_results(capsys):
    from easydiffraction.analysis.analysis import Analysis

    analysis = Analysis(project=_make_project_with_names([]))
    analysis.display.fit_results()
    out = capsys.readouterr().out
    assert 'No fit results available' in out


def test_display_fit_results_calls_process_fit_results(monkeypatch):
    from easydiffraction.analysis.analysis import Analysis

    process_called = {'called': False, 'args': None}

    def fake_process_fit_results(structures, experiments):
        process_called['called'] = True
        process_called['args'] = (structures, experiments)

    class Project:
        structures = object()
        _varname = 'proj'
        verbosity = 'full'

        class Experiments:
            names: list[str] = []

            @staticmethod
            def values():
                return []

            @property
            def parameters(self):
                return []

            @property
            def fittable_parameters(self):
                return []

            @property
            def free_parameters(self):
                return []

        experiments = Experiments()

    analysis = Analysis(project=Project())
    analysis.fit_results = object()
    monkeypatch.setattr(analysis.fitter, '_process_fit_results', fake_process_fit_results)

    analysis.display.fit_results()

    assert process_called['called'] is True


def test_analysis_display_as_cif_and_constraints(monkeypatch, capsys):
    import easydiffraction.analysis.analysis as analysis_mod
    import easydiffraction.analysis.categories.constraints.default as constraints_mod
    from easydiffraction.analysis.analysis import Analysis

    analysis = Analysis(project=_make_project())
    rendered: dict[str, str] = {}

    monkeypatch.setattr(analysis_mod, 'render_cif', lambda text: rendered.setdefault('text', text))
    analysis.display.as_cif()
    assert 'text' in rendered

    analysis.display.constraints()
    assert 'No constraints' in capsys.readouterr().out

    class FakeId:
        value = 'constraint_1'

    class FakeExpr:
        value = 'x = y + 1'

    class FakeConstraint:
        id = FakeId()
        expression = FakeExpr()

    analysis.constraints._items = [FakeConstraint()]
    captured: dict[str, object] = {}
    monkeypatch.setattr(constraints_mod, 'render_table', lambda **kwargs: captured.update(kwargs))
    analysis.display.constraints()
    out = capsys.readouterr().out
    assert 'User defined constraints' in out
    assert captured['columns_headers'] == ['id', 'expression']
    assert captured['columns_data'][0] == ['constraint_1', 'x = y + 1']


def test_discover_helpers_and_snapshot_params():
    from easydiffraction.analysis.analysis import Analysis
    from easydiffraction.analysis.analysis import _discover_method_rows
    from easydiffraction.analysis.analysis import _discover_property_rows

    class Demo:
        @property
        def alpha(self):
            """Alpha property."""
            return 1

        @property
        def beta(self):
            """Beta property."""
            return 2

        @beta.setter
        def beta(self, value):
            return None

        def do_thing(self):
            """Do a thing."""

        def _private(self):
            return None

    property_rows = _discover_property_rows(Demo)
    method_rows = _discover_method_rows(Demo)

    assert len(property_rows) == 2
    assert 'alpha' in [row[1] for row in property_rows]
    assert next(row for row in property_rows if row[1] == 'beta')[2] == '✓'
    assert 'do_thing()' in [row[1] for row in method_rows]
    assert '_private()' not in [row[1] for row in method_rows]

    analysis = Analysis(project=_make_project())

    class FakeParam:
        unique_name = 'p1'
        value = 1.23
        uncertainty = 0.01
        units = 'A'

    class FakeResults:
        parameters = [FakeParam()]

    analysis._snapshot_params('expt1', FakeResults())
    assert analysis._parameter_snapshots['expt1']['p1']['value'] == 1.23
    assert analysis._parameter_snapshots['expt1']['p1']['uncertainty'] == 0.01
