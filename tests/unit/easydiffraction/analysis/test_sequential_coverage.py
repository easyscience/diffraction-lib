# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Supplementary coverage tests for sequential fitting orchestration.

These tests exercise the worker pipeline, template construction,
precondition checks, recovery setup, worker-count resolution, the
process-pool context plumbing, and the sequential run loop without ever
invoking a real calculation engine, sampler, or minimizer. Every
boundary (``Project``, ``Fitter``, ``Parameter``, ``NumericDescriptor``)
is replaced with a lightweight fake injected via monkeypatching.
"""

from __future__ import annotations

import contextlib
import csv
import sys
from types import SimpleNamespace

import pytest

import easydiffraction.analysis.sequential as sequential_mod
from easydiffraction.analysis.sequential import SequentialFitExtractRule
from easydiffraction.analysis.sequential import SequentialFitTemplate
from easydiffraction.analysis.sequential import _apply_constraints
from easydiffraction.analysis.sequential import _apply_param_overrides
from easydiffraction.analysis.sequential import _build_template
from easydiffraction.analysis.sequential import _check_seq_preconditions
from easydiffraction.analysis.sequential import _collect_results
from easydiffraction.analysis.sequential import _create_pool_context
from easydiffraction.analysis.sequential import _extract_diffrn_values
from easydiffraction.analysis.sequential import _find_last_successful
from easydiffraction.analysis.sequential import _fit_worker
from easydiffraction.analysis.sequential import _format_progress_percent
from easydiffraction.analysis.sequential import _prepare_sequential_run
from easydiffraction.analysis.sequential import _resolve_workers
from easydiffraction.analysis.sequential import _restore_main_state
from easydiffraction.analysis.sequential import _run_fit_loop
from easydiffraction.analysis.sequential import _set_free_params
from easydiffraction.analysis.sequential import _setup_csv_and_recovery
from easydiffraction.analysis.sequential import _summarize_chunk_results
from easydiffraction.utils.enums import VerbosityEnum

# ------------------------------------------------------------------
#  Fakes for the Parameter / descriptor boundary
# ------------------------------------------------------------------


class _FakeParameter:
    """Stand-in for ``core.variable.Parameter`` used in isinstance checks."""

    def __init__(
        self,
        unique_name,
        value=0.0,
        *,
        free=False,
        user_constrained=False,
        uncertainty=0.0,
    ):
        self.unique_name = unique_name
        self.value = value
        self.free = free
        self.user_constrained = user_constrained
        self.uncertainty = uncertainty


class _FakeNumericDescriptor:
    """Stand-in for ``core.variable.NumericDescriptor`` (diffrn fields)."""

    def __init__(self, value=0.0):
        self.value = value


def _patch_variable_types(monkeypatch):
    """Make sequential's lazy ``Parameter``/``NumericDescriptor`` our fakes."""
    monkeypatch.setattr(
        'easydiffraction.core.variable.Parameter',
        _FakeParameter,
        raising=True,
    )
    monkeypatch.setattr(
        'easydiffraction.core.variable.NumericDescriptor',
        _FakeNumericDescriptor,
        raising=True,
    )


def _minimal_template(**overrides):
    base = {
        'structure_cifs': ['struct'],
        'experiment_cif': 'expt',
        'initial_params': {},
        'free_parameter_unique_names': ['cell.a'],
        'alias_defs': [],
        'constraint_defs': [],
        'constraints_enabled': False,
        'minimizer_tag': 'lmfit',
        'calculator_tag': 'cryspy',
        'diffrn_extract_rules': [],
        'diffrn_field_names': [],
    }
    base.update(overrides)
    return SequentialFitTemplate(**base)


# ------------------------------------------------------------------
#  _apply_param_overrides
# ------------------------------------------------------------------


class TestApplyParamOverrides:
    def test_sets_values_by_unique_name_and_ignores_unknown(self):
        a = _FakeParameter('cell.a', value=1.0)
        b = _FakeParameter('cell.b', value=2.0)
        project = SimpleNamespace(
            structures=SimpleNamespace(parameters=[a]),
            experiments=SimpleNamespace(parameters=[b]),
        )

        _apply_param_overrides(
            project,
            {'cell.a': 9.0, 'cell.b': 8.0, 'not.present': 7.0},
        )

        assert a.value == pytest.approx(9.0)
        assert b.value == pytest.approx(8.0)

    def test_skips_objects_without_unique_name(self):
        named = _FakeParameter('cell.a', value=1.0)
        anonymous = SimpleNamespace(value=5.0)  # no unique_name attribute
        project = SimpleNamespace(
            structures=SimpleNamespace(parameters=[named, anonymous]),
            experiments=SimpleNamespace(parameters=[]),
        )

        _apply_param_overrides(project, {'cell.a': 3.0})

        assert named.value == pytest.approx(3.0)
        assert anonymous.value == pytest.approx(5.0)


# ------------------------------------------------------------------
#  _set_free_params
# ------------------------------------------------------------------


class TestSetFreeParams:
    def test_marks_only_named_params_free(self, monkeypatch):
        _patch_variable_types(monkeypatch)
        a = _FakeParameter('cell.a', free=False)
        b = _FakeParameter('cell.b', free=True)
        project = SimpleNamespace(
            structures=SimpleNamespace(parameters=[a]),
            experiments=SimpleNamespace(parameters=[b]),
        )

        _set_free_params(project, ['cell.a'])

        assert a.free is True
        assert b.free is False

    def test_ignores_non_parameter_objects(self, monkeypatch):
        _patch_variable_types(monkeypatch)
        a = _FakeParameter('cell.a', free=False)
        not_a_param = SimpleNamespace(unique_name='cell.a', free=False)
        project = SimpleNamespace(
            structures=SimpleNamespace(parameters=[a, not_a_param]),
            experiments=SimpleNamespace(parameters=[]),
        )

        _set_free_params(project, ['cell.a'])

        assert a.free is True
        # The non-Parameter object stays untouched even though name matches.
        assert not_a_param.free is False


