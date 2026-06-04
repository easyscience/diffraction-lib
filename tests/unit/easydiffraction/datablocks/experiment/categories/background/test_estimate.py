# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np
import pytest

from easydiffraction.datablocks.experiment.categories.background import estimate

estimate_background_curve = estimate.estimate_background_curve
BackgroundEstimate = estimate.BackgroundEstimate


def _pattern(n=400, slope=0.3, intercept=5.0, peaks=((5.0, 6.0, 0.15),), noise=0.0, seed=0):
    """Build a synthetic pattern: linear background + Gaussian peaks + noise."""
    x = np.linspace(0.0, 10.0, n)
    y = intercept + slope * x
    for center, amp, width in peaks:
        y = y + amp * np.exp(-((x - center) ** 2) / (2.0 * width**2))
    if noise > 0:
        rng = np.random.default_rng(seed)
        y = y + rng.normal(0.0, noise, size=n)
    return x, y.astype(float)


def _anchor_indices(x, anchors):
    return [int(np.argmin(np.abs(x - ax))) for ax in anchors[:, 0]]


def _collect_warnings(monkeypatch):
    records = []

    class _Log:
        def warning(self, message, *args, **kwargs):
            records.append(str(message))

    monkeypatch.setattr(estimate, 'log', _Log())
    return records


def test_returns_background_estimate_with_metadata():
    x, y = _pattern(noise=0.05, seed=1)
    result = estimate_background_curve(x, y, method='arpls')
    assert isinstance(result, BackgroundEstimate)
    assert result.method == 'arpls'
    assert result.curve.shape == x.shape
    assert result.anchors.ndim == 2
    assert result.anchors.shape[1] == 2
    assert result.width > 0
    assert result.noise >= 0
    assert result.tolerance >= 0
    assert 'lam' in result.backend_params


def test_endpoints_always_kept():
    x, y = _pattern(noise=0.05, seed=2)
    result = estimate_background_curve(x, y)
    assert result.anchors[0, 0] == pytest.approx(x[0])
    assert result.anchors[-1, 0] == pytest.approx(x[-1])


def test_recovers_linear_background_curve():
    x, y = _pattern(noise=0.05, seed=3)
    result = estimate_background_curve(x, y, method='arpls')
    true_bg = 5.0 + 0.3 * x
    # The de-peaked curve tracks the true linear background closely.
    assert np.median(np.abs(result.curve - true_bg)) < 0.5


def test_anchors_are_sparse_with_noise():
    x, y = _pattern(n=400, noise=0.05, seed=4)
    result = estimate_background_curve(x, y)
    # Far fewer anchors than grid points, but at least the two endpoints.
    assert 2 <= result.anchors.shape[0] < 60


def test_no_anchor_on_planted_peak_self_derived():
    x, y = _pattern(noise=0.04, peaks=((5.0, 8.0, 0.2),), seed=5)
    result = estimate_background_curve(x, y, peaks=None)
    interior = result.anchors[1:-1, 0]
    # No interior anchor sits on the planted peak (centre 5.0).
    assert not np.any(np.abs(interior - 5.0) < 0.4)


def test_no_anchor_on_supplied_mask():
    x, y = _pattern(noise=0.04, seed=6)
    mask = (x > 4.0) & (x < 6.0)
    result = estimate_background_curve(x, y, peaks=mask)
    indices = _anchor_indices(x, result.anchors)
    endpoints = {0, x.size - 1}
    for idx in indices:
        if idx not in endpoints:
            assert not mask[idx]


def test_determinism():
    x, y = _pattern(noise=0.05, seed=7)
    first = estimate_background_curve(x, y)
    second = estimate_background_curve(x, y)
    assert np.array_equal(first.anchors, second.anchors)
    assert first.width == second.width


def test_graceful_degradation_peakless(monkeypatch):
    records = _collect_warnings(monkeypatch)
    x = np.linspace(0.0, 10.0, 60)
    y = np.full(60, 3.0)
    result = estimate_background_curve(x, y)
    assert result.anchors.shape[0] >= 2
    assert any('peak' in r.lower() for r in records)


def test_method_dispatch_backend_params():
    x, y = _pattern(noise=0.05, seed=8)
    assert 'lam' in estimate_background_curve(x, y, method='arpls').backend_params
    snip = estimate_background_curve(x, y, method='snip').backend_params
    assert 'max_half_window' in snip
    fabc = estimate_background_curve(x, y, method='fabc').backend_params
    assert 'scale' in fabc
    assert 'min_length' in fabc


def test_snip_ignores_smoothness_with_warning(monkeypatch):
    records = _collect_warnings(monkeypatch)
    x, y = _pattern(noise=0.03, seed=9)
    estimate_background_curve(x, y, method='snip', smoothness=500.0)
    assert any('smoothness' in r.lower() for r in records)


def test_n_points_cap_respected():
    x, y = _pattern(n=400, noise=0.05, seed=10)
    result = estimate_background_curve(x, y, n_points=6)
    assert result.anchors.shape[0] <= 6


def test_n_points_cap_respected_zero_noise():
    # Noiseless curved baseline: tolerance is zero, so the cap must rely on
    # the deviation-based fallback rather than RDP-tolerance growth.
    x = np.linspace(0.0, 10.0, 300)
    y = 5.0 + 2.0 * np.sin(x / 3.0)
    result = estimate_background_curve(x, y, n_points=5)
    assert result.anchors.shape[0] <= 5
    assert result.anchors.shape[0] >= 2


def test_invalid_method_rejected():
    x, y = _pattern(noise=0.05, seed=11)
    with pytest.raises(ValueError, match='method'):
        estimate_background_curve(x, y, method='bogus')


def test_cwl_broadening_keeps_background_off_broad_peaks():
    # FWHM grows with x; the upper-percentile width must still clear the
    # broad high-angle peak so the background is not pulled up under it.
    x = np.linspace(0.0, 10.0, 500)
    y = 4.0 + 0.0 * x
    for center in (2.0, 8.0):
        width = 0.1 + 0.06 * center  # broadening with angle
        y = y + 7.0 * np.exp(-((x - center) ** 2) / (2.0 * width**2))
    rng = np.random.default_rng(12)
    y = y + rng.normal(0.0, 0.05, size=x.size)
    result = estimate_background_curve(x, y)
    # Background near the broad peak stays well below the peak top.
    near_peak = result.curve[np.argmin(np.abs(x - 8.0))]
    assert near_peak < 6.0
