# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Integration checks for emcee Bayesian sampling."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pytest

from easydiffraction.utils.enums import VerbosityEnum


@dataclass
class ToyParameter:
    """Minimal parameter object accepted by the Bayesian engines."""

    unique_name: str
    value: float
    fit_min: float
    fit_max: float
    uncertainty: float | None = None

    @property
    def name(self) -> str:
        """Return the display name used in posterior summaries."""
        return self.unique_name

    @property
    def _minimizer_uid(self) -> str:
        """Return the BUMPS parameter identifier."""
        return self.unique_name

    def _set_value_from_minimizer(self, value: float) -> None:
        """Store a value committed by the minimizer."""
        self.value = value


def _toy_parameters() -> list[ToyParameter]:
    return [
        ToyParameter(unique_name='x', value=0.0, fit_min=-4.0, fit_max=4.0),
        ToyParameter(unique_name='y', value=0.0, fit_min=-4.0, fit_max=4.0),
    ]


def _array_residuals(values: np.ndarray) -> np.ndarray:
    target = np.asarray([1.2, -0.7], dtype=float)
    sigma = np.asarray([0.25, 0.35], dtype=float)
    return (np.asarray(values, dtype=float) - target) / sigma


def _mapping_residuals(values: dict[str, object]) -> np.ndarray:
    return _array_residuals(np.asarray([values['x'], values['y']], dtype=float))


def _posterior_medians(results: object) -> np.ndarray:
    return np.asarray(
        [summary.median for summary in results.posterior_parameter_summaries],
        dtype=float,
    )


@pytest.mark.parametrize('proposal_moves', ['de'])
def test_emcee_resume_matches_small_dream_posterior(tmp_path, proposal_moves):
    from easydiffraction.analysis.minimizers.bumps_dream import BumpsDreamMinimizer
    from easydiffraction.analysis.minimizers.emcee import EmceeMinimizer

    dream = BumpsDreamMinimizer()
    dream.steps = 80
    dream.burn = 20
    dream.thin = 1
    dream.pop = 4
    dream.parallel = 1
    dream_results = dream.fit(
        _toy_parameters(),
        _array_residuals,
        verbosity=VerbosityEnum.SILENT,
        random_seed=123,
    )

    emcee = EmceeMinimizer()
    emcee.nsteps = 80
    emcee.nburn = 20
    emcee.thin = 1
    emcee.nwalkers = 16
    emcee.parallel_workers = 1
    emcee.proposal_moves = proposal_moves
    emcee._sidecar_path = tmp_path / 'analysis' / 'results.h5'
    emcee_results = emcee.fit(
        _toy_parameters(),
        _mapping_residuals,
        verbosity=VerbosityEnum.SILENT,
        random_seed=123,
    )
    resumed_results = emcee.fit(
        _toy_parameters(),
        _mapping_residuals,
        verbosity=VerbosityEnum.SILENT,
        random_seed=123,
        resume=True,
        extra_steps=20,
    )

    assert dream_results.success is True
    assert emcee_results.success is True
    assert resumed_results.success is True
    assert resumed_results.posterior_samples is not None
    assert resumed_results.posterior_samples.parameter_samples.shape[1:] == (16, 2)
    assert resumed_results.sampler_settings['total_steps'] == 100
    np.testing.assert_allclose(
        _posterior_medians(resumed_results),
        _posterior_medians(dream_results),
        atol=0.35,
    )
