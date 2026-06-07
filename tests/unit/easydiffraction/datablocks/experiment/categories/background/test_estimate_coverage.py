# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np
import pytest

from easydiffraction.datablocks.experiment.categories.background import estimate

estimate_background_curve = estimate.estimate_background_curve
BackgroundEstimate = estimate.BackgroundEstimate


def _collect_warnings(monkeypatch):
    """Replace the module logger with a recorder and return the records list."""
    records = []

    class _Log:
        def warning(self, message, *args, **kwargs):
            records.append(str(message))

    monkeypatch.setattr(estimate, 'log', _Log())
    return records


# ---------------------------------------------------------------------------
# _robust_noise
# ---------------------------------------------------------------------------


def test_robust_noise_zero_for_flat_input():
    y = np.full(50, 7.0)
    assert estimate._robust_noise(y) == 0.0


def test_robust_noise_zero_for_linear_input():
    # A pure ramp has a vanishing second difference, hence zero noise.
    y = np.linspace(0.0, 100.0, 80)
    assert estimate._robust_noise(y) == pytest.approx(0.0, abs=1e-12)


def test_robust_noise_positive_for_noisy_input():
    rng = np.random.default_rng(0)
    y = rng.normal(0.0, 1.0, size=500)
    sigma = estimate._robust_noise(y)
    # Recovered sigma is in the right ballpark of the injected sigma (1.0).
    assert 0.5 < sigma < 2.0


# ---------------------------------------------------------------------------
# _measure_width
# ---------------------------------------------------------------------------


def test_measure_width_fallback_when_no_peaks():
    # Monotonic ramp has no local maxima -> fallback width, empty peaks.
    y = np.linspace(0.0, 10.0, 100)
    width, peaks = estimate._measure_width(y, sigma=0.1)
    assert width == estimate._FALLBACK_WIDTH
    assert peaks.size == 0


def test_measure_width_detects_peak_and_returns_positive_width():
    x = np.linspace(0.0, 10.0, 400)
    y = np.exp(-((x - 5.0) ** 2) / (2.0 * 0.2**2))
    width, peaks = estimate._measure_width(y, sigma=0.0)
    assert peaks.size >= 1
    assert width >= 1.0


def test_measure_width_floor_is_one_point():
    # A one-sample-wide spike yields a measured FWHM below 1 point, which
    # must be floored to 1.0.
    y = np.zeros(50)
    y[25] = 100.0
    width, peaks = estimate._measure_width(y, sigma=0.0)
    assert peaks.size == 1
    assert width == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# _forbidden_from_peaks
# ---------------------------------------------------------------------------


def test_forbidden_from_peaks_masks_window_around_each_peak():
    mask = estimate._forbidden_from_peaks(20, np.array([10]), width=2.0)
    assert mask.dtype == bool
    assert mask.shape == (20,)
    # +/- ceil(2) around index 10 -> indices 8..12 inclusive.
    assert np.all(mask[8:13])
    assert not mask[7]
    assert not mask[13]


def test_forbidden_from_peaks_clamps_at_edges():
    mask = estimate._forbidden_from_peaks(5, np.array([0, 4]), width=3.0)
    # Windows clamp to [0, n); both edges and everything between are masked.
    assert np.all(mask)


def test_forbidden_from_peaks_empty_peaks_all_false():
    mask = estimate._forbidden_from_peaks(10, np.array([], dtype=int), width=2.0)
    assert not np.any(mask)


# ---------------------------------------------------------------------------
# _derive_lam
# ---------------------------------------------------------------------------


def test_derive_lam_returns_floor_for_small_grids():
    # n * width below the floor -> the floor wins.
    assert estimate._derive_lam(2, 1.0) == estimate._LAM_FLOOR


def test_derive_lam_grows_with_size_and_width():
    big = estimate._derive_lam(1000, 5.0)
    assert big == pytest.approx(1000 * 5.0)
    assert big > estimate._derive_lam(1000, 2.0)