# ------------------------------------------------------------------
#  _apply_constraints
# ------------------------------------------------------------------


class TestApplyConstraints:
    def test_creates_aliases_and_constraints(self):
        a = _FakeParameter('cell.a')
        alias_calls = []
        constraint_calls = []
        analysis = SimpleNamespace(
            aliases=SimpleNamespace(
                create=lambda *, id, param: alias_calls.append((id, param)),
            ),
            constraints=SimpleNamespace(
                create=lambda *, expression: constraint_calls.append(expression),
            ),
        )
        project = SimpleNamespace(
            structures=SimpleNamespace(parameters=[a]),
            experiments=SimpleNamespace(parameters=[]),
            analysis=analysis,
        )

        _apply_constraints(
            project,
            [{'id': 'A', 'parameter_unique_name': 'cell.a'}],
            ['A = 2 * B'],
        )

        assert alias_calls == [('A', a)]
        assert constraint_calls == ['A = 2 * B']

    def test_skips_alias_for_missing_param(self):
        alias_calls = []
        analysis = SimpleNamespace(
            aliases=SimpleNamespace(
                create=lambda *, id, param: alias_calls.append((id, param)),
            ),
            constraints=SimpleNamespace(create=lambda *, expression: None),
        )
        project = SimpleNamespace(
            structures=SimpleNamespace(parameters=[]),
            experiments=SimpleNamespace(parameters=[]),
            analysis=analysis,
        )

        _apply_constraints(
            project,
            [{'id': 'A', 'parameter_unique_name': 'does.not.exist'}],
            [],
        )

        assert alias_calls == []


# ------------------------------------------------------------------
#  _extract_diffrn_values
# ------------------------------------------------------------------


def _rule(rule_id, field_name, pattern, *, required=False):
    return SequentialFitExtractRule(
        id=rule_id,
        field_name=field_name,
        pattern=pattern,
        required=required,
    )


class TestExtractDiffrnValues:
    def test_returns_empty_when_no_rules(self, tmp_path):
        data = tmp_path / 'scan.dat'
        data.write_text('temp 300\n')
        experiment = SimpleNamespace(diffrn=SimpleNamespace())

        result = _extract_diffrn_values(experiment, str(data), [])

        assert result == {}

    def test_extracts_and_updates_descriptor(self, tmp_path):
        data = tmp_path / 'scan.dat'
        data.write_text('header line\nTEMP = 305.5 K\nmore\n')
        temp_desc = _FakeNumericDescriptor()
        experiment = SimpleNamespace(diffrn=SimpleNamespace(ambient_temperature=temp_desc))
        rules = [_rule('temp', 'ambient_temperature', r'TEMP = (\d+\.\d+)', required=True)]

        result = _extract_diffrn_values(experiment, str(data), rules)

        assert result == {'diffrn.ambient_temperature': pytest.approx(305.5)}
        assert temp_desc.value == pytest.approx(305.5)

    def test_stops_after_all_rules_matched(self, tmp_path):
        # The second TEMP line must be ignored once the rule matches.
        data = tmp_path / 'scan.dat'
        data.write_text('TEMP = 100\nTEMP = 999\n')
        temp_desc = _FakeNumericDescriptor()
        experiment = SimpleNamespace(diffrn=SimpleNamespace(ambient_temperature=temp_desc))
        rules = [_rule('temp', 'ambient_temperature', r'TEMP = (\d+)')]

        result = _extract_diffrn_values(experiment, str(data), rules)

        assert result['diffrn.ambient_temperature'] == pytest.approx(100.0)

    def test_raises_on_non_numeric_capture(self, tmp_path):
        data = tmp_path / 'scan.dat'
        data.write_text('TEMP = hot\n')
        experiment = SimpleNamespace(
            diffrn=SimpleNamespace(ambient_temperature=_FakeNumericDescriptor())
        )
        rules = [_rule('temp', 'ambient_temperature', r'TEMP = (\w+)')]

        with pytest.raises(ValueError, match=r'non-numeric value'):
            _extract_diffrn_values(experiment, str(data), rules)

    def test_raises_when_required_rule_not_matched(self, tmp_path):
        data = tmp_path / 'scan.dat'
        data.write_text('nothing relevant here\n')
        experiment = SimpleNamespace(
            diffrn=SimpleNamespace(ambient_temperature=_FakeNumericDescriptor())
        )
        rules = [_rule('temp', 'ambient_temperature', r'TEMP = (\d+)', required=True)]

        with pytest.raises(ValueError, match=r'did not match'):
            _extract_diffrn_values(experiment, str(data), rules)

    def test_optional_rule_missing_is_silent(self, tmp_path):
        data = tmp_path / 'scan.dat'
        data.write_text('nothing relevant here\n')
        experiment = SimpleNamespace(
            diffrn=SimpleNamespace(ambient_temperature=_FakeNumericDescriptor())
        )
        rules = [_rule('temp', 'ambient_temperature', r'TEMP = (\d+)', required=False)]

        result = _extract_diffrn_values(experiment, str(data), rules)

        assert result == {}

    def test_two_rules_match_on_separate_lines(self, tmp_path):
        # Rule 'temp' matches line 1; on line 2 it is already matched and is
        # skipped while rule 'wave' matches.
        data = tmp_path / 'scan.dat'
        data.write_text('TEMP = 250\nWAVE = 1.54\nTEMP = 999\n')
        temp_desc = _FakeNumericDescriptor()
        wave_desc = _FakeNumericDescriptor()
        experiment = SimpleNamespace(
            diffrn=SimpleNamespace(
                ambient_temperature=temp_desc,
                wavelength=wave_desc,
            )
        )
        rules = [
            _rule('temp', 'ambient_temperature', r'TEMP = (\d+)'),
            _rule('wave', 'wavelength', r'WAVE = (\d+\.\d+)'),
        ]

        result = _extract_diffrn_values(experiment, str(data), rules)

        assert result == {
            'diffrn.ambient_temperature': pytest.approx(250.0),
            'diffrn.wavelength': pytest.approx(1.54),
        }
        # First match wins; the later TEMP line is ignored.
        assert temp_desc.value == pytest.approx(250.0)


