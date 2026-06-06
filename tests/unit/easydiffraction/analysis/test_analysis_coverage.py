# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Additional unit tests for analysis.py to cover patch gaps."""

from types import SimpleNamespace

import numpy as np


def _make_parameter(name, value):
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.variable import Parameter
    from easydiffraction.io.cif.handler import CifHandler

    return Parameter(
        name=name,
        value_spec=AttributeSpec(default=value),
        cif_handler=CifHandler(names=[f'_{name}.value']),
    )


def _make_project_with_parameters(structure_params, experiment_params=None):
    experiment_params = experiment_params or []

    class StructureColl:
        def __init__(self, params):
            self.parameters = list(params)

    class ExperimentColl:
        def __init__(self, params):
            self.parameters = list(params)
            self.names = []

        def values(self):
            return []

    return SimpleNamespace(
        structures=StructureColl(structure_params),
        experiments=ExperimentColl(experiment_params),
        info=SimpleNamespace(path=None),
        _varname='proj',
    )


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


# ------------------------------------------------------------------
# Module-level helpers: _parameter_display_units / _int_or_none
# ------------------------------------------------------------------


class TestModuleHelpers:
    def test_parameter_display_units_prefers_resolver(self):
        from easydiffraction.analysis.analysis import _parameter_display_units

        class WithResolver:
            def resolve_display_units(self, context):
                assert context == 'gui'
                return 'Å'

        assert _parameter_display_units(WithResolver()) == 'Å'

    def test_parameter_display_units_none_units_maps_to_empty(self):
        from easydiffraction.analysis.analysis import _parameter_display_units

        param = SimpleNamespace(units='none')
        assert _parameter_display_units(param) == ''

    def test_parameter_display_units_passes_through_plain_units(self):
        from easydiffraction.analysis.analysis import _parameter_display_units

        param = SimpleNamespace(units='deg')
        assert _parameter_display_units(param) == 'deg'

    def test_parameter_display_units_missing_attribute_falls_back(self):
        from easydiffraction.analysis.analysis import _parameter_display_units

        assert _parameter_display_units(object()) == 'N/A'

    def test_int_or_none_passes_none_through(self):
        from easydiffraction.analysis.analysis import _int_or_none

        assert _int_or_none(None) is None

    def test_int_or_none_coerces_value(self):
        from easydiffraction.analysis.analysis import _int_or_none

        assert _int_or_none(3.9) == 3
        assert _int_or_none('5') == 5


# ------------------------------------------------------------------
# Static numeric helpers
# ------------------------------------------------------------------


class TestNumericStatics:
    def test_finite_float_handles_none_and_nonfinite(self):
        from easydiffraction.analysis.analysis import Analysis

        assert Analysis._finite_float(None) is None
        assert Analysis._finite_float('not-a-number') is None
        assert Analysis._finite_float(float('inf')) is None
        assert Analysis._finite_float(float('nan')) is None
        assert Analysis._finite_float('2.5') == 2.5
        assert Analysis._finite_float(3) == 3.0

    def test_finite_metric_filters_nonfinite(self):
        from easydiffraction.analysis.analysis import Analysis

        assert Analysis._finite_metric(1.5) == 1.5
        assert Analysis._finite_metric(float('nan')) is None
        assert Analysis._finite_metric(float('inf')) is None

    def test_int_sampler_setting_defaults_and_none(self):
        from easydiffraction.analysis.analysis import Analysis

        assert Analysis._int_sampler_setting({}, 'missing') == 0
        assert Analysis._int_sampler_setting({'nsteps': None}, 'nsteps') == 0
        assert Analysis._int_sampler_setting({'nsteps': 100}, 'nsteps') == 100

    def test_sampler_sample_count_uses_steps_and_population(self):
        from easydiffraction.analysis.analysis import Analysis

        emcee_settings = {'nsteps': 10, 'nwalkers': 4}
        assert Analysis._sampler_sample_count(emcee_settings, n_parameters=3) == 120

        dream_settings = {'steps': 5, 'pop': 2}
        assert Analysis._sampler_sample_count(dream_settings, n_parameters=3) == 30

    def test_sampler_sample_count_clamps_negatives_to_zero(self):
        from easydiffraction.analysis.analysis import Analysis

        assert Analysis._sampler_sample_count({'steps': -5, 'pop': 4}, n_parameters=3) == 0
        assert Analysis._sampler_sample_count({}, n_parameters=3) == 0


# ------------------------------------------------------------------
# Software-provenance helpers
# ------------------------------------------------------------------


class TestSoftwareValues:
    def test_type_info_tag_reads_enum_value(self):
        from easydiffraction.analysis.analysis import Analysis

        engine = SimpleNamespace(type_info=SimpleNamespace(tag=SimpleNamespace(value='cryspy')))
        assert Analysis._type_info_tag(engine) == 'cryspy'

    def test_type_info_tag_reads_plain_string(self):
        from easydiffraction.analysis.analysis import Analysis

        engine = SimpleNamespace(type_info=SimpleNamespace(tag='lmfit (leastsq)'))
        assert Analysis._type_info_tag(engine) == 'lmfit (leastsq)'

    def test_type_info_tag_missing_returns_empty(self):
        from easydiffraction.analysis.analysis import Analysis

        assert Analysis._type_info_tag(object()) == ''

    def test_software_version_unknown_engine_is_none(self):
        from easydiffraction.analysis.analysis import Analysis

        assert Analysis._software_version('not-a-real-engine') is None

    def test_software_version_known_engine_delegates(self, monkeypatch):
        import easydiffraction.analysis.analysis as mod
        from easydiffraction.analysis.analysis import Analysis

        monkeypatch.setattr(mod, 'package_version', lambda name: f'{name}-9.9')
        # 'pdffit' maps to the 'diffpy.pdffit2' package name.
        assert Analysis._software_version('pdffit') == 'diffpy.pdffit2-9.9'
        assert Analysis._software_version('lmfit') == 'lmfit-9.9'

    def test_software_package_name_strips_minimizer_settings(self):
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project())
        engine = SimpleNamespace(type_info=SimpleNamespace(tag='lmfit (leastsq)'))
        assert a._software_package_name(engine) == 'lmfit'

    def test_software_values_returns_name_version_url(self, monkeypatch):
        import easydiffraction.analysis.analysis as mod
        from easydiffraction.analysis.analysis import Analysis

        monkeypatch.setattr(mod, 'package_version', lambda name: '1.2.3')
        a = Analysis(project=_make_project())
        engine = SimpleNamespace(
            type_info=SimpleNamespace(tag='lmfit (leastsq)'),
            url='https://lmfit.example',
        )
        assert a._software_values(engine) == ('lmfit', '1.2.3', 'https://lmfit.example')

    def test_combine_software_values_joins_unique_sorted(self):
        from easydiffraction.analysis.analysis import Analysis

        values = [
            ('cryspy', '1.0', 'u1'),
            ('cryspy', '1.0', 'u1'),
            ('pdffit', '2.0', 'u2'),
        ]
        name, version, url = Analysis._combine_software_values(values)
        assert name == 'cryspy, pdffit'
        assert version == '1.0, 2.0'
        assert url == 'u1, u2'

    def test_combine_software_values_empty_returns_none_triple(self):
        from easydiffraction.analysis.analysis import Analysis

        assert Analysis._combine_software_values([]) == (None, None, None)

    def test_combine_software_values_all_blank_fields_collapse_to_none(self):
        from easydiffraction.analysis.analysis import Analysis

        name, version, url = Analysis._combine_software_values([('engine', None, None)])
        assert name == 'engine'
        assert version is None
        assert url is None

    def test_set_software_role_assigns_fields(self):
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project())
        Analysis._set_software_role(a.software.framework, ('EasyDiffraction', '9.9', 'url'))
        assert a.software.framework.name.value == 'EasyDiffraction'
        assert a.software.framework.version.value == '9.9'
        assert a.software.framework.url.value == 'url'

    def test_has_software_provenance_tracks_stamping(self):
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project())
        assert a._has_software_provenance() is False
        a.software.framework.name = 'EasyDiffraction'
        assert a._has_software_provenance() is True


# ------------------------------------------------------------------
# IUCr / R-factor metric helpers (engine-free, array-driven)
# ------------------------------------------------------------------


def _intensity_experiment(*, meas, calc, su):
    data = SimpleNamespace(
        intensity_meas=np.asarray(meas, dtype=float),
        intensity_calc=np.asarray(calc, dtype=float),
        intensity_meas_su=np.asarray(su, dtype=float),
    )
    return SimpleNamespace(data=data)


class TestMetricHelpers:
    def test_fit_data_point_count_sums_measured_sizes(self):
        from easydiffraction.analysis.analysis import Analysis

        experiments = [
            _intensity_experiment(meas=[1.0, 2.0, 3.0], calc=[1, 2, 3], su=[1, 1, 1]),
            _intensity_experiment(meas=[4.0, 5.0], calc=[4, 5], su=[1, 1]),
        ]
        assert Analysis._fit_data_point_count(experiments) == 5

    def test_fit_intensity_arrays_drops_nonfinite_and_nonpositive_su(self):
        from easydiffraction.analysis.analysis import Analysis

        experiment = _intensity_experiment(
            meas=[1.0, 2.0, np.nan, 4.0, 5.0],
            calc=[1.1, 2.1, 3.0, np.inf, 5.5],
            su=[0.1, 0.0, 0.1, 0.1, 0.2],
        )
        observed, calculated, uncertainties = Analysis._fit_intensity_arrays([experiment])
        # Only rows 0 and 4 survive: row1 su<=0, row2 meas nan, row3 calc inf.
        assert np.allclose(observed, [1.0, 5.0])
        assert np.allclose(calculated, [1.1, 5.5])
        assert np.allclose(uncertainties, [0.1, 0.2])

    def test_r_factor_or_none_empty_returns_none(self):
        from easydiffraction.analysis.analysis import Analysis

        empty = np.asarray([], dtype=float)
        assert Analysis._r_factor_or_none(empty, empty) is None

    def test_r_factor_or_none_computes_value(self):
        from easydiffraction.analysis.analysis import Analysis

        observed = np.asarray([10.0, 10.0], dtype=float)
        calculated = np.asarray([9.0, 11.0], dtype=float)
        # sum|obs-calc| / sum|obs| = 2 / 20 = 0.1
        assert Analysis._r_factor_or_none(observed, calculated) == 0.1

    def test_weighted_r_factor_or_none_empty_and_zero_denominator(self):
        from easydiffraction.analysis.analysis import Analysis

        empty = np.asarray([], dtype=float)
        assert Analysis._weighted_r_factor_or_none(empty, empty, empty) is None

        observed = np.asarray([0.0, 0.0], dtype=float)
        calculated = np.asarray([0.0, 0.0], dtype=float)
        uncertainties = np.asarray([1.0, 1.0], dtype=float)
        assert Analysis._weighted_r_factor_or_none(observed, calculated, uncertainties) is None

    def test_weighted_r_factor_or_none_computes_value(self):
        from easydiffraction.analysis.analysis import Analysis

        observed = np.asarray([10.0, 10.0], dtype=float)
        calculated = np.asarray([10.0, 10.0], dtype=float)
        uncertainties = np.asarray([1.0, 1.0], dtype=float)
        assert Analysis._weighted_r_factor_or_none(observed, calculated, uncertainties) == 0.0

    def test_expected_weighted_r_factor_guards(self):
        from easydiffraction.analysis.analysis import Analysis

        observed = np.asarray([10.0, 10.0], dtype=float)
        uncertainties = np.asarray([1.0, 1.0], dtype=float)
        # Empty observations -> None.
        empty = np.asarray([], dtype=float)
        assert Analysis._expected_weighted_r_factor(empty, empty, 1) is None
        # Non-positive degrees of freedom -> None.
        assert Analysis._expected_weighted_r_factor(observed, uncertainties, 0) is None
        # Valid: sqrt(dof / sum(w * obs^2)) = sqrt(1 / 200).
        value = Analysis._expected_weighted_r_factor(observed, uncertainties, 1)
        assert value is not None
        assert np.isclose(value, np.sqrt(1.0 / 200.0))

    def test_gt_observation_mask_uses_three_sigma(self):
        from easydiffraction.analysis.analysis import Analysis

        observed = np.asarray([2.0, 4.0], dtype=float)
        uncertainties = np.asarray([1.0, 1.0], dtype=float)
        mask = Analysis._gt_observation_mask(observed, uncertainties)
        assert mask.tolist() == [False, True]


