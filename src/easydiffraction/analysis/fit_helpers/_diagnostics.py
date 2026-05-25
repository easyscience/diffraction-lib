# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
MCMC convergence diagnostics computed in pure NumPy + SciPy.

The two diagnostics this module produces — split-chain Gelman–Rubin R̂
and bulk effective sample size (ESS) — are the only Bayesian diagnostics
EasyDiffraction reports. The implementations follow the standard
formulas described in Vehtari, Gelman, Simpson, Carpenter and Bürkner
(2019), *Rank-normalization, folding, and localization: An improved R̂
for assessing convergence of MCMC* (https://arxiv.org/abs/1903.08008),
Stan's reference manual, and Geyer (1992), *Practical Markov chain Monte
Carlo*.

Inputs use the project's preserved layout: a 2-D NumPy array of shape
``(n_draws, n_chains)`` per parameter, never an ArviZ ``InferenceData``
object.
"""

from __future__ import annotations

import numpy as np
from scipy import stats

_MIN_DRAWS = 4


def compute_r_hat(samples: np.ndarray) -> float:
    """
    Split-chain Gelman–Rubin R̂ for one parameter.

    Each chain is split in half (the standard "split R̂" variant); the
    within-chain (W) and between-chain (B) variances are computed on the
    doubled chain set, and R̂ is returned as ``sqrt(V̂ / W)`` where ``V̂
    = ((n-1)/n) · W + B/n``.

    Parameters
    ----------
    samples : np.ndarray
        Posterior samples for one parameter with shape ``(n_draws,
        n_chains)``.

    Returns
    -------
    float
        R̂ value. ``nan`` when there are fewer than 4 draws, fewer than
        2 chains, or zero within-chain variance.

    Raises
    ------
    ValueError
        If ``samples`` is not 2-D.
    """
    if samples.ndim != 2:
        msg = 'samples must have shape (n_draws, n_chains)'
        raise ValueError(msg)
    n_draws, n_chains = samples.shape
    if n_draws < _MIN_DRAWS or n_chains < 2:
        return float('nan')

    # Split each chain in half. With odd n_draws, drop the middle sample.
    half = n_draws // 2
    splits = np.concatenate(
        [samples[:half, :], samples[-half:, :]],
        axis=1,
    )

    n_split = splits.shape[0]
    chain_means = splits.mean(axis=0)
    chain_vars = splits.var(axis=0, ddof=1)

    within = float(chain_vars.mean())
    if within == 0 or not np.isfinite(within):
        return float('nan')

    between = n_split * float(chain_means.var(ddof=1))
    var_hat = ((n_split - 1) / n_split) * within + between / n_split
    return float(np.sqrt(var_hat / within))


def compute_ess_bulk(samples: np.ndarray) -> float:
    """
    Bulk effective sample size for one parameter.

    Samples are rank-normalized across all chain/draw pairs (so the
    diagnostic is robust to heavy-tailed marginals); the autocorrelation
    function is then averaged across chains and summed with Geyer's
    initial positive sequence: pairs of consecutive lags are added to
    the running variance estimate until a pair first becomes
    non-positive (Geyer 1992; Vehtari et al. 2019 §3.1).

    Parameters
    ----------
    samples : np.ndarray
        Posterior samples for one parameter with shape ``(n_draws,
        n_chains)``.

    Returns
    -------
    float
        Effective sample size in the bulk of the posterior. ``nan`` when
        there are fewer than 4 draws, no chains, zero variance, or the
        autocorrelation sum is non-positive.

    Raises
    ------
    ValueError
        If ``samples`` is not 2-D.
    """
    if samples.ndim != 2:
        msg = 'samples must have shape (n_draws, n_chains)'
        raise ValueError(msg)
    n_draws, n_chains = samples.shape
    if n_draws < _MIN_DRAWS or n_chains < 1:
        return float('nan')

    total = n_draws * n_chains

    # Rank-normalize across all samples → standard normal scores.
    ranks = stats.rankdata(samples.ravel()).reshape(samples.shape)
    z = stats.norm.ppf((ranks - 0.5) / total)

    # Per-chain autocorrelation, then average across chains.
    acf_sum = np.zeros(n_draws)
    for chain_index in range(n_chains):
        acf_sum += _autocorr_fft(z[:, chain_index])
    rho = acf_sum / n_chains

    if not np.isfinite(rho[0]) or rho[0] <= 0:
        return float('nan')

    # Geyer's initial positive sequence on pairs of lags.
    tau = 1.0
    for t in range(1, n_draws // 2):
        pair = rho[2 * t - 1] + rho[2 * t]
        if pair <= 0:
            break
        tau += 2.0 * pair

    if tau <= 0 or not np.isfinite(tau):
        return float('nan')
    return float(total / tau)


def _autocorr_fft(series: np.ndarray) -> np.ndarray:
    """
    Return the normalized autocorrelation function via FFT.

    Pads to the next power of two so the FFT is well-conditioned for
    arbitrary chain lengths. The returned ACF has the same length as the
    input series and starts at ``rho[0] = 1`` when the input has
    non-zero variance.

    Parameters
    ----------
    series : np.ndarray
        One-dimensional sequence of samples.

    Returns
    -------
    np.ndarray
        Autocorrelation values at lags 0, 1, …, ``len(series) - 1``.
    """
    n = series.size
    centered = series - series.mean()
    size = 1 << (2 * n - 1).bit_length()
    fx = np.fft.fft(centered, n=size)
    acf = np.fft.ifft(fx * np.conj(fx))[:n].real
    if acf[0] == 0:
        return acf
    return acf / acf[0]