# ------------------------------------------------------------------
#  _collect_results
# ------------------------------------------------------------------


class TestCollectResults:
    def _project(self, params, fit_results, *, best_iteration=None):
        tracker = SimpleNamespace(best_iteration=best_iteration)
        analysis = SimpleNamespace(
            fit_results=fit_results,
            fitter=SimpleNamespace(minimizer=SimpleNamespace(tracker=tracker)),
        )
        return SimpleNamespace(
            structures=SimpleNamespace(parameters=params),
            experiments=SimpleNamespace(parameters=[]),
            analysis=analysis,
        )

    def test_collects_metrics_and_free_param_values(self, monkeypatch):
        _patch_variable_types(monkeypatch)
        free = _FakeParameter('cell.a', value=4.2, uncertainty=0.05)
        fixed = _FakeParameter('cell.b', value=9.9, uncertainty=0.0)
        fit_results = SimpleNamespace(
            success=True,
            reduced_chi_square=1.23,
            iterations=17,
        )
        project = self._project([free, fixed], fit_results)
        template = _minimal_template(free_parameter_unique_names=['cell.a'])

        result = _collect_results(project, template)

        assert result['fit_result.success'] is True
        assert result['fit_result.reduced_chi_square'] == pytest.approx(1.23)
        assert result['fit_result.iterations'] == 17
        assert result['cell.a'] == pytest.approx(4.2)
        assert result['cell.a.uncertainty'] == pytest.approx(0.05)
        assert result['params'] == {'cell.a': pytest.approx(4.2)}
        # Non-free parameter must not appear.
        assert 'cell.b' not in result

    def test_falls_back_to_best_iteration_when_iterations_zero(self, monkeypatch):
        _patch_variable_types(monkeypatch)
        fit_results = SimpleNamespace(success=True, reduced_chi_square=2.0, iterations=0)
        project = self._project([], fit_results, best_iteration=42)
        template = _minimal_template(free_parameter_unique_names=[])

        result = _collect_results(project, template)

        assert result['fit_result.iterations'] == 42

    def test_handles_missing_fit_results(self, monkeypatch):
        _patch_variable_types(monkeypatch)
        project = self._project([], None, best_iteration=7)
        template = _minimal_template(free_parameter_unique_names=[])

        result = _collect_results(project, template)

        assert result['fit_result.success'] is False
        assert result['fit_result.reduced_chi_square'] is None
        assert result['fit_result.iterations'] == 7
        assert result['params'] == {}


# ------------------------------------------------------------------
#  _fit_worker (success and error paths)
# ------------------------------------------------------------------