# ------------------------------------------------------------------
# Powder / category-type / reflection helpers
# ------------------------------------------------------------------


class TestExperimentClassificationHelpers:
    def test_is_powder_fit_detects_powder(self):
        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum

        powder = SimpleNamespace(
            type=SimpleNamespace(sample_form=SimpleNamespace(value=SampleFormEnum.POWDER.value))
        )
        single = SimpleNamespace(
            type=SimpleNamespace(
                sample_form=SimpleNamespace(value=SampleFormEnum.SINGLE_CRYSTAL.value)
            )
        )
        assert Analysis._is_powder_fit([single, powder]) is True
        assert Analysis._is_powder_fit([single]) is False

    def test_unique_category_type_names_dedupes_and_handles_missing(self):
        from easydiffraction.analysis.analysis import Analysis

        e1 = SimpleNamespace(peak=SimpleNamespace(type=SimpleNamespace(value='gaussian')))
        e2 = SimpleNamespace(peak=SimpleNamespace(type=SimpleNamespace(value='gaussian')))
        e3 = SimpleNamespace(peak=SimpleNamespace(type=SimpleNamespace(value='lorentzian')))
        e4 = SimpleNamespace()  # no 'peak' attribute -> skipped
        names = Analysis._unique_category_type_names([e1, e2, e3, e4], 'peak')
        assert names == 'gaussian, lorentzian'

    def test_unique_category_type_names_all_missing_returns_none(self):
        from easydiffraction.analysis.analysis import Analysis

        assert Analysis._unique_category_type_names([SimpleNamespace()], 'peak') is None

    def test_reflection_counts_no_reflections_returns_none_pair(self):
        from easydiffraction.analysis.analysis import Analysis

        # Empty refln and missing refln both yield no reflections.
        empty_refln = []
        e1 = SimpleNamespace(refln=empty_refln)
        e2 = SimpleNamespace()
        assert Analysis._reflection_counts([e1, e2]) == (None, None)

    def test_reflection_counts_thresholds_observations(self):
        from easydiffraction.analysis.analysis import Analysis

        class Refln:
            def __init__(self, meas, su):
                self.intensity_meas = meas
                self.intensity_meas_su = su

            def __len__(self):
                return len(self.intensity_meas)

        # meas > 3 * su for index 1 only (10 > 3); index 0: 2 < 3.
        refln = Refln([2.0, 10.0], [1.0, 1.0])
        experiment = SimpleNamespace(refln=refln)
        total, greater_than = Analysis._reflection_counts([experiment])
        assert total == 2
        assert greater_than == 1

    def test_reflection_counts_shape_mismatch_skips_threshold(self):
        from easydiffraction.analysis.analysis import Analysis

        class Refln:
            def __init__(self, meas, su):
                self.intensity_meas = meas
                self.intensity_meas_su = su

            def __len__(self):
                return len(self.intensity_meas)

        refln = Refln([2.0, 10.0, 20.0], [1.0, 1.0])  # mismatched shapes
        experiment = SimpleNamespace(refln=refln)
        total, greater_than = Analysis._reflection_counts([experiment])
        assert total == 3
        assert greater_than == 0


# ------------------------------------------------------------------
# Shift-over-su and covariance/correlation helpers
# ------------------------------------------------------------------


def _shift_param(*, value, start, uncertainty):
    return SimpleNamespace(value=value, _fit_start_value=start, uncertainty=uncertainty)


class TestShiftAndCovariance:
    def test_shift_over_su_values_skips_incomplete_and_nonpositive(self):
        from easydiffraction.analysis.analysis import Analysis

        params = [
            _shift_param(value=4.2, start=4.0, uncertainty=0.1),  # |0.2|/0.1 = 2.0
            _shift_param(value=4.2, start=None, uncertainty=0.1),  # no start
            _shift_param(value=4.2, start=4.0, uncertainty=None),  # no uncertainty
            _shift_param(value=4.2, start=4.0, uncertainty=0.0),  # su <= 0
        ]
        values = Analysis._shift_over_su_values(params)
        assert np.allclose(values, [2.0])

    def test_shift_over_su_summary_empty_returns_none_pair(self):
        from easydiffraction.analysis.analysis import Analysis

        assert Analysis._shift_over_su_summary([]) == (None, None)

    def test_shift_over_su_summary_max_and_mean(self):
        from easydiffraction.analysis.analysis import Analysis

        params = [
            _shift_param(value=4.2, start=4.0, uncertainty=0.1),  # 2.0
            _shift_param(value=4.0, start=4.4, uncertainty=0.1),  # 4.0
        ]
        shift_max, shift_mean = Analysis._shift_over_su_summary(params)
        assert np.isclose(shift_max, 4.0)
        assert np.isclose(shift_mean, 3.0)

    def test_resolve_covariance_matrix_reads_covar_attribute(self):
        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.analysis.fit_helpers.reporting import FitResults

        covar = np.asarray([[1.0, 0.5], [0.5, 2.0]], dtype=float)
        results = FitResults(success=True, engine_result=SimpleNamespace(covar=covar))
        resolved = Analysis._resolve_covariance_matrix(results)
        assert np.allclose(resolved, covar)

    def test_resolve_covariance_matrix_rejects_nonsquare(self):
        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.analysis.fit_helpers.reporting import FitResults

        nonsquare = np.asarray([[1.0, 0.5, 0.2]], dtype=float)
        results = FitResults(success=True, engine_result=SimpleNamespace(covar=nonsquare))
        assert Analysis._resolve_covariance_matrix(results) is None

    def test_resolve_covariance_matrix_missing_returns_none(self):
        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.analysis.fit_helpers.reporting import FitResults

        results = FitResults(success=True, engine_result=SimpleNamespace())
        assert Analysis._resolve_covariance_matrix(results) is None

    def test_correlation_matrix_from_covariance_normalizes(self):
        from easydiffraction.analysis.analysis import Analysis

        covariance = np.asarray([[4.0, 2.0], [2.0, 9.0]], dtype=float)
        correlation = Analysis._correlation_matrix_from_covariance(covariance)
        assert correlation is not None
        # off-diagonal = 2 / (2 * 3) = 1/3
        assert np.isclose(correlation[0, 1], 2.0 / 6.0)
        assert np.allclose(np.diag(correlation), [1.0, 1.0])

    def test_correlation_matrix_from_covariance_nonpositive_diag_returns_none(self):
        from easydiffraction.analysis.analysis import Analysis

        covariance = np.asarray([[0.0, 0.0], [0.0, 1.0]], dtype=float)
        assert Analysis._correlation_matrix_from_covariance(covariance) is None

    def test_resolve_objective_value_passthrough_and_none(self):
        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.analysis.fit_helpers.reporting import FitResults

        results = FitResults(success=True)
        results.chi_square = None
        assert Analysis._resolve_objective_value(results) is None
        results.chi_square = 12.5
        assert Analysis._resolve_objective_value(results) == 12.5


# ------------------------------------------------------------------
# Correlation projection storage
# ------------------------------------------------------------------


class TestCorrelationProjection:
    def test_store_correlation_projection_single_name_is_noop(self):
        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.analysis.enums import FitCorrelationSourceEnum

        a = Analysis(project=_make_project())
        a._store_correlation_projection(
            unique_names=['only'],
            correlation_matrix=np.asarray([[1.0]], dtype=float),
            source_kind=FitCorrelationSourceEnum.DETERMINISTIC,
        )
        assert len(a.fit_parameter_correlations) == 0

    def test_store_correlation_projection_shape_mismatch_is_noop(self):
        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.analysis.enums import FitCorrelationSourceEnum

        a = Analysis(project=_make_project())
        a._store_correlation_projection(
            unique_names=['a', 'b'],
            correlation_matrix=np.asarray([[1.0]], dtype=float),
            source_kind=FitCorrelationSourceEnum.DETERMINISTIC,
        )
        assert len(a.fit_parameter_correlations) == 0

    def test_store_correlation_projection_writes_upper_triangle_clipped(self):
        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.analysis.enums import FitCorrelationSourceEnum

        a = Analysis(project=_make_project())
        # Off-diagonal above 1.0 must be clipped to 1.0; non-finite skipped.
        matrix = np.asarray(
            [
                [1.0, 1.5, np.nan],
                [1.5, 1.0, 0.4],
                [np.nan, 0.4, 1.0],
            ],
            dtype=float,
        )
        a._store_correlation_projection(
            unique_names=['p1', 'p2', 'p3'],
            correlation_matrix=matrix,
            source_kind=FitCorrelationSourceEnum.POSTERIOR,
        )
        # Pairs: (p1,p2) clipped to 1.0, (p1,p3) nan -> skipped, (p2,p3)=0.4.
        assert len(a.fit_parameter_correlations) == 2
        correlations = sorted(row.correlation.value for row in a.fit_parameter_correlations)
        assert np.allclose(correlations, [0.4, 1.0])


