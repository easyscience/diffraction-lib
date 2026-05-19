# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import re

import numpy as np
import pytest

ANSI_ESCAPE_RE = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')


def _unstyled_output(text: str) -> str:
    return ANSI_ESCAPE_RE.sub('', text)


class Identity:
    def __init__(self) -> None:
        self.datablock_entry_name = 'db'
        self.category_code = 'cat'
        self.category_entry_name = 'entry'


class Param:
    def __init__(self, unique_name: str, start: float, value: float, uncertainty: float) -> None:
        self._identity = Identity()
        self._fit_start_value = start
        self.unique_name = unique_name
        self.name = unique_name
        self.value = value
        self.uncertainty = uncertainty
        self.units = 'arb'


def test_posterior_samples_flatten_and_to_arviz():
    from easydiffraction.analysis.fit_helpers.bayesian import PosteriorSamples

    posterior_samples = PosteriorSamples(
        parameter_names=['a', 'b'],
        parameter_samples=np.array(
            [
                [[1.0, 10.0], [2.0, 20.0]],
                [[3.0, 30.0], [4.0, 40.0]],
            ],
            dtype=float,
        ),
        log_posterior=np.array([[0.1, 0.2], [0.3, 0.4]], dtype=float),
    )

    flattened = posterior_samples.flattened()
    inference_data = posterior_samples.to_arviz()

    assert flattened.shape == (4, 2)
    np.testing.assert_allclose(flattened[:, 0], np.array([1.0, 2.0, 3.0, 4.0]))
    np.testing.assert_allclose(flattened[:, 1], np.array([10.0, 20.0, 30.0, 40.0]))
    assert set(inference_data.posterior.data_vars) == {'a', 'b'}
    assert inference_data.posterior['a'].shape == (2, 2)
    assert inference_data.sample_stats['lp'].shape == (2, 2)


def test_posterior_samples_to_arviz_validates_shapes():
    from easydiffraction.analysis.fit_helpers.bayesian import PosteriorSamples

    posterior_samples = PosteriorSamples(
        parameter_names=['a'],
        parameter_samples=np.array([1.0, 2.0]),
    )

    with pytest.raises(
        ValueError,
        match=r'Posterior sample array must have shape \(n_draws, n_chains, n_parameters\)\.',
    ):
        posterior_samples.to_arviz()


def test_posterior_samples_to_arviz_validates_name_and_log_posterior_lengths():
    from easydiffraction.analysis.fit_helpers.bayesian import PosteriorSamples

    wrong_names = PosteriorSamples(
        parameter_names=['a'],
        parameter_samples=np.ones((2, 2, 2), dtype=float),
    )
    with pytest.raises(
        ValueError,
        match=r'Posterior sample array does not match the parameter name list length\.',
    ):
        wrong_names.to_arviz()

    wrong_log_posterior = PosteriorSamples(
        parameter_names=['a'],
        parameter_samples=np.ones((2, 2, 1), dtype=float),
        log_posterior=np.ones((3, 2), dtype=float),
    )
    with pytest.raises(
        ValueError,
        match=r'Log-posterior array must match the first two posterior sample axes\.',
    ):
        wrong_log_posterior.to_arviz()


def test_compute_convergence_diagnostics_treats_non_finite_values_as_not_converged(
    monkeypatch,
):
    from easydiffraction.analysis.fit_helpers.bayesian import PosteriorSamples
    from easydiffraction.analysis.fit_helpers.bayesian import compute_convergence_diagnostics

    posterior_samples = PosteriorSamples(
        parameter_names=['a'],
        parameter_samples=np.ones((4, 2, 1), dtype=float),
    )

    fake_dataset = type('FakeDataset', (), {'data_vars': {'a': np.array([np.nan], dtype=float)}})

    monkeypatch.setattr(
        'easydiffraction.analysis.fit_helpers.bayesian.az.rhat',
        lambda inference_data: fake_dataset,
    )
    monkeypatch.setattr(
        'easydiffraction.analysis.fit_helpers.bayesian.az.ess',
        lambda inference_data, method='bulk': type(
            'FakeDataset', (), {'data_vars': {'a': np.array([4000.0], dtype=float)}}
        ),
    )

    diagnostics = compute_convergence_diagnostics(posterior_samples)

    assert diagnostics['converged'] is False
    assert diagnostics['r_hat_by_parameter'] == {'a': None}
    assert diagnostics['ess_bulk_by_parameter'] == {'a': 4000.0}
    assert diagnostics['max_r_hat'] is None
    assert diagnostics['min_ess_bulk'] == pytest.approx(4000.0)