class TestFitWorker:
    def test_success_path_builds_project_and_collects(self, monkeypatch):
        template = _minimal_template(
            free_parameter_unique_names=['cell.a'],
            constraints_enabled=True,
            alias_defs=[{'id': 'A', 'parameter_unique_name': 'cell.a'}],
            constraint_defs=['A = 1'],
        )
        events = []

        # Fake experiment with the methods the worker calls.
        expt = SimpleNamespace(
            _load_ascii_data_to_experiment=lambda path: events.append(('load', path)),
            _swap_calculator=lambda tag, *, announce: events.append(('swap', tag, announce)),
        )

        verbosity = SimpleNamespace(fit=SimpleNamespace(value='full'))

        analysis = SimpleNamespace(fitter=None)
        project = SimpleNamespace(
            structures=SimpleNamespace(
                add_from_cif_str=lambda cif: events.append(('struct_cif', cif)),
                parameters=[],
            ),
            experiments=SimpleNamespace(
                add_from_cif_str=lambda cif: events.append(('expt_cif', cif)),
                parameters=[],
                values=lambda: iter([expt]),
            ),
            analysis=analysis,
        )
        # project.verbosity.fit is a writable attribute on a SimpleNamespace
        project.verbosity = verbosity
        # Track verbosity restore: convert .fit assignment to a property via
        # a small holder. SimpleNamespace assignment works directly here.

        class FakeProject:
            _loading = False

            def __new__(cls, *, name):
                events.append(('project_init', name))
                return project

        def fake_fit():
            # During the fit the worker sets verbosity to the literal
            # 'silent' string; record that the silencing happened.
            events.append(('fit', project.verbosity.fit))

        analysis.fit = fake_fit

        monkeypatch.setattr(
            'easydiffraction.project.project.Project',
            FakeProject,
            raising=True,
        )
        monkeypatch.setattr(
            'easydiffraction.analysis.fitting.Fitter',
            lambda tag: events.append(('fitter', tag)) or SimpleNamespace(tag=tag),
            raising=True,
        )
        monkeypatch.setattr(
            sequential_mod,
            '_apply_param_overrides',
            lambda proj, overrides: events.append(('overrides', overrides)),
        )
        monkeypatch.setattr(
            sequential_mod,
            '_set_free_params',
            lambda proj, names: events.append(('free', names)),
        )
        monkeypatch.setattr(
            sequential_mod,
            '_apply_constraints',
            lambda proj, aliases, constraints: events.append((
                'constraints',
                aliases,
                constraints,
            )),
        )
        monkeypatch.setattr(
            sequential_mod,
            '_extract_diffrn_values',
            lambda experiment, path, rules: {'diffrn.temp': 300.0},
        )
        monkeypatch.setattr(
            sequential_mod,
            '_collect_results',
            lambda proj, tmpl: {'fit_result.success': True, 'cell.a': 4.0},
        )

        result = _fit_worker(template, '/data/scan_001.dat')

        assert result['file_path'] == '/data/scan_001.dat'
        assert result['diffrn.temp'] == pytest.approx(300.0)
        assert result['fit_result.success'] is True
        assert result['cell.a'] == pytest.approx(4.0)
        # Calculator swap and Fitter assignment happened.
        assert ('swap', 'cryspy', False) in events
        assert ('fitter', 'lmfit') in events
        # Constraints applied because enabled + alias_defs present.
        assert any(e[0] == 'constraints' for e in events)
        # During the fit the verbosity was forced to 'silent'.
        assert ('fit', 'silent') in events
        # Verbosity restored to the original value after the fit.
        assert project.verbosity.fit == 'full'

    def test_error_path_returns_failure_payload(self, monkeypatch):
        template = _minimal_template()

        def boom(template_arg, data_path):
            message = 'engine exploded'
            raise RuntimeError(message)

        monkeypatch.setattr(sequential_mod, '_fit_worker_success', boom)

        result = _fit_worker(template, '/data/scan_002.dat')

        assert result == {
            'file_path': '/data/scan_002.dat',
            'success': False,
            'reduced_chi_square': None,
            'iterations': 0,
            'error': 'engine exploded',
        }

    def test_skips_constraints_when_disabled(self, monkeypatch):
        template = _minimal_template(
            constraints_enabled=False,
            alias_defs=[{'id': 'A', 'parameter_unique_name': 'cell.a'}],
        )
        events = []
        expt = SimpleNamespace(
            _load_ascii_data_to_experiment=lambda path: None,
            _swap_calculator=lambda tag, *, announce: None,
        )
        verbosity = SimpleNamespace(fit=SimpleNamespace(value='silent'))
        analysis = SimpleNamespace(fitter=None, fit=lambda: None)
        project = SimpleNamespace(
            structures=SimpleNamespace(add_from_cif_str=lambda cif: None, parameters=[]),
            experiments=SimpleNamespace(
                add_from_cif_str=lambda cif: None,
                parameters=[],
                values=lambda: iter([expt]),
            ),
            analysis=analysis,
            verbosity=verbosity,
        )

        class FakeProject:
            _loading = False

            def __new__(cls, *, name):
                return project

        monkeypatch.setattr('easydiffraction.project.project.Project', FakeProject, raising=True)
        monkeypatch.setattr(
            'easydiffraction.analysis.fitting.Fitter',
            lambda tag: SimpleNamespace(tag=tag),
            raising=True,
        )
        monkeypatch.setattr(sequential_mod, '_apply_param_overrides', lambda *a: None)
        monkeypatch.setattr(sequential_mod, '_set_free_params', lambda *a: None)
        monkeypatch.setattr(
            sequential_mod,
            '_apply_constraints',
            lambda *a: events.append('constraints'),
        )
        monkeypatch.setattr(sequential_mod, '_extract_diffrn_values', lambda *a: {})
        monkeypatch.setattr(sequential_mod, '_collect_results', lambda *a: {})

        _fit_worker(template, '/data/scan.dat')

        assert 'constraints' not in events


# ------------------------------------------------------------------
#  _build_template
# ------------------------------------------------------------------