# ------------------------------------------------------------------
# Predictive dataset payload
# ------------------------------------------------------------------


class TestPredictiveDatasetPayload:
    def test_payload_includes_only_present_optional_arrays(self):
        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.analysis.fit_helpers.bayesian import PosteriorPredictiveSummary

        summary = PosteriorPredictiveSummary(
            experiment_name='hrpt',
            x_axis_name='two_theta',
            x=np.asarray([1.0, 2.0], dtype=float),
            best_sample_prediction=np.asarray([3.0, 4.0], dtype=float),
        )
        payload = Analysis._predictive_dataset_payload(summary)
        assert payload['x_axis_name'] == 'two_theta'
        assert np.allclose(payload['x'], [1.0, 2.0])
        assert np.allclose(payload['best_sample_prediction'], [3.0, 4.0])
        # Optional arrays not provided are omitted.
        for optional in ('lower_95', 'upper_95', 'lower_68', 'upper_68', 'draws'):
            assert optional not in payload

    def test_payload_includes_all_optional_arrays_when_present(self):
        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.analysis.fit_helpers.bayesian import PosteriorPredictiveSummary

        summary = PosteriorPredictiveSummary(
            experiment_name='hrpt',
            x_axis_name='two_theta',
            x=np.asarray([1.0], dtype=float),
            best_sample_prediction=np.asarray([3.0], dtype=float),
            lower_95=np.asarray([2.5], dtype=float),
            upper_95=np.asarray([3.5], dtype=float),
            lower_68=np.asarray([2.8], dtype=float),
            upper_68=np.asarray([3.2], dtype=float),
            draws=np.asarray([[3.0, 3.1]], dtype=float),
        )
        payload = Analysis._predictive_dataset_payload(summary)
        for optional in ('lower_95', 'upper_95', 'lower_68', 'upper_68', 'draws'):
            assert optional in payload


# ------------------------------------------------------------------
# Posterior contour / pair-metadata statics
# ------------------------------------------------------------------


class TestPosteriorPairStatics:
    def test_contour_levels_scale_with_density_max(self):
        from easydiffraction.analysis.analysis import Analysis

        density = np.asarray([0.0, 2.0, 1.0], dtype=float)
        levels = Analysis._posterior_pair_contour_levels(density)
        assert np.allclose(
            levels,
            2.0 * np.asarray([0.20, 0.35, 0.50, 0.65, 0.80, 0.95]),
        )

    def test_contour_levels_nonpositive_max_returns_empty(self):
        from easydiffraction.analysis.analysis import Analysis

        density = np.asarray([0.0, 0.0], dtype=float)
        assert Analysis._posterior_pair_contour_levels(density).size == 0

    def test_ordered_pair_metadata_sorts_by_name(self):
        from easydiffraction.analysis.analysis import Analysis

        names = ['z_param', 'a_param']
        x_index, y_index, x_name, y_name = Analysis._ordered_pair_metadata(names, 0, 1)
        # z_param > a_param so the pair is swapped into name order.
        assert (x_index, y_index) == (1, 0)
        assert (x_name, y_name) == ('a_param', 'z_param')

    def test_ordered_pair_metadata_keeps_order_when_already_sorted(self):
        from easydiffraction.analysis.analysis import Analysis

        names = ['a_param', 'z_param']
        x_index, y_index, x_name, y_name = Analysis._ordered_pair_metadata(names, 0, 1)
        assert (x_index, y_index) == (0, 1)
        assert (x_name, y_name) == ('a_param', 'z_param')


# ------------------------------------------------------------------
# Bayesian restore statics
# ------------------------------------------------------------------


class TestBayesianRestoreStatics:
    def test_restored_bayesian_converged_true_when_thresholds_met(self):
        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.analysis.fit_helpers.bayesian import ESS_BULK_CONVERGENCE_THRESHOLD
        from easydiffraction.analysis.fit_helpers.bayesian import R_HAT_CONVERGENCE_THRESHOLD

        assert (
            Analysis._restored_bayesian_converged(
                max_r_hat=R_HAT_CONVERGENCE_THRESHOLD,
                min_ess_bulk=ESS_BULK_CONVERGENCE_THRESHOLD,
            )
            is True
        )

    def test_restored_bayesian_converged_false_when_r_hat_high(self):
        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.analysis.fit_helpers.bayesian import ESS_BULK_CONVERGENCE_THRESHOLD

        assert (
            Analysis._restored_bayesian_converged(
                max_r_hat=10.0,
                min_ess_bulk=ESS_BULK_CONVERGENCE_THRESHOLD,
            )
            is False
        )

    def test_restored_bayesian_converged_false_when_value_missing(self):
        from easydiffraction.analysis.analysis import Analysis

        assert Analysis._restored_bayesian_converged(max_r_hat=None, min_ess_bulk=1000.0) is False
        assert Analysis._restored_bayesian_converged(max_r_hat=1.0, min_ess_bulk=None) is False

    def test_bayesian_result_random_seed_handles_none(self):
        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.analysis.fit_helpers.bayesian import BayesianFitResults

        results = BayesianFitResults(success=True, sampler_settings={'random_seed': None})
        assert Analysis._bayesian_result_random_seed(results) is None

        results = BayesianFitResults(success=True, sampler_settings={'random_seed': 7})
        assert Analysis._bayesian_result_random_seed(results) == 7

    def test_restored_bayesian_random_seed_prefers_persisted_value(self):
        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.analysis.categories.fit_result.bayesian import BayesianFitResult

        a = Analysis(project=_make_project())
        a._fit_result._parent = None
        a._fit_result = BayesianFitResult()
        a._fit_result._parent = a
        a.fit_result._set_resolved_random_seed(99)
        assert a._restored_bayesian_random_seed({'random_seed': 1}) == 99

    def test_restored_bayesian_random_seed_falls_back_to_settings(self):
        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.analysis.categories.fit_result.bayesian import BayesianFitResult

        a = Analysis(project=_make_project())
        a._fit_result._parent = None
        a._fit_result = BayesianFitResult()
        a._fit_result._parent = a
        # resolved_random_seed defaults to None -> use sampler settings.
        assert a._restored_bayesian_random_seed({'random_seed': 5}) == 5


# ------------------------------------------------------------------
# Fit-request validation
# ------------------------------------------------------------------


class TestFitRequestValidation:
    def test_validate_resume_extra_steps_rejects_bad_values(self):
        import pytest

        from easydiffraction.analysis.analysis import Analysis

        for bad in (None, True, 0, -1, 2.5, 'x'):
            with pytest.raises(ValueError, match='positive integer'):
                Analysis._validate_resume_extra_steps(bad)

    def test_validate_resume_extra_steps_accepts_positive_int(self):
        from easydiffraction.analysis.analysis import Analysis

        assert Analysis._validate_resume_extra_steps(3) == 3

    def test_validate_fit_request_extra_steps_without_resume_raises(self):
        import pytest

        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.analysis.enums import FitModeEnum

        a = Analysis(project=_make_project())
        with pytest.raises(ValueError, match='extra_steps is only valid when resume=True'):
            a._validate_fit_request(mode=FitModeEnum.SINGLE, resume=False, extra_steps=5)

    def test_validate_fit_request_resume_requires_single_mode(self):
        import pytest

        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.analysis.enums import FitModeEnum

        a = Analysis(project=_make_project())
        a.minimizer.type = 'emcee'
        with pytest.raises(ValueError, match='single fit mode only'):
            a._validate_fit_request(mode=FitModeEnum.JOINT, resume=True, extra_steps=None)

    def test_validate_fit_request_resume_requires_emcee(self):
        import pytest

        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.analysis.enums import FitModeEnum

        a = Analysis(project=_make_project())  # default lmfit minimizer
        with pytest.raises(ValueError, match=r"analysis.minimizer.type = 'emcee'"):
            a._validate_fit_request(mode=FitModeEnum.SINGLE, resume=True, extra_steps=None)


# ------------------------------------------------------------------
# Sequential data-dir resolution
# ------------------------------------------------------------------


class TestSequentialDataDir:
    def test_absolute_data_dir_returned_directly(self, tmp_path):
        from easydiffraction.analysis.analysis import Analysis

        project = SimpleNamespace(
            experiments=SimpleNamespace(values=list),
            structures=object(),
            info=SimpleNamespace(path=None),
            _varname='proj',
        )
        a = Analysis(project=project)
        a.sequential_fit.data_dir.value = str(tmp_path)
        assert a._resolve_sequential_data_dir() == tmp_path

    def test_relative_data_dir_requires_saved_project(self):
        import pytest

        from easydiffraction.analysis.analysis import Analysis

        project = SimpleNamespace(
            experiments=SimpleNamespace(values=list),
            structures=object(),
            info=SimpleNamespace(path=None),
            _varname='proj',
        )
        a = Analysis(project=project)
        a.sequential_fit.data_dir.value = 'scans'
        with pytest.raises(ValueError, match='Project must be saved'):
            a._resolve_sequential_data_dir()

    def test_relative_data_dir_joined_to_project_path(self, tmp_path):
        from easydiffraction.analysis.analysis import Analysis

        project = SimpleNamespace(
            experiments=SimpleNamespace(values=list),
            structures=object(),
            info=SimpleNamespace(path=tmp_path),
            _varname='proj',
        )
        a = Analysis(project=project)
        a.sequential_fit.data_dir.value = 'scans'
        assert a._resolve_sequential_data_dir() == tmp_path / 'scans'


# ------------------------------------------------------------------
# Resumable emcee sidecar detection (filesystem in tmp_path only)
# ------------------------------------------------------------------