def test_derive_lam_clamps_width_to_one():
    # Width below 1.0 is treated as 1.0 in the penalty.
    assert estimate._derive_lam(500, 0.1) == estimate._derive_lam(500, 1.0)


# ---------------------------------------------------------------------------
# _stage1_baseline error path
# ---------------------------------------------------------------------------


def test_stage1_baseline_rejects_unknown_method():
    x = np.linspace(0.0, 10.0, 50)
    y = np.ones_like(x)
    with pytest.raises(ValueError, match='Unsupported Stage-1 background method'):
        estimate._stage1_baseline(x, y, 'nope', width=5.0, smoothness=None)


def test_stage1_baseline_arpls_honours_smoothness_override():
    x = np.linspace(0.0, 10.0, 80)
    y = 3.0 + 0.1 * x
    _, params = estimate._stage1_baseline(x, y, 'arpls', width=5.0, smoothness=1234.0)
    assert params['lam'] == pytest.approx(1234.0)


# ---------------------------------------------------------------------------
# _rdp_indices
# ---------------------------------------------------------------------------


def test_rdp_keeps_only_endpoints_for_straight_line():
    x = np.linspace(0.0, 10.0, 50)
    curve = 2.0 + 0.5 * x
    idx = estimate._rdp_indices(x, curve, epsilon=1e-9)
    assert idx.tolist() == [0, 49]


def test_rdp_span_zero_segment_skipped():
    # All-equal x: the root segment has zero span, so the only retained
    # points are the two endpoints (the span<=0 branch is taken).
    x = np.array([0.0, 0.0, 0.0])
    curve = np.array([0.0, 9.0, 0.0])
    idx = estimate._rdp_indices(x, curve, epsilon=0.1)
    assert idx.tolist() == [0, 2]


def test_rdp_keeps_sharp_deviation():
    x = np.linspace(0.0, 10.0, 11)
    curve = np.zeros(11)
    curve[5] = 100.0
    idx = estimate._rdp_indices(x, curve, epsilon=1.0)
    assert 5 in idx.tolist()
    assert idx[0] == 0
    assert idx[-1] == 10


# ---------------------------------------------------------------------------
# _drop_forbidden
# ---------------------------------------------------------------------------


def test_drop_forbidden_keeps_endpoints_even_when_masked():
    indices = np.array([0, 3, 5, 7, 9])
    forbidden = np.zeros(10, dtype=bool)
    forbidden[0] = True  # endpoint on a peak -> still kept
    forbidden[5] = True  # interior on a peak -> dropped
    kept = estimate._drop_forbidden(indices, forbidden, n=10)
    assert kept.tolist() == [0, 3, 7, 9]


def test_drop_forbidden_deduplicates_and_sorts():
    indices = np.array([9, 0, 3, 3])
    forbidden = np.zeros(10, dtype=bool)
    kept = estimate._drop_forbidden(indices, forbidden, n=10)
    assert kept.tolist() == [0, 3, 9]


# ---------------------------------------------------------------------------
# _cap_by_deviation
# ---------------------------------------------------------------------------


def test_cap_by_deviation_noop_when_within_budget():
    x = np.linspace(0.0, 10.0, 20)
    curve = np.sin(x)
    indices = np.array([0, 5, 10, 19])
    out = estimate._cap_by_deviation(x, curve, indices, n_points=5)
    assert np.array_equal(out, indices)


def test_cap_by_deviation_keeps_endpoints_and_most_deviating():
    x = np.linspace(0.0, 10.0, 11)
    # Chord between endpoints is flat at 0; index 5 deviates the most.
    curve = np.zeros(11)
    curve[5] = 50.0
    curve[2] = 5.0
    indices = np.arange(11)
    out = estimate._cap_by_deviation(x, curve, indices, n_points=3)
    assert out.tolist() == [0, 5, 10]