class TestBuildTemplate:
    def _project(
        self, *, params, aliases, constraints, extract_rules, diffrn, constraints_enabled=True
    ):
        structure = SimpleNamespace(as_cif='STRUCT_CIF')
        experiment = SimpleNamespace(
            as_cif='EXPT_CIF',
            diffrn=diffrn,
            calculator=SimpleNamespace(type='crysfml'),
        )
        analysis = SimpleNamespace(
            aliases=aliases,
            constraints=_IterableNamespace(constraints, enabled=constraints_enabled),
            sequential_fit_extract=extract_rules,
            minimizer=SimpleNamespace(type='bumps'),
        )
        return SimpleNamespace(
            structures=_IterableNamespace([structure], parameters=params),
            experiments=_IterableNamespace([experiment], parameters=[]),
            analysis=analysis,
        )

    def test_builds_snapshot_from_project(self, monkeypatch):
        _patch_variable_types(monkeypatch)
        free = _FakeParameter('cell.a', value=5.0, free=True, user_constrained=False)
        constrained = _FakeParameter('cell.b', value=6.0, free=True, user_constrained=True)
        fixed = _FakeParameter('cell.c', value=7.0, free=False)
        temp_desc = _FakeNumericDescriptor(300.0)

        alias = SimpleNamespace(
            id=SimpleNamespace(value='A'),
            parameter_unique_name=SimpleNamespace(value='cell.a'),
        )
        constraint = SimpleNamespace(expression=SimpleNamespace(value='A = 1'))
        extract_rule = SimpleNamespace(
            target=SimpleNamespace(value='diffrn.ambient_temperature'),
            id=SimpleNamespace(value='temp'),
            pattern=SimpleNamespace(value=r'T=(\d+)'),
            required=SimpleNamespace(value=True),
        )

        project = self._project(
            params=[free, constrained, fixed],
            aliases=[alias],
            constraints=[constraint],
            extract_rules=[extract_rule],
            diffrn=SimpleNamespace(ambient_temperature=temp_desc),
        )

        template = _build_template(project)

        assert template.structure_cifs == ['STRUCT_CIF']
        assert template.experiment_cif == 'EXPT_CIF'
        # Only the free, non-user-constrained parameter is collected.
        assert template.free_parameter_unique_names == ['cell.a']
        assert template.initial_params == {'cell.a': pytest.approx(5.0)}
        assert template.alias_defs == [{'id': 'A', 'parameter_unique_name': 'cell.a'}]
        assert template.constraint_defs == ['A = 1']
        assert template.constraints_enabled is True
        assert template.minimizer_tag == 'bumps'
        assert template.calculator_tag == 'crysfml'
        assert len(template.diffrn_extract_rules) == 1
        assert template.diffrn_extract_rules[0].field_name == 'ambient_temperature'
        assert template.diffrn_field_names == ['ambient_temperature']

    def test_minimizer_tag_defaults_to_lmfit(self, monkeypatch):
        _patch_variable_types(monkeypatch)
        free = _FakeParameter('cell.a', value=5.0, free=True)
        project = self._project(
            params=[free],
            aliases=[],
            constraints=[],
            extract_rules=[],
            diffrn=SimpleNamespace(),
        )
        project.analysis.minimizer = SimpleNamespace(type=None)

        template = _build_template(project)

        assert template.minimizer_tag == 'lmfit'

    def test_raises_for_non_numeric_extract_target(self, monkeypatch):
        _patch_variable_types(monkeypatch)
        free = _FakeParameter('cell.a', value=5.0, free=True)
        extract_rule = SimpleNamespace(
            target=SimpleNamespace(value='diffrn.not_numeric'),
            id=SimpleNamespace(value='x'),
            pattern=SimpleNamespace(value='(.*)'),
            required=SimpleNamespace(value=False),
        )
        # The descriptor is a plain object, not a NumericDescriptor.
        project = self._project(
            params=[free],
            aliases=[],
            constraints=[],
            extract_rules=[extract_rule],
            diffrn=SimpleNamespace(not_numeric=SimpleNamespace(value=1.0)),
        )

        with pytest.raises(TypeError, match=r'must reference an existing numeric'):
            _build_template(project)

    def test_duplicate_extract_field_appears_once(self, monkeypatch):
        _patch_variable_types(monkeypatch)
        free = _FakeParameter('cell.a', value=5.0, free=True)
        temp_desc = _FakeNumericDescriptor(300.0)
        rule_a = SimpleNamespace(
            target=SimpleNamespace(value='diffrn.ambient_temperature'),
            id=SimpleNamespace(value='temp_a'),
            pattern=SimpleNamespace(value=r'A=(\d+)'),
            required=SimpleNamespace(value=False),
        )
        rule_b = SimpleNamespace(
            target=SimpleNamespace(value='diffrn.ambient_temperature'),
            id=SimpleNamespace(value='temp_b'),
            pattern=SimpleNamespace(value=r'B=(\d+)'),
            required=SimpleNamespace(value=False),
        )
        project = self._project(
            params=[free],
            aliases=[],
            constraints=[],
            extract_rules=[rule_a, rule_b],
            diffrn=SimpleNamespace(ambient_temperature=temp_desc),
        )

        template = _build_template(project)

        # Both rules are kept, but the field name is recorded only once.
        assert len(template.diffrn_extract_rules) == 2
        assert template.diffrn_field_names == ['ambient_temperature']


class _IterableNamespace:
    """A namespace whose iteration yields a stored list of items."""

    def __init__(self, items, *, parameters=None, enabled=None):
        self._items = list(items)
        if parameters is not None:
            self.parameters = parameters
        if enabled is not None:
            self.enabled = enabled

    def __iter__(self):
        return iter(self._items)

    def values(self):
        return iter(self._items)


# ------------------------------------------------------------------
#  _summarize_chunk_results / _format_progress_percent edge cases
# ------------------------------------------------------------------


class TestSummarizeChunkResults:
    def test_all_successful(self):
        results = [
            {'fit_result.success': True, 'fit_result.reduced_chi_square': 2.0},
            {'fit_result.success': True, 'fit_result.reduced_chi_square': 4.0},
        ]
        chi2_str, status = _summarize_chunk_results(results)
        assert chi2_str == '3.00'
        assert status == '✅'

    def test_partial_success(self):
        results = [
            {'fit_result.success': True, 'fit_result.reduced_chi_square': 2.0},
            {'fit_result.success': False, 'fit_result.reduced_chi_square': None},
        ]
        chi2_str, status = _summarize_chunk_results(results)
        assert chi2_str == '2.00'
        assert status == '⚠️'

    def test_all_failed_shows_dash_and_cross(self):
        results = [
            {'fit_result.success': False, 'fit_result.reduced_chi_square': None},
        ]
        chi2_str, status = _summarize_chunk_results(results)
        assert chi2_str == '—'
        assert status == '❌'


class TestFormatProgressPercent:
    def test_zero_total_returns_zero(self):
        assert _format_progress_percent(0, 0) == '0.0%'

    def test_clamps_overflow(self):
        assert _format_progress_percent(10, 4) == '100.0%'

    def test_clamps_negative(self):
        assert _format_progress_percent(-3, 4) == '0.0%'


# ------------------------------------------------------------------
#  _check_seq_preconditions
# ------------------------------------------------------------------


def _precondition_project(
    *,
    n_structures=1,
    n_experiments=1,
    path='/proj',
    params=None,
):
    if params is None:
        params = [_FakeParameter('cell.a', free=True)]
    return SimpleNamespace(
        structures=[object()] * n_structures,
        experiments=[object()] * n_experiments,
        metadata=SimpleNamespace(path=path),
        parameters=params,
    )