class TestResumableEmceeSidecar:
    def test_no_project_path_returns_false(self):
        from easydiffraction.analysis.analysis import Analysis

        project = SimpleNamespace(
            experiments=SimpleNamespace(values=list),
            structures=object(),
            info=SimpleNamespace(path=None),
            _varname='proj',
        )
        a = Analysis(project=project)
        assert a._has_resumable_emcee_sidecar() is False

    def test_missing_sidecar_file_returns_false(self, tmp_path):
        from easydiffraction.analysis.analysis import Analysis

        project = SimpleNamespace(
            experiments=SimpleNamespace(values=list),
            structures=object(),
            info=SimpleNamespace(path=tmp_path),
            _varname='proj',
        )
        a = Analysis(project=project)
        assert a._has_resumable_emcee_sidecar() is False

    def test_sidecar_with_positive_iteration_returns_true(self, tmp_path):
        import h5py

        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.analysis.minimizers.emcee import EMCEE_CHAIN_GROUP

        analysis_dir = tmp_path / 'analysis'
        analysis_dir.mkdir()
        sidecar = analysis_dir / 'results.h5'
        with h5py.File(sidecar, 'w') as handle:
            group = handle.create_group(EMCEE_CHAIN_GROUP)
            group.attrs['iteration'] = 12

        project = SimpleNamespace(
            experiments=SimpleNamespace(values=list),
            structures=object(),
            info=SimpleNamespace(path=tmp_path),
            _varname='proj',
        )
        a = Analysis(project=project)
        assert a._has_resumable_emcee_sidecar() is True

    def test_sidecar_with_zero_iteration_returns_false(self, tmp_path):
        import h5py

        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.analysis.minimizers.emcee import EMCEE_CHAIN_GROUP

        analysis_dir = tmp_path / 'analysis'
        analysis_dir.mkdir()
        sidecar = analysis_dir / 'results.h5'
        with h5py.File(sidecar, 'w') as handle:
            group = handle.create_group(EMCEE_CHAIN_GROUP)
            group.attrs['iteration'] = 0

        project = SimpleNamespace(
            experiments=SimpleNamespace(values=list),
            structures=object(),
            info=SimpleNamespace(path=tmp_path),
            _varname='proj',
        )
        a = Analysis(project=project)
        assert a._has_resumable_emcee_sidecar() is False

    def test_sidecar_without_chain_group_returns_false(self, tmp_path):
        import h5py

        from easydiffraction.analysis.analysis import Analysis

        analysis_dir = tmp_path / 'analysis'
        analysis_dir.mkdir()
        sidecar = analysis_dir / 'results.h5'
        with h5py.File(sidecar, 'w') as handle:
            handle.create_group('some_other_group')

        project = SimpleNamespace(
            experiments=SimpleNamespace(values=list),
            structures=object(),
            info=SimpleNamespace(path=tmp_path),
            _varname='proj',
        )
        a = Analysis(project=project)
        assert a._has_resumable_emcee_sidecar() is False


# ------------------------------------------------------------------
# Joint-fit preparation
# ------------------------------------------------------------------


class TestPrepareJointFit:
    def _project_with_named_experiments(self, names):
        class Experiments:
            def __init__(self, names):
                self._names = names

            def __len__(self):
                return len(self._names)

            @property
            def names(self):
                return self._names

        return SimpleNamespace(
            experiments=Experiments(names),
            structures=object(),
            info=SimpleNamespace(path=None),
            _varname='proj',
        )

    def test_requires_at_least_two_experiments(self):
        import pytest

        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=self._project_with_named_experiments(['e1']))
        with pytest.raises(ValueError, match='at least 2 experiments'):
            a._prepare_joint_fit()

    def test_auto_populates_missing_rows(self):
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=self._project_with_named_experiments(['e1', 'e2']))
        a._prepare_joint_fit()
        ids = sorted(item.experiment_id.value for item in a.joint_fit)
        assert ids == ['e1', 'e2']

    def test_rejects_rows_not_in_project(self):
        import pytest

        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=self._project_with_named_experiments(['e1', 'e2']))
        a.joint_fit.create(experiment_id='ghost', weight=1.0)
        with pytest.raises(ValueError, match='not present in the project'):
            a._prepare_joint_fit()


# ------------------------------------------------------------------
# Help filter for mode-specific categories
# ------------------------------------------------------------------


class TestHelpFilter:
    def test_single_mode_hides_joint_and_sequential(self):
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project())
        a._set_fitting_mode_type('single')
        properties = ['minimizer', 'joint_fit', 'sequential_fit', 'sequential_fit_extract']
        filtered, methods = a._help_filter(properties, ['fit'])
        assert filtered == ['minimizer']
        assert methods == ['fit']

    def test_joint_mode_keeps_joint_hides_sequential(self):
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project())
        a._set_fitting_mode_type('joint')
        properties = ['joint_fit', 'sequential_fit', 'sequential_fit_extract']
        filtered, _ = a._help_filter(properties, [])
        assert filtered == ['joint_fit']

    def test_sequential_mode_hides_only_joint(self):
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project())
        a._set_fitting_mode_type('sequential')
        properties = ['joint_fit', 'sequential_fit', 'sequential_fit_extract']
        filtered, _ = a._help_filter(properties, [])
        assert filtered == ['sequential_fit', 'sequential_fit_extract']


# ------------------------------------------------------------------
# Random-seed resolution
# ------------------------------------------------------------------


class TestResolvedFitRandomSeed:
    def test_explicit_seed_takes_precedence(self):
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project())
        assert a._resolved_fit_random_seed(42) == 42

    def test_falls_back_to_minimizer_seed(self, monkeypatch):
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project())
        monkeypatch.setattr(a.minimizer, '_native_kwargs', lambda: {'random_seed': 7})
        assert a._resolved_fit_random_seed(None) == 7

    def test_returns_none_when_no_seed_available(self, monkeypatch):
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project())
        monkeypatch.setattr(a.minimizer, '_native_kwargs', lambda: {'random_seed': None})
        assert a._resolved_fit_random_seed(None) is None


# ------------------------------------------------------------------
# Engine sync from minimizer category
# ------------------------------------------------------------------


class TestSyncEngineFromMinimizer:
    def test_sync_warns_for_unsupported_setting(self, monkeypatch):
        import easydiffraction.analysis.analysis as mod
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project())
        warnings = []
        monkeypatch.setattr(mod.log, 'warning', warnings.append)

        # Engine that lacks the 'method' attribute the kwargs reference.
        engine = SimpleNamespace()
        a.fitter.minimizer = engine
        monkeypatch.setattr(a.minimizer, '_native_kwargs', lambda: {'method': 'leastsq'})
        monkeypatch.setattr(
            type(a.minimizer), '_engine_sync_skip_keys', frozenset(), raising=False
        )

        a._sync_engine_from_minimizer_category()

        assert any('is not supported by' in message for message in warnings)

    def test_sync_applies_supported_settings_and_skips_keys(self, monkeypatch):
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project())
        engine = SimpleNamespace(tolerance=0.0, skipme=None)
        a.fitter.minimizer = engine
        monkeypatch.setattr(
            a.minimizer,
            '_native_kwargs',
            lambda: {'tolerance': 1e-6, 'skipme': 'should-not-apply'},
        )
        monkeypatch.setattr(
            type(a.minimizer),
            '_engine_sync_skip_keys',
            frozenset({'skipme'}),
            raising=False,
        )

        a._sync_engine_from_minimizer_category()

        assert engine.tolerance == 1e-6
        assert engine.skipme is None


# ------------------------------------------------------------------
# Restored posterior samples shape validation
# ------------------------------------------------------------------


class TestRestoredPosteriorSamples:
    def test_no_parameter_samples_returns_none(self):
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project())
        a._persisted_fit_state_sidecar = {'posterior': {}}
        assert a._restored_posterior_samples() is None

    def test_invalid_ndim_warns_and_returns_none(self, monkeypatch):
        import easydiffraction.analysis.analysis as mod
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project())
        warnings = []
        monkeypatch.setattr(mod.log, 'warning', warnings.append)
        # 2-D array (not 3-D) is rejected.
        a._persisted_fit_state_sidecar = {
            'posterior': {'parameter_samples': [[1.0, 2.0], [3.0, 4.0]]}
        }
        assert a._restored_posterior_samples() is None
        assert any('invalid shape' in message for message in warnings)

    def test_parameter_count_mismatch_warns_and_returns_none(self, monkeypatch):
        import easydiffraction.analysis.analysis as mod
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project())
        warnings = []
        monkeypatch.setattr(mod.log, 'warning', warnings.append)
        # No persisted posterior rows -> parameter_names is empty, but the
        # 3-D array has 2 parameters on its last axis -> mismatch.
        a._persisted_fit_state_sidecar = {
            'posterior': {'parameter_samples': np.zeros((4, 2, 2)).tolist()}
        }
        assert a._restored_posterior_samples() is None
        assert any('do not match' in message for message in warnings)


# ------------------------------------------------------------------
# Common fit-result projection storage
# ------------------------------------------------------------------


class TestCommonFitResultProjection:
    def test_stores_shared_fields_and_sets_persisted_flag(self):
        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.analysis.enums import FitResultKindEnum
        from easydiffraction.analysis.fit_helpers.reporting import FitResults

        a = Analysis(project=_make_project())
        results = FitResults(success=True, reduced_chi_square=2.5, fitting_time=1.5)
        results.message = 'converged'
        results.iterations = 42

        a._store_common_fit_result_projection(
            results,
            result_kind=FitResultKindEnum.DETERMINISTIC,
        )

        assert a.fit_result.result_kind.value == FitResultKindEnum.DETERMINISTIC.value
        assert a.fit_result.success.value is True
        assert a.fit_result.message.value == 'converged'
        assert a.fit_result.iterations.value == 42
        assert a.fit_result.fitting_time.value == 1.5
        assert a.fit_result.reduced_chi_square.value == 2.5
        assert a._has_persisted_fit_state() is True


# ------------------------------------------------------------------
# Pre-fit parameter capture and selection
# ------------------------------------------------------------------


class TestParameterCaptureAndSelection:
    def test_capture_fit_parameter_state_creates_rows(self):
        from easydiffraction.analysis.analysis import Analysis

        length_a = _make_parameter('length_a', 3.9)
        length_a.value = 4.1
        length_a.uncertainty = 0.05
        length_a.fit_min = 3.5
        length_a.fit_max = 4.5
        project = _make_project_with_parameters([length_a])
        a = Analysis(project=project)

        a._capture_fit_parameter_state([length_a])

        assert a._has_persisted_fit_state() is True
        assert len(a.fit_parameters) == 1
        row = a.fit_parameters[length_a.unique_name]
        assert row.start_value.value == 4.1
        assert row.start_uncertainty.value == 0.05
        assert row.fit_min.value == 3.5
        assert row.fit_max.value == 4.5

    def test_selected_parameters_dedupe_across_structures_and_experiments(self):
        from easydiffraction.analysis.analysis import Analysis

        shared = _make_parameter('scale', 1.0)
        structure_only = _make_parameter('length_a', 4.0)
        experiment_only = _make_parameter('wavelength', 1.5)

        project = _make_project_with_parameters([shared, structure_only])
        a = Analysis(project=project)

        experiment = SimpleNamespace(parameters=[shared, experiment_only])
        selected = a._selected_parameters_for_fit([experiment])

        unique_names = [param.unique_name for param in selected]
        # 'scale' appears in both but must be counted once.
        assert unique_names.count(shared.unique_name) == 1
        assert structure_only.unique_name in unique_names
        assert experiment_only.unique_name in unique_names
        assert len(selected) == 3

    def test_selected_parameters_ignores_non_parameter_descriptors(self):
        from easydiffraction.analysis.analysis import Analysis

        real = _make_parameter('scale', 1.0)
        not_a_parameter = SimpleNamespace(unique_name='descriptor')
        project = _make_project_with_parameters([real, not_a_parameter])
        a = Analysis(project=project)

        selected = a._selected_parameters_for_fit([])
        assert [param.unique_name for param in selected] == [real.unique_name]


