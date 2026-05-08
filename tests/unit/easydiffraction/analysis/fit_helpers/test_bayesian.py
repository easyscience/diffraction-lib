# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import numpy as np
import pytest


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


def test_module_import():
    import easydiffraction.analysis.fit_helpers.bayesian as MUT

    assert MUT.__name__ == 'easydiffraction.analysis.fit_helpers.bayesian'


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
        map_values=np.array([2.05, 1.05]),
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
                map_value=1.2,
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

    results.display_results(y_obs=[10.0, 20.0], y_calc=[9.5, 19.5])

    out = capsys.readouterr().out
    assert 'Bayesian fit results' in out
    assert 'Sampler: dream' in out
    assert 'random_seed=1313900679' in out
    assert 'steps=200' in out
    assert 'max_r_hat=1.107' in out
    assert 'min_ess_bulk=125.9' in out
    assert 'Posterior parameter summaries:' in out

    monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.RAISE, raising=True)


def test_posterior_table_notes_split_failed_diagnostics():
    from easydiffraction.analysis.fit_helpers.bayesian import PosteriorParameterSummary
    from easydiffraction.analysis.fit_helpers.bayesian import _posterior_table_notes

    notes = _posterior_table_notes([
        PosteriorParameterSummary(
            unique_name='a',
            display_name='a',
            map_value=1.0,
            median=1.0,
            standard_deviation=0.1,
            interval_68=(0.9, 1.1),
            interval_95=(0.8, 1.2),
            r_hat=1.02,
            ess_bulk=100.0,
        )
    ])

    assert len(notes) == 2
    assert 'r_hat' in notes[0]
    assert 'ess_bulk' in notes[1]