def test_summarize_posterior_parameters_preserves_order_and_display_names():
    from easydiffraction.analysis.fit_helpers.bayesian import PosteriorSamples
    from easydiffraction.analysis.fit_helpers.bayesian import summarize_posterior_parameters

    posterior_samples = PosteriorSamples(
        parameter_names=['beta', 'alpha'],
        parameter_samples=np.array(
            [
                [[2.0, 1.0], [2.2, 1.2]],
                [[1.8, 0.8], [2.1, 1.1]],
            ],
            dtype=float,
        ),
    )

    summaries = summarize_posterior_parameters(
        parameter_names=['beta', 'alpha'],
        posterior_samples=posterior_samples,
        best_sample_values=np.array([2.05, 1.05]),
        parameter_display_names=['Beta width', 'Alpha shift'],
        convergence_diagnostics={
            'r_hat_by_parameter': {'beta': 1.02, 'alpha': 1.0},
            'ess_bulk_by_parameter': {'beta': 120.0, 'alpha': 800.0},
        },
    )

    assert [summary.unique_name for summary in summaries] == ['beta', 'alpha']
    assert [summary.display_name for summary in summaries] == ['Beta width', 'Alpha shift']
    assert summaries[0].r_hat == pytest.approx(1.02)
    assert summaries[0].ess_bulk == pytest.approx(120.0)
    assert summaries[1].r_hat == pytest.approx(1.0)
    assert summaries[1].ess_bulk == pytest.approx(800.0)


def test_summarize_posterior_parameters_validates_display_name_length():
    from easydiffraction.analysis.fit_helpers.bayesian import PosteriorSamples
    from easydiffraction.analysis.fit_helpers.bayesian import summarize_posterior_parameters

    posterior_samples = PosteriorSamples(
        parameter_names=['alpha'],
        parameter_samples=np.ones((2, 2, 1), dtype=float),
    )

    with pytest.raises(
        ValueError,
        match=r'Posterior display-name list must match the sampled parameter name list length\.',
    ):
        summarize_posterior_parameters(
            parameter_names=['alpha'],
            posterior_samples=posterior_samples,
            best_sample_values=np.array([1.0]),
            parameter_display_names=['Alpha', 'Extra'],
        )


def test_standard_deviations_from_summaries_returns_float_array():
    from easydiffraction.analysis.fit_helpers.bayesian import PosteriorParameterSummary
    from easydiffraction.analysis.fit_helpers.bayesian import standard_deviations_from_summaries

    values = standard_deviations_from_summaries([
        PosteriorParameterSummary(
            unique_name='a',
            display_name='A',
            best_sample_value=1.0,
            median=1.0,
            standard_deviation=0.2,
            interval_68=(0.9, 1.1),
            interval_95=(0.8, 1.2),
        ),
        PosteriorParameterSummary(
            unique_name='b',
            display_name='B',
            best_sample_value=2.0,
            median=2.0,
            standard_deviation=0.3,
            interval_68=(1.9, 2.1),
            interval_95=(1.8, 2.2),
        ),
    ])

    np.testing.assert_allclose(values, np.array([0.2, 0.3]))
    assert values.dtype == float