# ------------------------------------------------------------------
# Fit-result state category selection
# ------------------------------------------------------------------


class TestFitResultStateCategories:
    def test_valid_result_kind_returns_common_categories(self):
        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.analysis.enums import FitResultKindEnum

        a = Analysis(project=_make_project())
        a.fit_result._set_result_kind(FitResultKindEnum.DETERMINISTIC.value)

        categories = a._fit_result_state_categories()
        assert a.fit_result in categories
        assert a.fit_parameter_correlations in categories

    def test_invalid_result_kind_warns_and_returns_common_only(self, monkeypatch):
        import easydiffraction.analysis.analysis as mod
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project())
        # The validating setter would reject an unknown kind and fall back,
        # so force the raw descriptor value to exercise the except branch.
        a.fit_result._result_kind._value = 'bogus-kind'
        warnings = []
        monkeypatch.setattr(mod.log, 'warning', warnings.append)

        categories = a._fit_result_state_categories()
        assert categories == [a.fit_result, a.fit_parameter_correlations]
        assert any('Unsupported fit_result.result_kind' in message for message in warnings)


# ------------------------------------------------------------------
# Restored Bayesian reduced chi-square branches
# ------------------------------------------------------------------


class TestRestoredBayesianReducedChiSquare:
    def _bayesian_analysis(self):
        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.analysis.categories.fit_result.bayesian import BayesianFitResult

        a = Analysis(project=_make_project())
        a._fit_result._parent = None
        a._fit_result = BayesianFitResult()
        a._fit_result._parent = a
        return a

    def test_finite_persisted_value_passes_through(self):
        a = self._bayesian_analysis()
        value = a._restored_bayesian_reduced_chi_square(2.5, restored_parameters=[object()])
        assert value == 2.5

    def test_missing_log_posterior_returns_none(self):
        a = self._bayesian_analysis()
        # best_log_posterior defaults to None -> cannot reconstruct.
        value = a._restored_bayesian_reduced_chi_square(
            float('nan'),
            restored_parameters=[object()],
        )
        assert value is None

    def test_nonpositive_dof_returns_none(self, monkeypatch):
        a = self._bayesian_analysis()
        a.fit_result._set_best_log_posterior(-10.0)
        # Two data points, two parameters -> dof = 0 -> None.
        monkeypatch.setattr(a, '_fit_data_point_count', lambda experiments: 2)
        value = a._restored_bayesian_reduced_chi_square(
            float('nan'),
            restored_parameters=[object(), object()],
        )
        assert value is None


# ------------------------------------------------------------------
# Restored posterior summaries and predictive datasets
# ------------------------------------------------------------------


class TestRestoredPosteriorSummariesAndPredictive:
    def _analysis_with_posterior_row(self):
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project())
        a.fit_parameters.create(
            param_unique_name='alpha',
            fit_min=0.0,
            fit_max=2.0,
            start_value=1.0,
            start_uncertainty=0.1,
        )
        row = a.fit_parameters['alpha']
        row._set_posterior_best_sample_value(1.2)
        row._set_posterior_median(1.1)
        row._set_posterior_uncertainty(0.1)
        row._set_posterior_interval_68_low(1.0)
        row._set_posterior_interval_68_high(1.2)
        row._set_posterior_interval_95_low(0.9)
        row._set_posterior_interval_95_high(1.3)
        return a

    def test_restored_posterior_summaries_uses_unique_name_when_param_missing(self):
        a = self._analysis_with_posterior_row()
        summaries = a._restored_posterior_summaries()
        assert len(summaries) == 1
        # No live parameter named 'alpha' -> display name falls back to id.
        assert summaries[0].display_name == 'alpha'

    def test_restored_posterior_samples_valid_path_returns_samples(self):
        a = self._analysis_with_posterior_row()
        samples = np.zeros((4, 2, 1), dtype=float)
        a._persisted_fit_state_sidecar = {
            'posterior': {
                'parameter_samples': samples.tolist(),
                'log_posterior': np.zeros((4, 2)).tolist(),
                'draw_index': [0, 1, 2, 3],
            }
        }
        restored = a._restored_posterior_samples()
        assert restored is not None
        assert restored.parameter_names == ['alpha']
        assert restored.parameter_samples.shape == (4, 2, 1)
        assert restored.log_posterior is not None
        assert restored.draw_index is not None

    def test_restored_predictive_summaries_builds_cache_keys(self):
        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.analysis.fit_helpers.bayesian import posterior_predictive_cache_key

        a = Analysis(project=_make_project())
        a._persisted_fit_state_sidecar = {
            'predictive_datasets': {
                'hrpt': {
                    'x_axis_name': 'two_theta',
                    'x': [1.0, 2.0],
                    'best_sample_prediction': [3.0, 4.0],
                    'lower_95': [2.5, 3.5],
                    'upper_95': [3.5, 4.5],
                    'draws': [[3.0, 3.1], [4.0, 4.1]],
                }
            }
        }
        restored = a._restored_predictive_summaries()
        assert 'hrpt' in restored
        no_draws_key = posterior_predictive_cache_key('hrpt', 'two_theta', include_draws=False)
        draws_key = posterior_predictive_cache_key('hrpt', 'two_theta', include_draws=True)
        assert no_draws_key in restored
        assert draws_key in restored
        assert np.allclose(restored['hrpt'].best_sample_prediction, [3.0, 4.0])


# ------------------------------------------------------------------
# Least-squares result projection (engine-free, array-driven)
# ------------------------------------------------------------------


class TestLeastSquaresResultProjection:
    def _powder_experiment(self, *, meas, calc, su):
        data = SimpleNamespace(
            intensity_meas=np.asarray(meas, dtype=float),
            intensity_calc=np.asarray(calc, dtype=float),
            intensity_meas_su=np.asarray(su, dtype=float),
        )
        from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum

        return SimpleNamespace(
            data=data,
            type=SimpleNamespace(sample_form=SimpleNamespace(value=SampleFormEnum.POWDER.value)),
            peak=SimpleNamespace(type=SimpleNamespace(value='gaussian')),
            background=SimpleNamespace(type=SimpleNamespace(value='chebyshev')),
            parameters=[],
        )

    def test_store_least_squares_result_projection_populates_statistics(self):
        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.analysis.fit_helpers.reporting import FitResults

        a = Analysis(project=_make_project())
        experiment = self._powder_experiment(
            meas=[10.0, 10.0, 10.0, 10.0],
            calc=[9.0, 11.0, 10.0, 10.0],
            su=[1.0, 1.0, 1.0, 1.0],
        )

        fitted = _make_parameter('scale', 1.0)
        fitted.value = 1.1
        fitted.uncertainty = 0.05
        fitted._fit_start_value = 1.0

        results = FitResults(success=True, reduced_chi_square=1.0)
        results.chi_square = 4.0
        results.message = 'converged'

        a._store_least_squares_result_projection(
            results,
            experiments=[experiment],
            fitted_parameters=[fitted],
        )

        assert a.fit_result.objective_name.value == 'chi_square'
        assert a.fit_result.objective_value.value == 4.0
        assert a.fit_result.n_data_points.value == 4
        assert a.fit_result.n_free_parameters.value == 1
        assert a.fit_result.degrees_of_freedom.value == 3
        assert a.fit_result.covariance_available.value is False
        assert a.fit_result.r_factor_all.value is not None
        # Powder profile R factors are populated for powder fits.
        assert a.fit_result.prof_r_factor.value is not None
        assert a.fit_result.profile_function.value == 'gaussian'
        assert a.fit_result.background_function.value == 'chebyshev'

    def test_store_least_squares_with_covariance_records_correlations(self):
        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.analysis.fit_helpers.reporting import FitResults

        a = Analysis(project=_make_project())
        experiment = self._powder_experiment(
            meas=[10.0, 10.0],
            calc=[10.0, 10.0],
            su=[1.0, 1.0],
        )

        p1 = _make_parameter('p1', 1.0)
        p1.value = 1.0
        p1.uncertainty = 0.1
        p1._fit_start_value = 1.0
        p2 = _make_parameter('p2', 2.0)
        p2.value = 2.0
        p2.uncertainty = 0.2
        p2._fit_start_value = 2.0

        covar = np.asarray([[0.01, 0.005], [0.005, 0.04]], dtype=float)
        results = FitResults(success=True, engine_result=SimpleNamespace(covar=covar))
        results.chi_square = 0.0
        results.message = 'ok'

        a._store_least_squares_result_projection(
            results,
            experiments=[experiment],
            fitted_parameters=[p1, p2],
        )

        assert a.fit_result.covariance_available.value is True
        assert a.fit_result.correlation_available.value is True
        assert len(a.fit_parameter_correlations) == 1


# ------------------------------------------------------------------
# Display: how-to-access and CIF UID tables
# ------------------------------------------------------------------


def _identity_param(*, datablock, category, entry, name):
    return SimpleNamespace(
        name=name,
        value=1.0,
        _identity=SimpleNamespace(
            datablock_entry_name=datablock,
            category_code=category,
            category_entry_name=entry,
        ),
        _cif_handler=SimpleNamespace(uid=f'{category}_{name}_uid'),
    )