class TestCheckSeqPreconditions:
    def test_passes_with_valid_project(self, monkeypatch):
        _patch_variable_types(monkeypatch)
        project = _precondition_project()
        # No exception means success.
        assert _check_seq_preconditions(project) is None

    def test_accepts_multiple_structures(self, monkeypatch):
        _patch_variable_types(monkeypatch)
        project = _precondition_project(n_structures=2)
        # Multiple structures are now supported; no exception means success.
        assert _check_seq_preconditions(project) is None

    def test_rejects_no_structures(self, monkeypatch):
        _patch_variable_types(monkeypatch)
        project = _precondition_project(n_structures=0)
        with pytest.raises(ValueError, match=r'at least 1 structure'):
            _check_seq_preconditions(project)

    def test_rejects_multiple_experiments(self, monkeypatch):
        _patch_variable_types(monkeypatch)
        project = _precondition_project(n_experiments=3)
        with pytest.raises(ValueError, match=r'exactly 1 experiment'):
            _check_seq_preconditions(project)

    def test_rejects_unsaved_project(self, monkeypatch):
        _patch_variable_types(monkeypatch)
        project = _precondition_project(path=None)
        with pytest.raises(ValueError, match=r'must be saved'):
            _check_seq_preconditions(project)

    def test_rejects_when_no_free_params(self, monkeypatch):
        _patch_variable_types(monkeypatch)
        project = _precondition_project(params=[_FakeParameter('cell.a', free=False)])
        with pytest.raises(ValueError, match=r'No free parameters'):
            _check_seq_preconditions(project)

    def test_user_constrained_params_do_not_count_as_free(self, monkeypatch):
        _patch_variable_types(monkeypatch)
        project = _precondition_project(
            params=[_FakeParameter('cell.a', free=True, user_constrained=True)],
        )
        with pytest.raises(ValueError, match=r'No free parameters'):
            _check_seq_preconditions(project)


# ------------------------------------------------------------------
#  _setup_csv_and_recovery
# ------------------------------------------------------------------


class TestSetupCsvAndRecovery:
    def test_fresh_run_writes_header(self, tmp_path, monkeypatch):
        project = SimpleNamespace(metadata=SimpleNamespace(path=tmp_path))
        template = _minimal_template(free_parameter_unique_names=['cell.a'])

        monkeypatch.setattr(
            sequential_mod,
            '_read_csv_for_recovery',
            lambda csv_path: (set(), None),
        )

        csv_path, header, already_fitted, returned_template = _setup_csv_and_recovery(
            project,
            template,
            VerbosityEnum.SHORT,
        )

        assert csv_path == tmp_path / 'analysis' / 'results.csv'
        assert csv_path.is_file()
        assert already_fitted == set()
        assert returned_template is template
        with csv_path.open() as f:
            first_row = next(csv.reader(f))
        assert first_row == header

    def test_resume_recovers_params_and_skips_header(self, tmp_path, monkeypatch):
        project = SimpleNamespace(metadata=SimpleNamespace(path=tmp_path))
        template = _minimal_template(
            free_parameter_unique_names=['cell.a'],
            initial_params={'cell.a': 1.0},
        )
        recovered = {'cell.a': 9.9}
        prints = []
        monkeypatch.setattr(
            sequential_mod,
            '_read_csv_for_recovery',
            lambda csv_path: ({'/data/a.dat', '/data/b.dat'}, recovered),
        )
        monkeypatch.setattr(
            sequential_mod,
            'console',
            SimpleNamespace(print=prints.append),
        )

        csv_path, _header, already_fitted, returned_template = _setup_csv_and_recovery(
            project,
            template,
            VerbosityEnum.SHORT,
        )

        assert len(already_fitted) == 2
        # initial_params replaced with recovered values.
        assert returned_template.initial_params == {'cell.a': 9.9}
        # No CSV header written on resume (file should not exist).
        assert not csv_path.is_file()
        assert any('Resuming from CSV' in msg for msg in prints)

    def test_resume_silent_does_not_print(self, tmp_path, monkeypatch):
        project = SimpleNamespace(metadata=SimpleNamespace(path=tmp_path))
        template = _minimal_template()
        prints = []
        monkeypatch.setattr(
            sequential_mod,
            '_read_csv_for_recovery',
            lambda csv_path: ({'/data/a.dat'}, None),
        )
        monkeypatch.setattr(
            sequential_mod,
            'console',
            SimpleNamespace(print=prints.append),
        )

        _setup_csv_and_recovery(project, template, VerbosityEnum.SILENT)

        assert prints == []


# ------------------------------------------------------------------
#  _resolve_workers
# ------------------------------------------------------------------


class TestResolveWorkers:
    def test_explicit_workers_and_chunk_size(self):
        assert _resolve_workers(4, 2) == (4, 2)

    def test_chunk_size_defaults_to_workers(self):
        assert _resolve_workers(3, None) == (3, 3)

    def test_auto_uses_cpu_count(self, monkeypatch):
        monkeypatch.setattr('os.cpu_count', lambda: 5)
        workers, chunk = _resolve_workers('auto', None)
        assert workers == 5
        assert chunk == 5

    def test_auto_falls_back_to_one_when_cpu_count_none(self, monkeypatch):
        monkeypatch.setattr('os.cpu_count', lambda: None)
        workers, _chunk = _resolve_workers('auto', None)
        assert workers == 1

    def test_rejects_zero_workers(self):
        with pytest.raises(ValueError, match=r'positive integer'):
            _resolve_workers(0, None)

    def test_rejects_non_int_non_auto(self):
        bad_value = 'lots'
        with pytest.raises(ValueError, match=r"or 'auto'"):
            _resolve_workers(bad_value, None)


# ------------------------------------------------------------------
#  _create_pool_context / _restore_main_state
# ------------------------------------------------------------------


