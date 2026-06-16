# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Integration checks for bumps-DREAM resume (extend a saved chain)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

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

    def _physical_lower_bound(self) -> float:
        """Return the lower physical limit for warning checks."""
        return -np.inf

    def _physical_upper_bound(self) -> float:
        """Return the upper physical limit for warning checks."""
        return np.inf


def _toy_parameters() -> list[ToyParameter]:
    return [
        ToyParameter(unique_name='x', value=0.0, fit_min=-4.0, fit_max=4.0),
        ToyParameter(unique_name='y', value=0.0, fit_min=-4.0, fit_max=4.0),
    ]


def _array_residuals(values: np.ndarray) -> np.ndarray:
    target = np.asarray([1.2, -0.7], dtype=float)
    sigma = np.asarray([0.25, 0.35], dtype=float)
    return (np.asarray(values, dtype=float) - target) / sigma


def _posterior_medians(results: object) -> np.ndarray:
    return np.asarray(
        [summary.median for summary in results.posterior_parameter_summaries],
        dtype=float,
    )


def _build_dream(sidecar_path: object) -> object:
    from easydiffraction.analysis.minimizers.bumps_dream import BumpsDreamMinimizer

    dream = BumpsDreamMinimizer()
    dream.steps = 80
    dream.burn = 20
    dream.thin = 1
    dream.pop = 4
    dream.parallel = 1
    dream._sidecar_path = sidecar_path
    return dream


def test_dream_resume_grows_chain_and_matches_longer_run(tmp_path):
    from easydiffraction.analysis.minimizers.base import MinimizerFitOptions
    from easydiffraction.analysis.minimizers.bumps_dream import DREAM_STATE_GROUP

    sidecar_path = tmp_path / 'analysis' / 'mcmc.h5'

    dream = _build_dream(sidecar_path)
    fresh_results = dream.fit(
        _toy_parameters(),
        _array_residuals,
        verbosity=VerbosityEnum.SILENT,
        options=MinimizerFitOptions(random_seed=123),
    )

    # The fresh fit persists a resumable DREAM state in the sidecar.
    assert fresh_results.success is True
    assert fresh_results.posterior_samples.parameter_samples.shape == (80, 8, 2)
    assert sidecar_path.is_file()

    import h5py

    with h5py.File(sidecar_path, 'r') as handle:
        assert DREAM_STATE_GROUP in handle

    resumed_results = dream.fit(
        _toy_parameters(),
        _array_residuals,
        verbosity=VerbosityEnum.SILENT,
        options=MinimizerFitOptions(random_seed=123, resume=True, extra_steps=20),
    )

    # Resume extends the saved chain by exactly extra_steps generations.
    assert resumed_results.success is True
    assert resumed_results.posterior_samples.parameter_samples.shape == (100, 8, 2)

    # A single 100-generation run reaches a comparable posterior.
    longer = _build_dream(tmp_path / 'longer' / 'mcmc.h5')
    longer.steps = 100
    longer_results = longer.fit(
        _toy_parameters(),
        _array_residuals,
        verbosity=VerbosityEnum.SILENT,
        options=MinimizerFitOptions(random_seed=123),
    )

    np.testing.assert_allclose(
        _posterior_medians(resumed_results),
        _posterior_medians(longer_results),
        atol=0.35,
    )


def test_dream_resume_rejects_population_change(tmp_path):
    import pytest

    from easydiffraction.analysis.minimizers.base import MinimizerFitOptions

    sidecar_path = tmp_path / 'analysis' / 'mcmc.h5'

    dream = _build_dream(sidecar_path)
    dream.fit(
        _toy_parameters(),
        _array_residuals,
        verbosity=VerbosityEnum.SILENT,
        options=MinimizerFitOptions(random_seed=123),
    )

    # Changing the population scale cannot be honoured on resume because
    # bumps resumes positionally into a fixed chain count.
    dream.pop = 6

    with pytest.raises(ValueError, match='population cannot change on resume'):
        dream.fit(
            _toy_parameters(),
            _array_residuals,
            verbosity=VerbosityEnum.SILENT,
            options=MinimizerFitOptions(random_seed=123, resume=True, extra_steps=20),
        )