def test_bayesian_format_helpers_cover_edge_cases():
    from easydiffraction.analysis.fit_helpers.bayesian import _calculate_fit_quality_metrics
    from easydiffraction.analysis.fit_helpers.bayesian import _dataset_to_scalar_dict
    from easydiffraction.analysis.fit_helpers.bayesian import _format_bayesian_overall_status
    from easydiffraction.analysis.fit_helpers.bayesian import _format_convergence_summary
    from easydiffraction.analysis.fit_helpers.bayesian import _format_point_estimate_name
    from easydiffraction.analysis.fit_helpers.bayesian import _format_sampler_settings
    from easydiffraction.analysis.fit_helpers.bayesian import _maybe_scalar

    dataset = type(
        'FakeDataset',
        (),
        {'data_vars': {'a': np.array([np.nan], dtype=float), 'b': np.array([3.0], dtype=float)}},
    )

    assert _maybe_scalar(None) is None
    assert _maybe_scalar(float('inf')) is None
    assert _maybe_scalar(3.0) == pytest.approx(3.0)
    assert _dataset_to_scalar_dict(dataset) == {'a': None, 'b': 3.0}
    assert _format_sampler_settings({}) is None
    assert (
        _format_sampler_settings({'steps': 10, 'burn': 2, 'samples': 40})
        == 'steps=10, burn=2, samples=40'
    )
    assert _format_point_estimate_name('map') == 'Best posterior sample'
    assert _format_point_estimate_name('best_sample') == 'Best posterior sample'
    assert _format_bayesian_overall_status(
        success=False,
        sampler_completed=False,
        convergence_diagnostics={},
    ) == ('❌', 'failed')
    assert _format_bayesian_overall_status(
        success=True,
        sampler_completed=False,
        convergence_diagnostics={'converged': False},
    ) == ('⚠️', 'completed with warnings')
    assert _format_bayesian_overall_status(
        success=True,
        sampler_completed=True,
        convergence_diagnostics={'converged': True},
    ) == ('✅', 'completed')
    assert _format_bayesian_overall_status(
        success=True,
        sampler_completed=False,
        convergence_diagnostics={},
    ) == ('✅', 'posterior available')
    assert _format_convergence_summary({}) is None
    assert _format_convergence_summary({
        'converged': False,
        'max_r_hat': 1.02,
        'min_ess_bulk': 200.0,
        'n_draws': 30,
        'n_chains': 8,
    }) == (
        'status=[red]failed[/red], max_r_hat=[red]1.020[/red], '
        'min_ess_bulk=[red]200.0[/red], draws=30, chains=8'
    )

    metrics = _calculate_fit_quality_metrics(
        y_obs=[10.0, 20.0],
        y_calc=[9.5, 19.5],
        y_err=[1.0, 1.0],
        f_obs=[5.0, 6.0],
        f_calc=[5.1, 5.9],
    )

    assert metrics['rf'] is not None
    assert metrics['rf2'] is not None
    assert metrics['wr'] is not None
    assert metrics['br'] is not None


def test_bayesian_fit_results_display_results_prints_sampler_and_convergence(capsys, monkeypatch):
    from easydiffraction.analysis.fit_helpers.bayesian import BayesianFitResults
    from easydiffraction.analysis.fit_helpers.bayesian import PosteriorParameterSummary
    from easydiffraction.utils.logging import Logger

    monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

    results = BayesianFitResults(
        success=True,
        parameters=[Param(unique_name='a', start=1.0, value=1.2, uncertainty=0.05)],
        reduced_chi_square=1.2345,
        fitting_time=0.9876,
        sampler_name='dream',
        sampler_completed=True,
        sampler_settings={
            'random_seed': 1313900679,
            'steps': 200,
            'burn': 50,
            'thin': 1,
            'pop': 4,
            'init': 'lhs',
            'samples': 3200,
        },
        convergence_diagnostics={
            'converged': False,
            'max_r_hat': 1.107,
            'min_ess_bulk': 125.9,
            'n_draws': 200,
            'n_chains': 16,
        },
        posterior_parameter_summaries=[
            PosteriorParameterSummary(
                unique_name='a',
                display_name='a',
                best_sample_value=1.2,
                median=1.15,
                standard_deviation=0.05,
                interval_68=(1.1, 1.2),
                interval_95=(1.0, 1.3),
                r_hat=1.107,
                ess_bulk=125.9,
            )
        ],
        best_log_posterior=-12.34,
    )
    results.message = 'DREAM sampling completed'

    results.display_results(y_obs=[10.0, 20.0], y_calc=[9.5, 19.5])

    out = _unstyled_output(capsys.readouterr().out)
    assert 'Bayesian fit results' in out
    assert 'Overall status: completed with warnings' in out
    assert 'Sampler status: DREAM sampling completed' in out
    assert 'Sampler: dream' in out
    assert 'Sampler completed: yes' in out
    assert 'steps=200' in out
    assert 'init=lhs' in out
    assert 'random_seed=1313900679' not in out
    assert 'status=failed' in out
    assert 'max_r_hat=1.107' in out
    assert 'min_ess_bulk=125.9' in out
    assert 'Posterior parameter summaries:' in out
    assert 'Success: True' not in out
    assert 'datablock' in out
    assert 'category' in out
    assert 'entry' in out
    assert '95% interval' in out
    assert '68% interval' not in out
    assert 'std' not in out

    monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.RAISE, raising=True)