class TestCreatePoolContext:
    def test_single_worker_uses_nullcontext(self):
        pool_cm, main_mod, file_bak, spec_bak = _create_pool_context(1)
        assert isinstance(pool_cm, contextlib.nullcontext)
        # Restoring with single worker leaves state unchanged.
        _restore_main_state(main_mod, file_bak, spec_bak)

    def test_multi_worker_clears_and_restores_main_state(self, monkeypatch):
        fake_main = SimpleNamespace(__file__='/x/main.py', __spec__=object())
        original_file = fake_main.__file__
        original_spec = fake_main.__spec__
        monkeypatch.setitem(sys.modules, '__main__', fake_main)

        created = {}

        class FakeExecutor:
            def __init__(self, *, max_workers, mp_context, max_tasks_per_child):
                created['max_workers'] = max_workers
                created['max_tasks_per_child'] = max_tasks_per_child

        monkeypatch.setattr(sequential_mod, 'ProcessPoolExecutor', FakeExecutor)
        monkeypatch.setattr(
            sequential_mod.mp,
            'get_context',
            lambda name: SimpleNamespace(name=name),
        )

        pool_cm, main_mod, file_bak, spec_bak = _create_pool_context(2)

        assert isinstance(pool_cm, FakeExecutor)
        assert created['max_workers'] == 2
        assert created['max_tasks_per_child'] == 100
        # __main__ state was cleared during pool creation.
        assert fake_main.__file__ is None
        assert fake_main.__spec__ is None

        _restore_main_state(main_mod, file_bak, spec_bak)
        assert fake_main.__file__ == original_file
        assert fake_main.__spec__ is original_spec

    def test_multi_worker_without_main_file_or_spec(self, monkeypatch):
        # __main__ exposes neither __file__ nor __spec__, so the clear /
        # restore guards short-circuit on the missing-attribute path.
        class BareMain:
            pass

        bare_main = BareMain()
        monkeypatch.setitem(sys.modules, '__main__', bare_main)

        class FakeExecutor:
            def __init__(self, *, max_workers, mp_context, max_tasks_per_child):
                del max_workers, mp_context, max_tasks_per_child

        monkeypatch.setattr(sequential_mod, 'ProcessPoolExecutor', FakeExecutor)
        monkeypatch.setattr(
            sequential_mod.mp,
            'get_context',
            lambda name: SimpleNamespace(name=name),
        )

        pool_cm, main_mod, file_bak, spec_bak = _create_pool_context(2)

        assert isinstance(pool_cm, FakeExecutor)
        assert file_bak is None
        assert spec_bak is None
        # No __file__/__spec__ were created on the bare main module.
        assert not hasattr(bare_main, '__file__')
        # Restoring is a no-op because the backups are None.
        _restore_main_state(main_mod, file_bak, spec_bak)
        assert not hasattr(bare_main, '__file__')


# ------------------------------------------------------------------
#  _report_chunk_progress (silent short-circuit)
# ------------------------------------------------------------------


class TestReportChunkProgressSilent:
    def test_silent_verbosity_is_noop(self):
        progress = sequential_mod.SequentialProgressContext(
            verbosity=VerbosityEnum.SILENT,
            state=None,
        )

        sequential_mod._report_chunk_progress(
            1,
            1,
            ['scan.dat'],
            [{'file_path': 'scan.dat', 'fit_result.success': True}],
            progress,
            sequential_mod._ChunkProgressMetrics(
                completed_files_before=0,
                total_files=1,
                elapsed_time=1.0,
            ),
        )

        # Nothing recorded; state stays None.
        assert progress.state is None
        assert progress.indicator is None


# ------------------------------------------------------------------
#  _find_last_successful
# ------------------------------------------------------------------


class TestFindLastSuccessful:
    def test_returns_last_successful_with_params(self):
        results = [
            {'fit_result.success': True, 'params': {'cell.a': 1.0}},
            {'fit_result.success': True, 'params': {'cell.a': 2.0}},
            {'fit_result.success': False, 'params': {}},
        ]
        last = _find_last_successful(results)
        assert last['params'] == {'cell.a': 2.0}

    def test_returns_none_when_none_successful(self):
        results = [
            {'fit_result.success': False, 'params': {}},
            {'fit_result.success': True, 'params': {}},  # no params -> skipped
        ]
        assert _find_last_successful(results) is None

    def test_empty_results_returns_none(self):
        assert _find_last_successful([]) is None


# ------------------------------------------------------------------
#  _run_fit_loop (sequential, no-executor path + param propagation)
# ------------------------------------------------------------------