class TestDisplayAccessTables:
    def test_how_to_access_parameters_warns_when_empty(self, capsys):
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project())
        a.display.how_to_access_parameters()
        out = capsys.readouterr().out
        assert 'No parameters found' in out

    def test_how_to_access_parameters_builds_code_paths(self, capsys, monkeypatch):
        import easydiffraction.analysis.analysis as mod
        from easydiffraction.analysis.analysis import Analysis

        structure_param = _identity_param(
            datablock='lbco', category='cell', entry='', name='length_a'
        )
        experiment_param = _identity_param(
            datablock='hrpt', category='atom_site', entry='Ba', name='fract_x'
        )
        project = _make_project_with_parameters([structure_param], [experiment_param])
        a = Analysis(project=project)

        captured = {}
        monkeypatch.setattr(mod, 'render_table', lambda **kwargs: captured.update(kwargs))
        a.display.how_to_access_parameters()

        out = capsys.readouterr().out
        assert 'How to access parameters' in out
        access_codes = [row[-1] for row in captured['columns_data']]
        assert "proj.structures['lbco'].cell.length_a" in access_codes
        # Category-entry name is rendered for looped (collection) categories.
        assert "proj.experiments['hrpt'].atom_site['Ba'].fract_x" in access_codes

    def test_parameter_cif_uids_warns_when_empty(self, capsys):
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project())
        a.display.parameter_cif_uids()
        out = capsys.readouterr().out
        assert 'No parameters found' in out

    def test_parameter_cif_uids_lists_handler_uids(self, capsys, monkeypatch):
        import easydiffraction.analysis.analysis as mod
        from easydiffraction.analysis.analysis import Analysis

        structure_param = _identity_param(
            datablock='lbco', category='cell', entry='', name='length_a'
        )
        project = _make_project_with_parameters([structure_param])
        a = Analysis(project=project)

        captured = {}
        monkeypatch.setattr(mod, 'render_table', lambda **kwargs: captured.update(kwargs))
        a.display.parameter_cif_uids()

        out = capsys.readouterr().out
        assert 'CIF unique identifiers' in out
        uids = [row[-1] for row in captured['columns_data']]
        assert 'cell_length_a_uid' in uids


# ------------------------------------------------------------------
# Restoring live parameter state from persisted fit rows
# ------------------------------------------------------------------


class TestRestoreLiveParameterState:
    def _analysis_with_persisted_param(self, parameter):
        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.core.posterior import PosteriorParameterSummary

        project = _make_project_with_parameters([parameter])
        a = Analysis(project=project)
        a.fit_parameters.create(
            param_unique_name=parameter.unique_name,
            fit_min=3.5,
            fit_max=4.5,
            fit_bounds_uncertainty_multiplier=4.0,
            start_value=3.90,
            start_uncertainty=0.02,
        )
        summary = PosteriorParameterSummary(
            unique_name=parameter.unique_name,
            display_name=parameter.name,
            best_sample_value=4.0,
            median=4.0,
            standard_deviation=0.03,
            interval_68=(3.97, 4.03),
            interval_95=(3.94, 4.06),
            ess_bulk=100.0,
            r_hat=1.01,
        )
        a.fit_parameters[parameter.unique_name]._set_posterior_summary(summary)
        return a

    def test_restore_live_parameter_state_applies_bounds_and_posterior(self):
        parameter = _make_parameter('length_a', 3.90)
        a = self._analysis_with_persisted_param(parameter)
        param_map = a._live_parameter_map()

        a._restore_live_parameter_state(param_map)

        assert parameter.fit_min == 3.5
        assert parameter.fit_max == 4.5
        assert parameter._fit_start_value == 3.90
        assert parameter._fit_start_uncertainty == 0.02
        # The posterior standard deviation is restored onto the uncertainty.
        assert np.isclose(parameter.uncertainty, 0.03)
        assert parameter.posterior is not None

    def test_restore_bounds_warns_for_unknown_parameter(self, monkeypatch):
        import easydiffraction.analysis.analysis as mod
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project_with_parameters([]))
        a.fit_parameters.create(
            param_unique_name='ghost',
            fit_min=0.0,
            fit_max=1.0,
            start_value=0.5,
        )
        warnings = []
        monkeypatch.setattr(mod.log, 'warning', warnings.append)

        a._restore_live_parameter_bounds_and_anchors({})
        assert any('unknown parameter' in message for message in warnings)

    def test_restore_posterior_skips_unknown_parameter(self):
        parameter = _make_parameter('length_a', 3.90)
        a = self._analysis_with_persisted_param(parameter)
        # An empty param_map exercises the parameter-is-None branch.
        a._restore_live_parameter_posterior({})
        # No exception and live parameter is untouched.
        assert parameter.posterior is None

    def test_ordered_restored_parameter_names_follows_row_order(self):
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project_with_parameters([]))
        for name in ('beta', 'alpha'):
            a.fit_parameters.create(
                param_unique_name=name,
                fit_min=0.0,
                fit_max=1.0,
                start_value=0.5,
            )
        assert a._ordered_restored_parameter_names() == ['beta', 'alpha']

    def test_restored_fit_parameters_filters_to_live_parameters(self):
        parameter = _make_parameter('length_a', 3.90)
        a = self._analysis_with_persisted_param(parameter)
        # Add a persisted row with no matching live parameter.
        a.fit_parameters.create(
            param_unique_name='ghost',
            fit_min=0.0,
            fit_max=1.0,
            start_value=0.5,
        )
        param_map = a._live_parameter_map()
        restored = a._restored_fit_parameters(param_map)
        assert [p.unique_name for p in restored] == [parameter.unique_name]


# ------------------------------------------------------------------
# Deterministic fit-result restore from projection
# ------------------------------------------------------------------


class TestDeterministicRestoreFromProjection:
    def test_restore_returns_none_without_persisted_state(self):
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project_with_parameters([]))
        assert a._restore_fit_results_from_projection() is None

    def test_restore_rebuilds_deterministic_results(self):
        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.analysis.enums import FitResultKindEnum

        parameter = _make_parameter('length_a', 3.90)
        a = Analysis(project=_make_project_with_parameters([parameter]))
        a.fit_parameters.create(
            param_unique_name=parameter.unique_name,
            fit_min=3.5,
            fit_max=4.5,
            start_value=3.90,
            start_uncertainty=0.02,
        )

        fit_result = a.fit_result
        fit_result._set_result_kind(FitResultKindEnum.DETERMINISTIC.value)
        fit_result._set_success(value=True)
        fit_result._set_message('converged')
        fit_result._set_iterations(17)
        fit_result._set_fitting_time(2.5)
        fit_result._set_reduced_chi_square(1.4)
        fit_result._set_objective_name('chi_square')
        fit_result._set_objective_value(42.0)
        fit_result._set_n_data_points(100)
        fit_result._set_n_parameters(3)
        fit_result._set_n_free_parameters(1)
        fit_result._set_degrees_of_freedom(99)
        fit_result._set_covariance_available(value=True)
        fit_result._set_correlation_available(value=False)
        fit_result._set_exit_reason('done')
        a._set_has_persisted_fit_state(value=True)

        restored = a._restore_fit_results_from_projection()

        assert restored is not None
        assert restored.success is True
        assert restored.message == 'converged'
        assert restored.iterations == 17
        assert restored.reduced_chi_square == 1.4
        assert restored.optimizer_name == 'lmfit (leastsq)'
        assert restored.method_name == 'leastsq'
        assert restored.n_data_points == 100
        assert restored.degrees_of_freedom == 99
        assert restored.chi_square == 42.0
        # The restored result is also cached on the analysis object.
        assert a.fit_results is restored

    def test_fit_results_property_restores_on_first_access(self):
        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.analysis.enums import FitResultKindEnum

        parameter = _make_parameter('length_a', 3.90)
        a = Analysis(project=_make_project_with_parameters([parameter]))
        a.fit_parameters.create(
            param_unique_name=parameter.unique_name,
            fit_min=3.5,
            fit_max=4.5,
            start_value=3.90,
        )
        a.fit_result._set_result_kind(FitResultKindEnum.DETERMINISTIC.value)
        a.fit_result._set_success(value=True)
        a._set_has_persisted_fit_state(value=True)
        a._fit_results = None

        # Accessing the property lazily restores the projection.
        assert a.fit_results is not None


# ------------------------------------------------------------------
# Bayesian fit-result restore from projection
# ------------------------------------------------------------------


class TestBayesianRestoreFromProjection:
    def test_restore_rebuilds_bayesian_results(self):
        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.analysis.enums import FitResultKindEnum

        parameter = _make_parameter('alpha', 1.0)
        a = Analysis(project=_make_project_with_parameters([parameter]))
        a.minimizer.type = 'bumps (dream)'

        a.fit_parameters.create(
            param_unique_name=parameter.unique_name,
            fit_min=0.0,
            fit_max=2.0,
            start_value=1.0,
            start_uncertainty=0.1,
        )
        row = a.fit_parameters[parameter.unique_name]
        row._set_posterior_best_sample_value(1.2)
        row._set_posterior_median(1.1)
        row._set_posterior_uncertainty(0.1)
        row._set_posterior_interval_68_low(1.0)
        row._set_posterior_interval_68_high(1.2)
        row._set_posterior_interval_95_low(0.9)
        row._set_posterior_interval_95_high(1.3)

        fit_result = a.fit_result
        fit_result._set_result_kind(FitResultKindEnum.BAYESIAN.value)
        fit_result._set_success(value=True)
        fit_result._set_message('sampled')
        fit_result._set_iterations(3000)
        fit_result._set_fitting_time(12.0)
        fit_result._set_reduced_chi_square(1.1)
        fit_result._set_point_estimate_name('median')
        fit_result._set_sampler_completed(value=True)
        fit_result._set_best_log_posterior(-50.0)
        fit_result._set_credible_interval_inner(0.68)
        fit_result._set_credible_interval_outer(0.95)
        fit_result._set_gelman_rubin_max(1.001)
        fit_result._set_effective_sample_size_min(8000.0)
        a._set_has_persisted_fit_state(value=True)

        a._persisted_fit_state_sidecar = {
            'posterior': {
                'parameter_samples': np.zeros((4, 2, 1)).tolist(),
                'log_posterior': None,
                'draw_index': None,
            }
        }

        restored = a._restore_fit_results_from_projection()

        assert restored is not None
        assert restored.success is True
        assert restored.message == 'sampled'
        assert restored.sampler_name == 'dream'
        assert restored.point_estimate_name == 'median'
        assert restored.reduced_chi_square == 1.1
        assert restored.convergence_diagnostics['converged'] is True
        assert a.fit_results is restored


# ------------------------------------------------------------------
# Restored Bayesian sampler settings (dream / non-emcee branch)
# ------------------------------------------------------------------


class TestRestoredDreamSamplerSettings:
    def test_dream_branch_builds_settings(self):
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project())
        a.minimizer.type = 'bumps (dream)'

        settings = a._restored_bayesian_sampler_settings(
            {
                'steps': 5000,
                'burn': 1000,
                'thin': 2,
                'pop': 8,
                'parallel': 0,
                'init': 'lhs',
            },
            random_seed=7,
            n_parameters=3,
        )

        assert settings['steps'] == 5000
        assert settings['burn'] == 1000
        assert settings['thin'] == 2
        assert settings['pop'] == 8
        assert settings['parallel'] == 0
        assert settings['init'] == 'lhs'
        assert settings['random_seed'] == 7
        # samples = steps * pop * n_parameters
        assert settings['samples'] == 5000 * 8 * 3


