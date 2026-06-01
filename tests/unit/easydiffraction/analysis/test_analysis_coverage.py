# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Additional unit tests for analysis.py to cover patch gaps."""

from types import SimpleNamespace

import numpy as np


def _make_project():
    class ExpCol:
        def __init__(self):
            self._names = []

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

    class P:
        experiments = ExpCol()
        structures = ExpCol()
        _varname = 'proj'
        verbosity = 'full'

    return P()


# ------------------------------------------------------------------
# AnalysisDisplay.as_cif
# ------------------------------------------------------------------


class TestAnalysisDisplayAsCif:
    def test_as_cif_renders(self, capsys, monkeypatch):
        import easydiffraction.analysis.analysis as mod
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project())
        # Mock render_cif to avoid rendering issues
        rendered = {}

        def fake_render_cif(text):
            rendered['text'] = text

        monkeypatch.setattr(mod, 'render_cif', fake_render_cif)
        a.display.as_cif()
        out = capsys.readouterr().out
        assert 'Analysis' in out or 'cif' in out.lower()
        assert 'text' in rendered


# ------------------------------------------------------------------
# AnalysisDisplay.constraints (with items)
# ------------------------------------------------------------------


class TestAnalysisDisplayConstraints:
    def test_empty_constraints_warns(self, capsys):
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project())
        a.display.constraints()
        out = capsys.readouterr().out
        assert 'No constraints' in out

    def test_constraints_with_items(self, capsys, monkeypatch):
        import easydiffraction.analysis.categories.constraints.default as constraints_mod
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project())

        # Create a fake constraint with expression
        class FakeId:
            value = 'constraint_1'

        class FakeExpr:
            value = 'x = y + 1'

        class FakeConstraint:
            id = FakeId()
            expression = FakeExpr()

        a.constraints._items = [FakeConstraint()]

        captured = {}

        def fake_render_table(**kwargs):
            captured.update(kwargs)

        monkeypatch.setattr(constraints_mod, 'render_table', fake_render_table)
        a.display.constraints()
        out = capsys.readouterr().out
        assert 'User defined constraints' in out
        assert captured['columns_headers'] == ['id', 'expression']
        assert 'columns_data' in captured
        assert captured['columns_data'][0] == ['constraint_1', 'x = y + 1']


# ------------------------------------------------------------------
# Analysis._discover_property_rows / _discover_method_rows
# ------------------------------------------------------------------


class TestDiscoverHelpers:
    def test_discover_property_rows(self):
        from easydiffraction.analysis.analysis import _discover_property_rows

        class MyClass:
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
                pass

        rows = _discover_property_rows(MyClass)
        assert len(rows) == 2
        names = [row[0] for row in rows]
        assert 'alpha' in names
        assert 'beta' in names
        # beta is writable
        beta_row = next(r for r in rows if r[0] == 'beta')
        assert beta_row[1] == '✓'

    def test_discover_method_rows(self):
        from easydiffraction.analysis.analysis import _discover_method_rows

        class MyClass:
            def do_thing(self):
                """Do a thing."""

            def _private(self):
                pass

            @property
            def prop(self):
                """Not a method."""
                return 1

        rows = _discover_method_rows(MyClass)
        names = [row[0] for row in rows]
        assert 'do_thing()' in names
        assert '_private()' not in names
        assert 'prop()' not in names


# ------------------------------------------------------------------
# Analysis.minimizer.type setter
# ------------------------------------------------------------------


class TestCurrentMinimizerSetter:
    def test_setter_changes_minimizer(self, capsys):
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project())
        assert a.minimizer.type == 'lmfit (leastsq)'
        a.minimizer.type = 'lmfit'
        out = capsys.readouterr().out
        assert 'Current minimizer changed to' in out


# ------------------------------------------------------------------
# Analysis._snapshot_params
# ------------------------------------------------------------------