def test_cap_by_deviation_keep_count_zero_returns_endpoints():
    x = np.linspace(0.0, 10.0, 11)
    curve = np.sin(x)
    indices = np.arange(11)
    out = estimate._cap_by_deviation(x, curve, indices, n_points=2)
    assert out.tolist() == [0, 10]


def test_cap_by_deviation_zero_span_uses_first_interior_slice():
    # Degenerate x (all equal) -> span<=0 branch: take the first
    # ``keep_count`` interior anchors in order.
    x = np.zeros(11)
    curve = np.arange(11, dtype=float)
    indices = np.arange(11)
    out = estimate._cap_by_deviation(x, curve, indices, n_points=4)
    # Endpoints 0 and 10 plus the first two interior indices (1, 2).
    assert out.tolist() == [0, 1, 2, 10]


# ---------------------------------------------------------------------------
# _thin_to_anchors
# ---------------------------------------------------------------------------


def test_thin_to_anchors_uncapped_returns_rdp_result():
    x = np.linspace(0.0, 10.0, 50)
    curve = 1.0 + 0.2 * x
    forbidden = np.zeros(50, dtype=bool)
    out = estimate._thin_to_anchors(x, curve, epsilon=1e-9, forbidden=forbidden, n_points=None)
    assert out.tolist() == [0, 49]


def test_thin_to_anchors_grows_tolerance_to_meet_cap():
    # A finely-wiggling curve yields many RDP anchors at a small tolerance;
    # the growth loop must reduce them to <= n_points.
    x = np.linspace(0.0, 10.0, 400)
    curve = np.sin(8.0 * x)
    forbidden = np.zeros(400, dtype=bool)
    out = estimate._thin_to_anchors(x, curve, epsilon=1e-6, forbidden=forbidden, n_points=8)
    assert out.size <= 8
    assert out[0] == 0
    assert out[-1] == 399


def test_thin_to_anchors_growth_alone_meets_cap():
    # A smooth single-frequency curve: growing the RDP tolerance alone
    # brings the anchor count to the target, so the deviation cap is not
    # needed (the size-already-within-budget branch after the loop).
    x = np.linspace(0.0, 10.0, 400)
    curve = np.sin(1.2 * x)
    forbidden = np.zeros(400, dtype=bool)
    out = estimate._thin_to_anchors(x, curve, epsilon=1e-3, forbidden=forbidden, n_points=12)
    assert out.size <= 12
    assert out[0] == 0
    assert out[-1] == 399


def test_thin_to_anchors_zero_tolerance_falls_back_to_deviation_cap():
    # With epsilon == 0 the growth loop cannot shrink the count (tolerance
    # stays 0), so the deviation-based cap must enforce the bound.
    x = np.linspace(0.0, 10.0, 200)
    curve = np.sin(5.0 * x)
    forbidden = np.zeros(200, dtype=bool)
    out = estimate._thin_to_anchors(x, curve, epsilon=0.0, forbidden=forbidden, n_points=4)
    assert out.size <= 4
    assert out[0] == 0
    assert out[-1] == 199


# ---------------------------------------------------------------------------
# _flat_estimate
# ---------------------------------------------------------------------------


def test_flat_estimate_levels_at_data_minimum():
    x = np.linspace(0.0, 5.0, 6)
    y = np.array([4.0, 2.0, 3.0, 5.0, 2.5, 6.0])
    est = estimate._flat_estimate(x, y, 'arpls', width=None, noise=0.1)
    assert np.all(est.curve == 2.0)
    assert est.anchors.tolist() == [[0.0, 2.0], [5.0, 2.0]]
    assert est.width == estimate._FALLBACK_WIDTH
    assert est.tolerance == pytest.approx(estimate._NOISE_TOLERANCE_FACTOR * 0.1)
    assert est.backend_params == {}


def test_flat_estimate_respects_supplied_width():
    x = np.linspace(0.0, 1.0, 5)
    y = np.ones(5)
    est = estimate._flat_estimate(x, y, 'snip', width=42.0, noise=0.0)
    assert est.width == 42.0
    assert est.method == 'snip'