def test_render_posterior_summary_table_without_summaries_prints_notice(capsys):
    from easydiffraction.analysis.fit_helpers import bayesian

    bayesian._render_posterior_summary_table(parameters=[], posterior_parameter_summaries=[])

    assert 'No posterior parameter summaries available.' in capsys.readouterr().out


def test_build_posterior_summary_row_restores_identifier_columns():
    from easydiffraction.analysis.fit_helpers.bayesian import PosteriorParameterSummary
    from easydiffraction.analysis.fit_helpers.bayesian import _build_posterior_summary_row

    parameter = Param(unique_name='a', start=1.0, value=1.2, uncertainty=0.05)
    summary = PosteriorParameterSummary(
        unique_name='a',
        display_name='a',
        best_sample_value=1.2,
        median=1.15,
        standard_deviation=0.05,
        interval_68=(1.1, 1.2),
        interval_95=(1.0, 1.3),
        r_hat=1.107,
        ess_bulk=125.9,
    )

    row = _build_posterior_summary_row(summary, {'a': parameter})

    assert row == [
        'db',
        'cat',
        'entry',
        'a',
        'arb',
        '1.1500',
        '[1.0000, 1.3000]',
        '[red]1.107[/red]',
        '[red]125.9[/red]',
    ]


def test_render_committed_parameter_table_places_units_after_parameter(monkeypatch):
    from easydiffraction.analysis.fit_helpers import bayesian

    captured: dict[str, object] = {}

    def fake_render_table(*, columns_headers, columns_alignment, columns_data):
        captured['columns_headers'] = columns_headers
        captured['columns_alignment'] = columns_alignment
        captured['columns_data'] = columns_data

    monkeypatch.setattr(bayesian, 'render_table', fake_render_table)

    bayesian._render_committed_parameter_table([
        Param(unique_name='a', start=1.0, value=1.2, uncertainty=0.05)
    ])

    assert captured['columns_headers'] == [
        'datablock',
        'category',
        'entry',
        'parameter',
        'units',
        'start',
        'best posterior sample',
        'uncertainty',
        'change',
    ]
    assert captured['columns_alignment'] == [
        'left',
        'left',
        'left',
        'left',
        'left',
        'right',
        'right',
        'right',
        'right',
    ]
    assert captured['columns_data'] == [
        [
            'db',
            'cat',
            'entry',
            'a',
            'arb',
            '1.0000',
            '1.2000',
            '0.0500',
            '20.00 % ↑',
        ]
    ]


def test_render_posterior_summary_table_places_units_after_parameter(monkeypatch):
    from easydiffraction.analysis.fit_helpers import bayesian
    from easydiffraction.analysis.fit_helpers.bayesian import PosteriorParameterSummary

    captured: dict[str, object] = {}

    def fake_render_table(*, columns_headers, columns_alignment, columns_data):
        captured['columns_headers'] = columns_headers
        captured['columns_alignment'] = columns_alignment
        captured['columns_data'] = columns_data

    monkeypatch.setattr(bayesian, 'render_table', fake_render_table)

    bayesian._render_posterior_summary_table(
        parameters=[Param(unique_name='a', start=1.0, value=1.2, uncertainty=0.05)],
        posterior_parameter_summaries=[
            PosteriorParameterSummary(
                unique_name='a',
                display_name='a',
                best_sample_value=1.2,
                median=1.15,
                standard_deviation=0.05,
                interval_68=(1.1, 1.2),
                interval_95=(1.0, 1.3),
                r_hat=1.107,
                ess_bulk=125.9,
            )
        ],
    )

    assert captured['columns_headers'] == [
        'datablock',
        'category',
        'entry',
        'parameter',
        'units',
        'median',
        '95% interval',
        'r-hat',
        'ess bulk',
    ]
    assert captured['columns_alignment'] == [
        'left',
        'left',
        'left',
        'left',
        'left',
        'right',
        'right',
        'right',
        'right',
    ]
    assert captured['columns_data'] == [
        [
            'db',
            'cat',
            'entry',
            'a',
            'arb',
            '1.1500',
            '[1.0000, 1.3000]',
            '[red]1.107[/red]',
            '[red]125.9[/red]',
        ]
    ]


