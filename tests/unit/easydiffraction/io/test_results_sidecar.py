# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for persisted Bayesian results sidecars."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import numpy as np


def _analysis_with_predictive_sidecar() -> object:
    from easydiffraction.analysis.categories.bayesian_predictive_datasets.default import (
        BayesianPredictiveDatasetPaths,
        BayesianPredictiveDatasets,
    )
    from easydiffraction.analysis.categories.bayesian_result.default import BayesianResult
    from easydiffraction.analysis.categories.fit_result.default import FitResult

    fit_result = FitResult()
    fit_result._set_result_kind('bayesian')
    bayesian_result = BayesianResult()
    bayesian_result._set_has_posterior_predictive(value=True)
    predictive = BayesianPredictiveDatasets()
    predictive.create(
        experiment_name='hrpt',
        x_axis_name='two_theta',
        paths=BayesianPredictiveDatasetPaths(
            x_path='/predictive/hrpt/x',
            best_sample_prediction_path='/predictive/hrpt/best_sample_prediction',
            lower_95_path='/predictive/hrpt/lower_95',
            upper_95_path='/predictive/hrpt/upper_95',
        ),
        n_x=2,
        n_draws_cached=0,
    )
    return SimpleNamespace(
        fit_result=fit_result,
        bayesian_result=bayesian_result,
        bayesian_convergence=SimpleNamespace(
            n_draws=SimpleNamespace(value=0),
            n_chains=SimpleNamespace(value=0),
            n_parameters=SimpleNamespace(value=0),
        ),
        bayesian_distribution_caches=[],
        bayesian_pair_caches=[],
        bayesian_predictive_datasets=predictive,
        fit_results=SimpleNamespace(
            posterior_predictive={
                'hrpt': SimpleNamespace(
                    experiment_name='hrpt',
                    x_axis_name='two_theta',
                    x=np.asarray([1.0, 2.0]),
                    best_sample_prediction=np.asarray([3.0, 4.0]),
                    lower_95=np.asarray([2.5, 3.5]),
                    upper_95=np.asarray([3.5, 4.5]),
                    lower_68=None,
                    upper_68=None,
                    draws=None,
                )
            }
        ),
        _persisted_fit_state_sidecar={},
        _has_persisted_fit_state=lambda: True,
    )


def test_write_and_read_analysis_results_sidecar_round_trip_predictive(tmp_path):
    from easydiffraction.io.results_sidecar import read_analysis_results_sidecar
    from easydiffraction.io.results_sidecar import write_analysis_results_sidecar

    analysis_dir = Path(tmp_path)
    analysis = _analysis_with_predictive_sidecar()

    write_analysis_results_sidecar(analysis=analysis, analysis_dir=analysis_dir)

    sidecar_path = analysis_dir / 'results.h5'
    assert sidecar_path.is_file()

    restored = _analysis_with_predictive_sidecar()
    restored.fit_results = None
    read_analysis_results_sidecar(analysis=restored, analysis_dir=analysis_dir)

    assert 'predictive_datasets' in restored._persisted_fit_state_sidecar
    dataset = restored._persisted_fit_state_sidecar['predictive_datasets']['hrpt']
    assert np.allclose(dataset['x'], np.asarray([1.0, 2.0]))
    assert np.allclose(dataset['best_sample_prediction'], np.asarray([3.0, 4.0]))


def test_read_analysis_results_sidecar_warns_when_expected_file_is_missing(tmp_path, monkeypatch):
    from easydiffraction.io import results_sidecar as results_sidecar_mod

    analysis = _analysis_with_predictive_sidecar()
    warnings: list[str] = []
    monkeypatch.setattr(results_sidecar_mod.log, 'warning', warnings.append)

    results_sidecar_mod.read_analysis_results_sidecar(
        analysis=analysis,
        analysis_dir=Path(tmp_path),
    )

    assert analysis._persisted_fit_state_sidecar == {}
    assert any('Expected Bayesian results sidecar is missing' in warning for warning in warnings)