def test_flat_estimate_handles_empty_arrays():
    est = estimate._flat_estimate(np.array([]), np.array([]), 'arpls', width=None, noise=0.0)
    assert est.curve.size == 0
    assert est.anchors.shape == (0, 2)
    assert est.width == estimate._FALLBACK_WIDTH


# ---------------------------------------------------------------------------
# estimate_background_curve short-pattern path
# ---------------------------------------------------------------------------


def test_short_pattern_returns_flat_estimate_with_warning(monkeypatch):
    records = _collect_warnings(monkeypatch)
    x = np.linspace(0.0, 1.0, 4)  # below _MIN_POINTS (5)
    y = np.array([3.0, 1.0, 2.0, 4.0])
    result = estimate_background_curve(x, y)
    assert isinstance(result, BackgroundEstimate)
    assert result.anchors.shape == (2, 2)
    assert result.curve.size == 4
    assert np.all(result.curve == 1.0)  # flat at the data minimum
    assert any('too short' in r.lower() for r in records)


def test_short_pattern_keeps_supplied_width(monkeypatch):
    _collect_warnings(monkeypatch)
    x = np.linspace(0.0, 1.0, 3)
    y = np.array([2.0, 2.0, 2.0])
    result = estimate_background_curve(x, y, width=7.0)
    assert result.width == 7.0


# ---------------------------------------------------------------------------
# estimate_background_curve width/peaks resolution branches
# ---------------------------------------------------------------------------


def test_supplied_width_and_peaks_skip_detection():
    # Both width and peaks supplied: the detection branch (524->529) is
    # skipped entirely and the supplied values are honoured.
    x = np.linspace(0.0, 10.0, 200)
    y = 4.0 + 0.2 * x + 5.0 * np.exp(-((x - 5.0) ** 2) / (2.0 * 0.2**2))
    mask = (x > 4.5) & (x < 5.5)
    result = estimate_background_curve(x, y, width=8.0, peaks=mask)
    assert result.width == 8.0
    # No interior anchor falls inside the supplied forbidden mask.
    for ax in result.anchors[1:-1, 0]:
        idx = int(np.argmin(np.abs(x - ax)))
        assert not mask[idx]


def test_supplied_peaks_only_still_measures_width():
    # peaks supplied, width None -> width is derived but the supplied mask
    # is used (the width-only branch of 524->529).
    x = np.linspace(0.0, 10.0, 200)
    y = 4.0 + 5.0 * np.exp(-((x - 5.0) ** 2) / (2.0 * 0.2**2))
    mask = np.zeros(200, dtype=bool)
    result = estimate_background_curve(x, y, peaks=mask, width=None)
    assert result.width > 0


def test_supplied_width_only_derives_mask_from_data(monkeypatch):
    # width supplied, peaks None: the detection branch still runs to build
    # the forbidden mask, but the supplied width is honoured verbatim.
    _collect_warnings(monkeypatch)
    x = np.linspace(0.0, 10.0, 300)
    rng = np.random.default_rng(3)
    y = 4.0 + 6.0 * np.exp(-((x - 5.0) ** 2) / (2.0 * 0.2**2)) + rng.normal(0.0, 0.05, size=300)
    result = estimate_background_curve(x, y, width=6.0, peaks=None)
    assert result.width == 6.0
    interior = result.anchors[1:-1, 0]
    # No interior anchor sits on the planted peak (centre 5.0).
    assert not np.any(np.abs(interior - 5.0) < 0.4)


def test_no_peaks_detected_emits_unreliable_warning(monkeypatch):
    records = _collect_warnings(monkeypatch)
    x = np.linspace(0.0, 10.0, 60)
    y = np.full(60, 3.0)  # perfectly flat: no peaks
    estimate_background_curve(x, y, peaks=None)
    assert any('unreliable' in r.lower() for r in records)