def test_posterior_table_notes_split_failed_diagnostics():
    from easydiffraction.analysis.fit_helpers.bayesian import PosteriorParameterSummary
    from easydiffraction.analysis.fit_helpers.bayesian import _posterior_table_notes

    notes = _posterior_table_notes([
        PosteriorParameterSummary(
            unique_name='a',
            display_name='a',
            best_sample_value=1.0,
            median=1.0,
            standard_deviation=0.1,
            interval_68=(0.9, 1.1),
            interval_95=(0.8, 1.2),
            r_hat=1.02,
            ess_bulk=100.0,
        )
    ])

    assert len(notes) == 2
    assert 'r-hat' in notes[0]
    assert 'ess bulk' in notes[1]


def test_bayesian_helpers_cover_non_warning_and_default_display_paths():
    from easydiffraction.analysis.fit_helpers.bayesian import PosteriorParameterSummary
    from easydiffraction.analysis.fit_helpers.bayesian import _build_posterior_summary_row
    from easydiffraction.analysis.fit_helpers.bayesian import _format_ess_bulk
    from easydiffraction.analysis.fit_helpers.bayesian import _format_r_hat
    from easydiffraction.analysis.fit_helpers.bayesian import _posterior_table_notes

    summary = PosteriorParameterSummary(
        unique_name='missing',
        display_name='Missing',
        best_sample_value=1.0,
        median=1.0,
        standard_deviation=0.1,
        interval_68=(0.9, 1.1),
        interval_95=(0.8, 1.2),
        r_hat=1.0,
        ess_bulk=500.0,
    )

    row = _build_posterior_summary_row(summary, {})

    assert row == [
        'N/A',
        'N/A',
        '',
        'Missing',
        'N/A',
        '1.0000',
        '[0.8000, 1.2000]',
        '1.000',
        '500.0',
    ]
    assert _format_r_hat(None) == 'N/A'
    assert _format_r_hat(1.0) == '1.000'
    assert _format_ess_bulk(None) == 'N/A'
    assert _format_ess_bulk(500.0) == '500.0'
    assert _posterior_table_notes([]) == []
    assert _posterior_table_notes([summary]) == []


def test_fitresults_display_results_prints_and_table(capsys):
    from easydiffraction.analysis.fit_helpers.reporting import FitResults

    params = [Param(unique_name='a', start=1.0, value=1.2, uncertainty=0.05)]

    results = FitResults(
        success=True,
        parameters=params,
        reduced_chi_square=1.2345,
        fitting_time=0.9876,
    )

    results.display_results(
        y_obs=[10.0, 20.0],
        y_calc=[9.5, 19.5],
        y_err=[1.0, 1.0],
        f_obs=[5.0, 6.0],
        f_calc=[5.1, 5.9],
    )

    out = _unstyled_output(capsys.readouterr().out)
    assert 'Fit results' in out
    assert 'Success: True' in out
    assert 'reduced χ²' in out
    assert 'R-factor (Rf)' in out
    assert 'R-factor squared (Rf²)' in out
    assert 'Weighted R-factor (wR)' in out
    assert 'Bragg R-factor (BR)' in out
    assert 'Fitted parameters:' in out
    assert any(char in out for char in ('╒', '┌', '+', '─'))


def test_fitresults_display_results_places_units_after_parameter(monkeypatch):
    from easydiffraction.analysis.fit_helpers import reporting

    captured: dict[str, object] = {}

    def fake_render_table(*, columns_headers, columns_alignment, columns_data):
        captured['columns_headers'] = columns_headers
        captured['columns_alignment'] = columns_alignment
        captured['columns_data'] = columns_data

    monkeypatch.setattr(reporting, 'render_table', fake_render_table)

    reporting.FitResults(
        success=True,
        parameters=[Param(unique_name='a', start=1.0, value=1.2, uncertainty=0.05)],
    ).display_results()

    assert captured['columns_headers'] == [
        'datablock',
        'category',
        'entry',
        'parameter',
        'units',
        'start',
        'fitted',
        'uncertainty',
        'change',
    ]
    assert captured['columns_alignment'] == [
        'left',
        'left',
        'left',
        'left',
        'left',
        'right',
        'right',
        'right',
        'right',
    ]
    assert captured['columns_data'] == [
        [
            'db',
            'cat',
            'entry',
            'a',
            'arb',
            '1.0000',
            '1.2000',
            '0.0500',
            '20.00 % ↑',
        ]
    ]