class TestRunFitLoopSequential:
    def test_sequential_path_calls_worker_and_propagates_params(self, monkeypatch, tmp_path):
        template = _minimal_template(free_parameter_unique_names=['cell.a'])
        appended = []
        worker_templates = []

        def fake_worker(template_arg, path):
            worker_templates.append(template_arg.initial_params)
            return {
                'file_path': path,
                'fit_result.success': True,
                'fit_result.reduced_chi_square': 1.0,
                'fit_result.iterations': 3,
                'params': {'cell.a': float(len(path))},
            }

        monkeypatch.setattr(sequential_mod, '_fit_worker', fake_worker)
        monkeypatch.setattr(
            sequential_mod,
            '_append_to_csv',
            lambda csv_path, header, results: appended.append([r['file_path'] for r in results]),
        )
        monkeypatch.setattr(sequential_mod, '_report_chunk_progress', lambda *a: None)

        progress = sequential_mod.SequentialProgressContext(
            verbosity=VerbosityEnum.SILENT,
            state=None,
        )

        # nullcontext yields None -> executor is None -> sequential branch.
        _run_fit_loop(
            contextlib.nullcontext(),
            [['aa'], ['bbbb']],
            template,
            (tmp_path / 'results.csv', ['file_path']),
            progress,
        )

        assert appended == [['aa'], ['bbbb']]
        # First chunk worker saw the original (empty) initial_params; second
        # chunk worker saw the propagated params from chunk 1.
        assert worker_templates[0] == {}
        assert worker_templates[1] == {'cell.a': pytest.approx(2.0)}

    def test_failed_chunk_does_not_propagate_params(self, monkeypatch, tmp_path):
        # When a chunk has no successful result, the template's
        # initial_params must stay unchanged for the next chunk.
        template = _minimal_template(
            free_parameter_unique_names=['cell.a'],
            initial_params={'cell.a': 1.0},
        )
        seen_initial = []

        def fake_worker(template_arg, path):
            seen_initial.append(template_arg.initial_params)
            return {
                'file_path': path,
                'fit_result.success': False,
                'fit_result.reduced_chi_square': None,
                'fit_result.iterations': 0,
                'params': {},
            }

        monkeypatch.setattr(sequential_mod, '_fit_worker', fake_worker)
        monkeypatch.setattr(sequential_mod, '_append_to_csv', lambda *a: None)
        monkeypatch.setattr(sequential_mod, '_report_chunk_progress', lambda *a: None)

        progress = sequential_mod.SequentialProgressContext(
            verbosity=VerbosityEnum.SILENT,
            state=None,
        )

        _run_fit_loop(
            contextlib.nullcontext(),
            [['a'], ['b']],
            template,
            (tmp_path / 'results.csv', ['file_path']),
            progress,
        )

        # Both chunks saw the original initial_params (no propagation).
        assert seen_initial == [{'cell.a': 1.0}, {'cell.a': 1.0}]


# ------------------------------------------------------------------
#  _prepare_sequential_run (no remaining files branch)
# ------------------------------------------------------------------


class TestPrepareSequentialRun:
    def _analysis(self, verbosity='short'):
        return SimpleNamespace(
            project=SimpleNamespace(
                verbosity=SimpleNamespace(fit=SimpleNamespace(value=verbosity)),
            ),
        )

    def test_returns_none_when_all_files_fitted(self, monkeypatch):
        analysis = self._analysis()
        template = _minimal_template()
        prints = []
        monkeypatch.setattr(sequential_mod, '_check_seq_preconditions', lambda project: None)
        monkeypatch.setattr(
            sequential_mod,
            'extract_data_paths_from_dir',
            lambda data_dir, file_pattern='*': ['a.dat', 'b.dat'],
        )
        monkeypatch.setattr(sequential_mod, '_build_template', lambda project: template)
        monkeypatch.setattr(
            sequential_mod,
            '_setup_csv_and_recovery',
            lambda project, tmpl, verb: (
                'csv',
                ['file_path'],
                {'a.dat', 'b.dat'},
                tmpl,
            ),
        )
        monkeypatch.setattr(
            sequential_mod,
            'console',
            SimpleNamespace(print=prints.append),
        )

        plan = _prepare_sequential_run(
            analysis,
            data_dir='/data',
            max_workers=1,
            chunk_size=None,
            file_pattern='*',
            reverse=False,
        )

        assert plan is None
        assert any('Nothing to do' in msg for msg in prints)

    def test_builds_plan_with_reverse_and_chunks(self, monkeypatch):
        analysis = self._analysis(verbosity='short')
        template = _minimal_template()
        monkeypatch.setattr(sequential_mod, '_check_seq_preconditions', lambda project: None)
        monkeypatch.setattr(
            sequential_mod,
            'extract_data_paths_from_dir',
            lambda data_dir, file_pattern='*': ['a.dat', 'b.dat', 'c.dat'],
        )
        monkeypatch.setattr(sequential_mod, '_build_template', lambda project: template)
        monkeypatch.setattr(
            sequential_mod,
            '_setup_csv_and_recovery',
            lambda project, tmpl, verb: ('csv', ['file_path'], set(), tmpl),
        )
        monkeypatch.setattr(
            sequential_mod,
            '_resolve_workers',
            lambda max_workers, chunk_size: (2, 2),
        )

        plan = _prepare_sequential_run(
            analysis,
            data_dir='/data',
            max_workers=2,
            chunk_size=2,
            file_pattern='*',
            reverse=True,
        )

        assert plan is not None
        # Reverse applied.
        assert plan.remaining == ['c.dat', 'b.dat', 'a.dat']
        # Chunked by 2.
        assert plan.chunks == [['c.dat', 'b.dat'], ['a.dat']]
        assert plan.max_workers == 2
        assert plan.processed_count == 3


# ------------------------------------------------------------------
#  fit_sequential top-level guards
# ------------------------------------------------------------------


class TestFitSequentialGuards:
    def test_returns_early_in_child_process(self, monkeypatch):
        monkeypatch.setattr(sequential_mod.mp, 'parent_process', object)
        prepared = []

        def record_prepare(*args, **kwargs):
            prepared.append(True)

        monkeypatch.setattr(sequential_mod, '_prepare_sequential_run', record_prepare)

        analysis = SimpleNamespace()
        sequential_mod.fit_sequential(analysis, data_dir='/data')

        assert prepared == []

    def test_returns_early_when_plan_is_none(self, monkeypatch):
        monkeypatch.setattr(sequential_mod.mp, 'parent_process', lambda: None)
        monkeypatch.setattr(sequential_mod, '_prepare_sequential_run', lambda *a, **k: None)
        # If we got past the plan-is-None guard, this would raise.
        monkeypatch.setattr(
            sequential_mod,
            '_print_sequential_header',
            lambda *a: (_ for _ in ()).throw(AssertionError('should not run')),
        )

        analysis = SimpleNamespace()
        # No exception means the early return fired.
        sequential_mod.fit_sequential(analysis, data_dir='/data')