class TestSnapshotParams:
    def test_snapshot_stores_values(self):
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project())

        class FakeParam:
            unique_name = 'p1'
            value = 1.23
            uncertainty = 0.01
            units = 'angstroms'

            def resolve_display_units(self, context):
                assert context == 'gui'
                return 'Å'

        class FakeResults:
            parameters = [FakeParam()]

        a._snapshot_params('expt1', FakeResults())
        assert 'expt1' in a._parameter_snapshots
        assert a._parameter_snapshots['expt1']['p1']['value'] == 1.23
        assert a._parameter_snapshots['expt1']['p1']['uncertainty'] == 0.01
        assert a._parameter_snapshots['expt1']['p1']['units'] == 'Å'


class TestBayesianProjection:
    def test_single_parameter_projection_persists_distribution_and_predictive_caches(self):
        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.analysis.fit_helpers.bayesian import BayesianFitResults
        from easydiffraction.analysis.fit_helpers.bayesian import PosteriorParameterSummary
        from easydiffraction.analysis.fit_helpers.bayesian import PosteriorPredictiveSummary
        from easydiffraction.analysis.fit_helpers.bayesian import PosteriorSamples

        class Plotter:
            @staticmethod
            def _posterior_parameter_bounds(*, fit_results, parameter_name):
                del fit_results, parameter_name
                return 0.5, 1.5

            @staticmethod
            def _posterior_density_curve(values, *, lower_bound, upper_bound):
                del values
                return (
                    np.asarray([lower_bound, upper_bound], dtype=float),
                    np.asarray([0.25, 0.75], dtype=float),
                )

            @staticmethod
            def _resolve_x_axis(experiment_type, _axis_name):
                del experiment_type
                return np.asarray([1.0, 2.0], dtype=float), 'two_theta', None, None, None

            @staticmethod
            def _build_posterior_predictive_summary(
                *,
                fit_results,
                experiment,
                expt_name,
                x_axis,
                include_draws,
            ):
                del fit_results, experiment, x_axis, include_draws
                return PosteriorPredictiveSummary(
                    experiment_name=expt_name,
                    x_axis_name='two_theta',
                    x=np.asarray([1.0, 2.0], dtype=float),
                    best_sample_prediction=np.asarray([3.0, 4.0], dtype=float),
                    lower_95=np.asarray([2.5, 3.5], dtype=float),
                    upper_95=np.asarray([3.5, 4.5], dtype=float),
                )

        class Experiments:
            names = ['hrpt']

            def __getitem__(self, name):
                del name
                return SimpleNamespace(type='powder')

        project = SimpleNamespace(
            experiments=Experiments(),
            structures=object(),
            rendering_plot=SimpleNamespace(plotter=Plotter()),
            _varname='proj',
        )
        analysis = Analysis(project=project)

        results = BayesianFitResults(
            success=True,
            parameters=[],
            posterior_samples=PosteriorSamples(
                parameter_names=['alpha'],
                parameter_samples=np.asarray([[[1.0]], [[1.2]]], dtype=float),
            ),
            posterior_parameter_summaries=[
                PosteriorParameterSummary(
                    unique_name='alpha',
                    display_name='Alpha',
                    best_sample_value=1.2,
                    median=1.1,
                    standard_deviation=0.1,
                    interval_68=(1.0, 1.2),
                    interval_95=(0.9, 1.3),
                )
            ],
            posterior_predictive={},
            sampler_settings={},
            convergence_diagnostics={},
        )

        analysis._store_posterior_plot_cache_projection(results)

        sidecar = analysis._persisted_fit_state_sidecar
        assert sidecar['distribution_caches']
        assert sidecar['pair_caches'] == {}
        assert sidecar['predictive_datasets']
        assert np.allclose(
            sidecar['distribution_caches']['alpha']['x'],
            np.asarray([0.5, 1.5], dtype=float),
        )
        assert np.allclose(
            sidecar['predictive_datasets']['hrpt']['best_sample_prediction'],
            np.asarray([3.0, 4.0], dtype=float),
        )