# ------------------------------------------------------------------
# Posterior plot-cache projection: empty / invalid sample paths
# ------------------------------------------------------------------


class TestPosteriorPlotCacheGuards:
    def test_no_samples_resets_caches(self):
        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.analysis.fit_helpers.bayesian import BayesianFitResults

        a = Analysis(project=_make_project())
        results = BayesianFitResults(success=True, posterior_samples=None)

        a._store_posterior_plot_cache_projection(results)

        assert results.posterior_distribution_caches == {}
        assert results.posterior_pair_caches == {}
        assert a._persisted_fit_state_sidecar['distribution_caches'] == {}
        assert a._persisted_fit_state_sidecar['pair_caches'] == {}
        assert a._persisted_fit_state_sidecar['predictive_datasets'] == {}

    def test_invalid_flattened_shape_resets_caches(self):
        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.analysis.fit_helpers.bayesian import BayesianFitResults

        a = Analysis(project=_make_project())
        # A non-2-D flattened array trips the shape guard, resetting caches
        # before any plotter access (the project here has no plotter).
        fake_samples = SimpleNamespace(
            parameter_names=['alpha'],
            flattened=lambda: np.asarray([1.0, 2.0, 3.0], dtype=float),
        )
        results = BayesianFitResults(success=True, posterior_samples=fake_samples)

        a._store_posterior_plot_cache_projection(results)

        assert a._persisted_fit_state_sidecar['distribution_caches'] == {}
        assert a._persisted_fit_state_sidecar['pair_caches'] == {}
        assert a._persisted_fit_state_sidecar['predictive_datasets'] == {}


# ------------------------------------------------------------------
# Posterior pair-cache projection (multi-parameter)
# ------------------------------------------------------------------


class _PairPlotter:
    @staticmethod
    def _posterior_parameter_bounds(*, fit_results, parameter_name):
        del fit_results, parameter_name
        return 0.0, 1.0

    @staticmethod
    def _posterior_density_curve(values, *, lower_bound, upper_bound):
        del values
        return (
            np.asarray([lower_bound, upper_bound], dtype=float),
            np.asarray([0.25, 0.75], dtype=float),
        )

    @staticmethod
    def _thin_posterior_samples(samples, *, max_points):
        del max_points
        return np.asarray(samples, dtype=float)

    @staticmethod
    def _posterior_pair_density_max_points(n_parameters):
        del n_parameters
        return 1000

    @staticmethod
    def _posterior_pair_contour_grid_size(n_parameters):
        del n_parameters
        return 4

    @staticmethod
    def _posterior_pair_bounds(
        *, fit_results, x_parameter_name, y_parameter_name, x_values, y_values
    ):
        del fit_results, x_parameter_name, y_parameter_name, x_values, y_values
        return (0.0, 1.0), (0.0, 1.0)

    @staticmethod
    def _posterior_pair_density_surface(*, x_values, y_values, x_bounds, y_bounds, grid_size):
        del x_values, y_values, x_bounds, y_bounds
        x_grid = np.linspace(0.0, 1.0, grid_size)
        y_grid = np.linspace(0.0, 1.0, grid_size)
        density = np.ones((grid_size, grid_size), dtype=float)
        return x_grid, y_grid, density

    @staticmethod
    def _resolve_x_axis(experiment_type, _axis_name):
        del experiment_type
        return np.asarray([1.0, 2.0], dtype=float), 'two_theta', None, None, None

    @staticmethod
    def _build_posterior_predictive_summary(
        *, fit_results, experiment, expt_name, x_axis, include_draws
    ):
        del fit_results, experiment, x_axis, include_draws
        from easydiffraction.analysis.fit_helpers.bayesian import PosteriorPredictiveSummary

        return PosteriorPredictiveSummary(
            experiment_name=expt_name,
            x_axis_name='two_theta',
            x=np.asarray([1.0, 2.0], dtype=float),
            best_sample_prediction=np.asarray([3.0, 4.0], dtype=float),
        )


class TestPosteriorPairCacheProjection:
    def _bayesian_results(self):
        from easydiffraction.analysis.fit_helpers.bayesian import BayesianFitResults
        from easydiffraction.analysis.fit_helpers.bayesian import PosteriorSamples

        return BayesianFitResults(
            success=True,
            posterior_samples=PosteriorSamples(
                parameter_names=['beta', 'alpha'],
                parameter_samples=np.asarray(
                    [[[1.0, 2.0]], [[1.2, 2.2]], [[1.1, 2.1]]],
                    dtype=float,
                ),
            ),
            posterior_parameter_summaries=[],
            posterior_predictive={},
            sampler_settings={},
            convergence_diagnostics={},
        )

    def test_pair_cache_orders_names_and_stores_contours(self):
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project())
        results = self._bayesian_results()
        flattened = np.asarray(results.posterior_samples.flattened(), dtype=float)

        payload = a._store_posterior_pair_cache_projection(
            plotter=_PairPlotter(),
            results=results,
            flattened_samples=flattened,
            parameter_names=['beta', 'alpha'],
        )

        assert payload
        pair = payload['1']
        # Names are ordered alphabetically for the pair (alpha before beta).
        assert pair['param_unique_name_x'] == 'alpha'
        assert pair['param_unique_name_y'] == 'beta'
        assert pair['contour_levels'].size > 0

    def test_pair_cache_single_parameter_is_empty(self):
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project())
        results = self._bayesian_results()
        flattened = np.asarray([[1.0], [1.2]], dtype=float)

        payload = a._store_posterior_pair_cache_projection(
            plotter=_PairPlotter(),
            results=results,
            flattened_samples=flattened,
            parameter_names=['alpha'],
        )
        assert payload == {}

    def test_one_pair_returns_none_when_surface_missing(self):
        from easydiffraction.analysis.analysis import Analysis

        class NoSurfacePlotter(_PairPlotter):
            @staticmethod
            def _posterior_pair_density_surface(
                *, x_values, y_values, x_bounds, y_bounds, grid_size
            ) -> None:
                del x_values, y_values, x_bounds, y_bounds, grid_size

        a = Analysis(project=_make_project())
        results = self._bayesian_results()
        density_samples = np.asarray([[1.0, 2.0], [1.2, 2.2]], dtype=float)

        outcome = a._store_one_posterior_pair_cache_projection(
            plotter=NoSurfacePlotter(),
            results=results,
            density_samples=density_samples,
            pair_metadata=(0, 1, 'alpha', 'beta'),
            contour_grid_size=4,
            pair_id='1',
        )
        assert outcome is None


# ------------------------------------------------------------------
# Posterior samples sidecar projection
# ------------------------------------------------------------------


class TestPosteriorSamplesSidecar:
    def test_no_samples_stores_empty_posterior(self):
        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.analysis.fit_helpers.bayesian import BayesianFitResults

        a = Analysis(project=_make_project())
        results = BayesianFitResults(success=True, posterior_samples=None)
        a._store_posterior_samples_sidecar_projection(results)
        assert a._persisted_fit_state_sidecar['posterior'] == {}

    def test_samples_stored_with_optional_arrays(self):
        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.analysis.fit_helpers.bayesian import BayesianFitResults
        from easydiffraction.analysis.fit_helpers.bayesian import PosteriorSamples

        a = Analysis(project=_make_project())
        samples = PosteriorSamples(
            parameter_names=['alpha'],
            parameter_samples=np.asarray([[[1.0]], [[1.2]]], dtype=float),
            log_posterior=np.asarray([[-1.0], [-1.1]], dtype=float),
            draw_index=np.asarray([0, 1]),
        )
        results = BayesianFitResults(success=True, posterior_samples=samples)
        a._store_posterior_samples_sidecar_projection(results)

        stored = a._persisted_fit_state_sidecar['posterior']
        assert stored['parameter_samples'].shape == (2, 1, 1)
        assert stored['log_posterior'] is not None
        assert stored['draw_index'] is not None


# ------------------------------------------------------------------
# Fit-result projection dispatch (Bayesian vs deterministic)
# ------------------------------------------------------------------


class TestStoreFitResultProjectionDispatch:
    def test_bayesian_results_route_to_posterior_projection(self, monkeypatch):
        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.analysis.enums import FitResultKindEnum
        from easydiffraction.analysis.fit_helpers.bayesian import BayesianFitResults

        a = Analysis(project=_make_project())
        a.minimizer.type = 'bumps (dream)'
        calls = []
        monkeypatch.setattr(a, '_store_posterior_fit_projection', calls.append)

        results = BayesianFitResults(
            success=True,
            convergence_diagnostics={},
            sampler_settings={},
            posterior_samples=None,
            posterior_parameter_summaries=[],
        )
        a._store_fit_result_projection(results, experiments=[], fitted_parameters=[])

        assert a.fit_result.result_kind.value == FitResultKindEnum.BAYESIAN.value
        assert calls == [results]

    def test_deterministic_results_route_to_least_squares_projection(self, monkeypatch):
        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.analysis.enums import FitResultKindEnum
        from easydiffraction.analysis.fit_helpers.reporting import FitResults

        a = Analysis(project=_make_project())
        calls = []
        monkeypatch.setattr(
            a,
            '_store_least_squares_result_projection',
            lambda results, *, experiments, fitted_parameters: calls.append((
                results,
                experiments,
                fitted_parameters,
            )),
        )

        results = FitResults(success=True, reduced_chi_square=1.0)
        results.message = 'ok'
        a._store_fit_result_projection(results, experiments=['e'], fitted_parameters=['p'])

        assert a.fit_result.result_kind.value == FitResultKindEnum.DETERMINISTIC.value
        assert calls == [(results, ['e'], ['p'])]


# ------------------------------------------------------------------
# Posterior fit projection: live-parameter + correlation wiring
# ------------------------------------------------------------------


