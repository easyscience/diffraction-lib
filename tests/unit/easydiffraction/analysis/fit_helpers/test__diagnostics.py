# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import math

import numpy as np
import pytest

from easydiffraction.analysis.fit_helpers._diagnostics import _autocorr_fft
from easydiffraction.analysis.fit_helpers._diagnostics import compute_ess_bulk
from easydiffraction.analysis.fit_helpers._diagnostics import compute_r_hat


def _independent_samples(n_draws: int, n_chains: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.standard_normal((n_draws, n_chains))


def _correlated_chain(n_draws: int, n_chains: int, rho: float, seed: int) -> np.ndarray:
    """Generate AR(1) chains with autocorrelation ``rho``."""
    rng = np.random.default_rng(seed)
    samples = np.zeros((n_draws, n_chains))
    samples[0, :] = rng.standard_normal(n_chains)
    sigma = math.sqrt(1.0 - rho * rho)
    for t in range(1, n_draws):
        samples[t, :] = rho * samples[t - 1, :] + sigma * rng.standard_normal(n_chains)
    return samples


def test_r_hat_returns_nan_for_too_few_draws_or_chains():
    assert math.isnan(compute_r_hat(np.ones((3, 4))))
    assert math.isnan(compute_r_hat(np.ones((100, 1))))


def test_r_hat_returns_nan_for_zero_variance():
    assert math.isnan(compute_r_hat(np.ones((100, 4))))


def test_r_hat_rejects_non_2d_arrays():
    with pytest.raises(ValueError, match=r'samples must have shape \(n_draws, n_chains\)'):
        compute_r_hat(np.ones((10, 4, 2)))


def test_r_hat_close_to_one_for_well_mixed_independent_chains():
    samples = _independent_samples(n_draws=2000, n_chains=4, seed=42)
    r_hat = compute_r_hat(samples)

    assert math.isfinite(r_hat)
    assert 0.98 < r_hat < 1.05


def test_r_hat_above_one_when_chains_disagree():
    rng = np.random.default_rng(1)
    chains_with_offsets = rng.standard_normal((1000, 4)) + np.array([-2.0, -1.0, 1.0, 2.0])
    r_hat = compute_r_hat(chains_with_offsets)

    assert math.isfinite(r_hat)
    assert r_hat > 1.5


def test_r_hat_handles_odd_number_of_draws():
    samples = _independent_samples(n_draws=2001, n_chains=4, seed=7)
    r_hat = compute_r_hat(samples)

    assert math.isfinite(r_hat)
    assert 0.97 < r_hat < 1.05


def test_ess_bulk_returns_nan_for_too_few_draws():
    assert math.isnan(compute_ess_bulk(np.ones((3, 4))))


def test_ess_bulk_rejects_non_2d_arrays():
    with pytest.raises(ValueError, match=r'samples must have shape \(n_draws, n_chains\)'):
        compute_ess_bulk(np.ones((10, 4, 2)))


def test_ess_bulk_near_total_for_independent_samples():
    samples = _independent_samples(n_draws=2000, n_chains=4, seed=123)
    ess = compute_ess_bulk(samples)

    assert math.isfinite(ess)
    # Rank-normalized ACF on truly independent samples is dominated by
    # noise around zero; the Geyer initial-positive-sequence sum truncates
    # quickly and ESS is close to the total sample count.
    assert ess > 0.5 * samples.size


def test_ess_bulk_lower_for_strongly_autocorrelated_chains():
    independent = _independent_samples(n_draws=2000, n_chains=4, seed=11)
    correlated = _correlated_chain(n_draws=2000, n_chains=4, rho=0.9, seed=11)

    ess_independent = compute_ess_bulk(independent)
    ess_correlated = compute_ess_bulk(correlated)

    assert math.isfinite(ess_independent)
    assert math.isfinite(ess_correlated)
    assert ess_correlated < 0.4 * ess_independent


def test_autocorr_fft_handles_zero_variance():
    flat = np.ones(64)
    acf = _autocorr_fft(flat)

    # Zero-variance input: ACF is all zeros except the lag-0 element.
    assert acf[0] == 0.0