class TestPosteriorFitProjectionWiring:
    def test_updates_live_parameter_and_stores_correlations(self):
        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.analysis.categories.fit_result.bayesian import BayesianFitResult
        from easydiffraction.analysis.fit_helpers.bayesian import BayesianFitResults
        from easydiffraction.analysis.fit_helpers.bayesian import PosteriorSamples
        from easydiffraction.core.posterior import PosteriorParameterSummary

        alpha = _make_parameter('alpha', 1.0)
        beta = _make_parameter('beta', 2.0)
        project = SimpleNamespace(
            experiments=SimpleNamespace(names=[]),
            structures=object(),
            rendering_plot=SimpleNamespace(plotter=_PairPlotter()),
            _varname='proj',
        )
        a = Analysis(project=project)
        a._fit_result._parent = None
        a._fit_result = BayesianFitResult()
        a._fit_result._parent = a

        for name in (alpha.unique_name, beta.unique_name):
            a.fit_parameters.create(
                param_unique_name=name,
                fit_min=0.0,
                fit_max=3.0,
                start_value=1.0,
            )

        summaries = [
            PosteriorParameterSummary(
                unique_name=alpha.unique_name,
                display_name='alpha',
                best_sample_value=1.1,
                median=1.1,
                standard_deviation=0.1,
                interval_68=(1.0, 1.2),
                interval_95=(0.9, 1.3),
            ),
            PosteriorParameterSummary(
                unique_name=beta.unique_name,
                display_name='beta',
                best_sample_value=2.1,
                median=2.1,
                standard_deviation=0.1,
                interval_68=(2.0, 2.2),
                interval_95=(1.9, 2.3),
            ),
        ]
        results = BayesianFitResults(
            success=True,
            parameters=[alpha, beta],
            convergence_diagnostics={},
            sampler_settings={'random_seed': 3},
            posterior_parameter_summaries=summaries,
            posterior_samples=PosteriorSamples(
                parameter_names=[alpha.unique_name, beta.unique_name],
                parameter_samples=np.asarray(
                    [[[1.0, 2.0]], [[1.2, 2.3]], [[1.1, 2.1]]],
                    dtype=float,
                ),
            ),
            posterior_predictive={},
        )

        a._store_posterior_fit_projection(results)

        # The live parameters receive the posterior summaries.
        assert alpha.posterior is not None
        assert beta.posterior is not None
        # Multi-parameter posterior samples produce a correlation row.
        assert len(a.fit_parameter_correlations) >= 1


# ------------------------------------------------------------------
# Fit-run preparation guards and dispatch
# ------------------------------------------------------------------


def _fit_project(*, structures, experiments, path=None, verbosity_value='silent'):
    return SimpleNamespace(
        structures=structures,
        experiments=experiments,
        info=SimpleNamespace(path=path),
        verbosity=SimpleNamespace(fit=SimpleNamespace(value=verbosity_value)),
        _varname='proj',
    )


class TestPrepareFitRun:
    def test_no_structures_warns_and_returns_none(self, monkeypatch):
        import easydiffraction.analysis.analysis as mod
        from easydiffraction.analysis.analysis import Analysis

        project = _fit_project(structures=[], experiments=['e'])
        a = Analysis(project=project)
        warnings = []
        monkeypatch.setattr(mod.log, 'warning', warnings.append)

        assert a._prepare_fit_run() is None
        assert any('No structures found' in message for message in warnings)

    def test_no_experiments_warns_and_returns_none(self, monkeypatch):
        import easydiffraction.analysis.analysis as mod
        from easydiffraction.analysis.analysis import Analysis

        project = _fit_project(structures=['s'], experiments=[])
        a = Analysis(project=project)
        warnings = []
        monkeypatch.setattr(mod.log, 'warning', warnings.append)

        assert a._prepare_fit_run() is None
        assert any('No experiments found' in message for message in warnings)

    def test_prepared_inputs_sync_engine_and_update_categories(self, monkeypatch):
        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.utils.enums import VerbosityEnum

        project = _fit_project(structures=['s'], experiments=['e'])
        a = Analysis(project=project)
        events = []
        monkeypatch.setattr(
            a, '_prepare_results_sidecar_for_new_fit', lambda: events.append('sidecar')
        )
        monkeypatch.setattr(
            a, '_sync_engine_from_minimizer_category', lambda: events.append('sync')
        )
        monkeypatch.setattr(a, '_update_categories', lambda: events.append('update'))

        verb, structures, experiments = a._prepare_fit_run()
        assert verb is VerbosityEnum.SILENT
        assert structures == ['s']
        assert experiments == ['e']
        assert events == ['sidecar', 'sync', 'update']

    def test_resume_skips_sidecar_preparation(self, monkeypatch):
        from easydiffraction.analysis.analysis import Analysis

        project = _fit_project(structures=['s'], experiments=['e'])
        a = Analysis(project=project)
        events = []
        monkeypatch.setattr(
            a, '_prepare_results_sidecar_for_new_fit', lambda: events.append('sidecar')
        )
        monkeypatch.setattr(a, '_sync_engine_from_minimizer_category', lambda: None)
        monkeypatch.setattr(a, '_update_categories', lambda: None)

        a._prepare_fit_run(resume=True)
        assert 'sidecar' not in events


class TestRunSingleAndJoint:
    def test_run_single_aborts_when_preparation_fails(self, monkeypatch):
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project())
        monkeypatch.setattr(a, '_prepare_fit_run', lambda *, resume=False: None)
        called = []
        monkeypatch.setattr(a, '_fit_single', lambda *a_, **k_: called.append(True))

        a._run_single()
        assert called == []

    def test_run_single_invokes_fit_and_stamps_provenance(self, monkeypatch, tmp_path):
        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.utils.enums import VerbosityEnum

        project = _fit_project(structures=['s'], experiments=['e'], path=tmp_path)
        project.save_calls = 0
        project.save = lambda: setattr(project, 'save_calls', project.save_calls + 1)
        a = Analysis(project=project)

        captured = {}
        monkeypatch.setattr(
            a,
            '_prepare_fit_run',
            lambda *, resume=False: (VerbosityEnum.SILENT, ['s'], ['e']),
        )
        monkeypatch.setattr(
            a,
            '_fit_single',
            lambda verb, structures, experiments, *, fit_options: captured.update(
                resume=fit_options.resume, extra_steps=fit_options.extra_steps
            ),
        )
        monkeypatch.setattr(a, '_stamp_software_provenance', lambda: captured.update(stamped=True))

        a._run_single(resume=True, extra_steps=5)

        assert captured == {'resume': True, 'extra_steps': 5, 'stamped': True}
        assert project.save_calls == 1

    def test_run_joint_rejects_resume(self):
        import pytest

        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project())
        with pytest.raises(ValueError, match='single fit mode only'):
            a._run_joint(resume=True)

    def test_run_joint_aborts_when_preparation_fails(self, monkeypatch):
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project())
        monkeypatch.setattr(a, '_prepare_fit_run', lambda *, resume=False: None)
        called = []
        monkeypatch.setattr(a, '_fit_joint', lambda *a_, **k_: called.append(True))

        a._run_joint()
        assert called == []


# ------------------------------------------------------------------
# Joint fitting execution
# ------------------------------------------------------------------


class TestFitJoint:
    def test_fit_joint_rejects_resume(self):
        import pytest

        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.analysis.fitting import FitterFitOptions
        from easydiffraction.utils.enums import VerbosityEnum

        a = Analysis(project=_make_project())
        with pytest.raises(ValueError, match='single fit mode only'):
            a._fit_joint(
                VerbosityEnum.SILENT,
                object(),
                SimpleNamespace(names=[], values=list),
                fit_options=FitterFitOptions(resume=True),
            )

    def test_fit_joint_auto_populates_weights_and_calls_fitter(self, monkeypatch):
        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.analysis.fitting import FitterFitOptions
        from easydiffraction.utils.enums import VerbosityEnum

        class Experiments:
            names = ['e1', 'e2']

            def values(self):
                return ['exp1', 'exp2']

        a = Analysis(project=_make_project())
        captured = {}

        def fake_fit(structures, experiments_list, *, weights, analysis, verbosity, options):
            del structures, analysis, verbosity, options
            captured['experiments'] = experiments_list
            captured['weights'] = weights

        monkeypatch.setattr(a.fitter, 'fit', fake_fit)
        a.fitter.results = SimpleNamespace(success=True)

        a._fit_joint(
            VerbosityEnum.SILENT,
            object(),
            Experiments(),
            fit_options=FitterFitOptions(),
        )

        assert captured['experiments'] == ['exp1', 'exp2']
        # Auto-populated default weight is 0.5 for each experiment.
        assert np.allclose(captured['weights'], [0.5, 0.5])
        assert a.fit_results is a.fitter.results
        ids = sorted(item.experiment_id.value for item in a.joint_fit)
        assert ids == ['e1', 'e2']


# ------------------------------------------------------------------
# Short-mode summary table and constraint application
# ------------------------------------------------------------------


class TestShortTableAndUpdateCategories:
    def test_short_table_formats_chi2_and_status(self, monkeypatch):
        import easydiffraction.analysis.analysis as mod
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project())
        a.fitter.minimizer = SimpleNamespace(tracker=SimpleNamespace(best_iteration=9))
        captured = {}
        monkeypatch.setattr(mod, 'render_table', lambda **kwargs: captured.update(kwargs))

        short_rows = []
        results = SimpleNamespace(reduced_chi_square=1.234, success=True)
        a._fit_single_update_short_table(short_rows, 'e1', results, display_handle=None)

        assert short_rows == [['e1', '1.23', '9', '✅']]
        assert captured['columns_headers'] == ['experiment', 'χ²', 'iterations', 'status']

    def test_short_table_handles_missing_chi2_and_failure(self, monkeypatch):
        import easydiffraction.analysis.analysis as mod
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project())
        a.fitter.minimizer = SimpleNamespace(tracker=SimpleNamespace(best_iteration=None))
        monkeypatch.setattr(mod, 'render_table', lambda **kwargs: None)

        short_rows = []
        results = SimpleNamespace(reduced_chi_square=None, success=False)
        a._fit_single_update_short_table(short_rows, 'e2', results, display_handle=None)

        assert short_rows == [['e2', '—', '0', '❌']]

    def test_update_categories_applies_enabled_constraints(self, monkeypatch):
        from easydiffraction.analysis.analysis import Analysis
        from easydiffraction.core.category_owner import CategoryOwner

        a = Analysis(project=_make_project())
        a.constraints._items = [SimpleNamespace(id=SimpleNamespace(value='c1'))]
        a.constraints.enable()

        applied = []
        monkeypatch.setattr(a._constraints_handler, 'set_aliases', lambda aliases: None)
        monkeypatch.setattr(a._constraints_handler, 'set_constraints', lambda constraints: None)
        monkeypatch.setattr(a._constraints_handler, 'apply', lambda: applied.append(True))
        # Avoid touching the real super()._update_categories machinery.
        monkeypatch.setattr(
            CategoryOwner,
            '_update_categories',
            lambda self, *, called_by_minimizer=False: None,
        )

        a._update_categories()
        assert applied == [True]
