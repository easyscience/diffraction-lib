# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Automatic background-curve estimation for powder patterns.

Pure, array-in / array-out helpers with no experiment-model state. The
estimator runs in two stages (see the ``background-auto-estimate`` ADR):

* Stage 1 builds a peak-insensitive background curve ``B(x)`` over the
  whole grid using :mod:`pybaselines`.
* Stage 2 thins ``B(x)`` to a sparse set of ``(x, intensity)`` anchors
  with a vertical Ramer-Douglas-Peucker simplification, keeping the
  endpoints and never placing a non-endpoint anchor on a peak.

All per-dataset parameters (peak width, noise, smoothing penalty) are
derived from the data so a bare call needs no tuning. The numeric
constants below are first cuts; they are calibrated against the tutorial
corpus in Phase 2.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from pybaselines import Baseline
from scipy.signal import find_peaks
from scipy.signal import peak_widths

from easydiffraction.utils.logging import log

# Stage-2 RDP tolerance as a multiple of the noise sigma (c in c*sigma).
_NOISE_TOLERANCE_FACTOR = 2.0
# Robust upper percentile of measured peak widths used as the window.
_WIDTH_PERCENTILE = 75.0
# Peak prominence threshold for find_peaks, in units of noise sigma.
_PEAK_PROMINENCE_FACTOR = 3.0
# Relative height at which peak widths are measured (FWHM).
_PEAK_WIDTH_REL_HEIGHT = 0.5
# snip max_half_window as a multiple of the peak width W.
_SNIP_WINDOW_FACTOR = 1.0
# fabc min_length as a multiple of the peak width W.
_FABC_MIN_LENGTH_FACTOR = 1.0
# Second-difference noise inflation: var(diff2) = 6 * var(noise).
_SECOND_DIFF_SCALE = 6.0**0.5
# MAD-to-sigma scaling for a normal distribution.
_MAD_TO_SIGMA = 1.4826
# Floor for the derived Whittaker penalty.
_LAM_FLOOR = 1.0e2
# Smallest pattern (in points) the estimator can work on.
_MIN_POINTS = 5
# Fallback peak width (in points) when no peaks can be detected.
_FALLBACK_WIDTH = 10.0
# Geometric growth of the RDP tolerance when capping the anchor count.
_TOLERANCE_GROWTH = 1.3
# Maximum tolerance-growth iterations when enforcing ``n_points``.
_MAX_CAP_ITERATIONS = 20


@dataclass(frozen=True)
class BackgroundEstimate:
    """
    Result of a background-curve estimation.

    Attributes
    ----------
    curve : np.ndarray
        Dense peak-insensitive background ``B(x)`` over the input grid.
    anchors : np.ndarray
        Thinned control points with shape ``(n_anchors, 2)`` whose rows
        are ``(x, intensity)``; heights are read from ``curve``.
    method : str
        Resolved Stage-1 method actually run (``snip``/``arpls``/
        ``fabc``).
    width : float
        Effective peak width ``W`` in points (supplied, derived, or the
        degenerate-input fallback).
    noise : float
        Robust noise estimate ``sigma`` from the second difference.
    tolerance : float
        Stage-2 RDP tolerance actually used (``c * sigma``).
    backend_params : dict[str, float]
        Parameters handed to the :mod:`pybaselines` routine.
    """

    curve: np.ndarray
    anchors: np.ndarray
    method: str
    width: float
    noise: float
    tolerance: float
    backend_params: dict[str, float]


def _robust_noise(y: np.ndarray) -> float:
    """
    Estimate the noise standard deviation, insensitive to peaks.

    Uses the median absolute deviation (MAD) of the second difference of
    the intensities; the second difference suppresses the smooth
    background and most peak signal, leaving noise.

    Parameters
    ----------
    y : np.ndarray
        Intensities over the grid.

    Returns
    -------
    float
        Estimated noise sigma; ``0.0`` for flat input.
    """
    diff2 = np.diff(y, n=2)
    mad = float(np.median(np.abs(diff2 - np.median(diff2))))
    return _MAD_TO_SIGMA * mad / _SECOND_DIFF_SCALE


def _measure_width(y: np.ndarray, sigma: float) -> tuple[float, np.ndarray]:
    """
    Measure a robust peak width and the prominent peak positions.

    Peaks are found with a prominence threshold relative to the noise
    and their full-width-at-half-maximum is summarised by a high
    percentile, so the window clears the broadest (e.g. high-angle CWL)
    peaks.

    Parameters
    ----------
    y : np.ndarray
        Intensities over the grid.
    sigma : float
        Noise estimate used for the prominence threshold.

    Returns
    -------
    width : float
        Robust peak width in points; the fallback when no peaks are
        found.
    peaks : np.ndarray
        Indices of the detected peaks (possibly empty).
    """
    prominence = _PEAK_PROMINENCE_FACTOR * sigma if sigma > 0 else None
    peaks, _ = find_peaks(y, prominence=prominence)
    if not peaks.size:
        return _FALLBACK_WIDTH, peaks
    widths = peak_widths(y, peaks, rel_height=_PEAK_WIDTH_REL_HEIGHT)[0]
    width = float(np.percentile(widths, _WIDTH_PERCENTILE))
    return max(width, 1.0), peaks


def _forbidden_from_peaks(n: int, peaks: np.ndarray, width: float) -> np.ndarray:
    """
    Build a peak-region mask from detected peak positions.

    Each peak is widened by ``+/- width`` points; Stage 2 must not place
    a non-endpoint anchor on a masked sample.

    Parameters
    ----------
    n : int
        Number of grid points.
    peaks : np.ndarray
        Indices of detected peaks.
    width : float
        Half-width (in points) masked around each peak.

    Returns
    -------
    np.ndarray
        Boolean mask of length ``n``; ``True`` marks a peak region.
    """
    mask = np.zeros(n, dtype=bool)
    half = int(np.ceil(width))
    for peak in peaks:
        lo = max(0, int(peak) - half)
        hi = min(n, int(peak) + half + 1)
        mask[lo:hi] = True
    return mask


def _derive_lam(n: int, width: float) -> float:
    """
    Derive a Whittaker smoothing penalty for arPLS/fabc.

    The penalty grows with the grid size and the peak width so the
    baseline stays smooth under broad features. The scaling is a
    monotonic first cut; the constant is calibrated in Phase 2.

    Parameters
    ----------
    n : int
        Number of grid points.
    width : float
        Peak width in points.

    Returns
    -------
    float
        The ``lam`` penalty passed to the backend.
    """
    return float(max(_LAM_FLOOR, n * max(width, 1.0)))


def _stage1_baseline(
    x: np.ndarray,
    y: np.ndarray,
    method: str,
    width: float,
    smoothness: float | None,
) -> tuple[np.ndarray, dict[str, float]]:
    """
    Compute the Stage-1 background curve via pybaselines.

    Dispatches to the resolved ``method`` and maps the derived width and
    optional smoothness onto the backend parameters (the plan's backend
    dispatch contract).

    Parameters
    ----------
    x : np.ndarray
        Grid coordinates.
    y : np.ndarray
        Intensities (data-only or peak-subtracted) to baseline.
    method : str
        Resolved method: ``snip``, ``arpls`` or ``fabc``.
    width : float
        Peak width in points.
    smoothness : float | None
        Optional Whittaker penalty override.

    Returns
    -------
    curve : np.ndarray
        Estimated background over the grid.
    backend_params : dict[str, float]
        Parameters passed to the backend.

    Raises
    ------
    ValueError
        If ``method`` is not a supported Stage-1 routine.
    """
    fitter = Baseline(x_data=x)
    if method == 'arpls':
        lam = smoothness if smoothness is not None else _derive_lam(y.size, width)
        curve, _ = fitter.arpls(y, lam=lam)
        return curve, {'lam': float(lam)}
    if method == 'snip':
        if smoothness is not None:
            log.warning("Method 'snip' ignores the 'smoothness' parameter.")
        max_half_window = int(np.ceil(_SNIP_WINDOW_FACTOR * width))
        curve, _ = fitter.snip(y, max_half_window=max_half_window)
        return curve, {'max_half_window': float(max_half_window)}
    if method == 'fabc':
        lam = smoothness if smoothness is not None else _derive_lam(y.size, width)
        scale = int(np.ceil(width))
        min_length = int(np.ceil(_FABC_MIN_LENGTH_FACTOR * width))
        curve, _ = fitter.fabc(y, lam=lam, scale=scale, min_length=min_length)
        return curve, {'lam': float(lam), 'scale': float(scale), 'min_length': float(min_length)}
    msg = f'Unsupported Stage-1 background method: {method!r}'
    raise ValueError(msg)


def _rdp_indices(x: np.ndarray, curve: np.ndarray, epsilon: float) -> np.ndarray:
    """
    Vertical Ramer-Douglas-Peucker simplification of a curve.

    Returns the indices of the points to keep so that every dropped
    point lies within ``epsilon`` (in intensity units) of the
    piecewise-linear interpolation through the kept points. The
    endpoints are always kept.

    Parameters
    ----------
    x : np.ndarray
        Monotonic grid coordinates.
    curve : np.ndarray
        Curve values to simplify.
    epsilon : float
        Maximum allowed vertical deviation.

    Returns
    -------
    np.ndarray
        Sorted indices of the retained points.
    """
    n = x.size
    keep = np.zeros(n, dtype=bool)
    keep[0] = True
    keep[-1] = True
    stack = [(0, n - 1)]
    while stack:
        start, end = stack.pop()
        if end <= start + 1:
            continue
        span = x[end] - x[start]
        if span <= 0:
            continue
        segment = slice(start, end + 1)
        line = curve[start] + (curve[end] - curve[start]) * (x[segment] - x[start]) / span
        deviation = np.abs(curve[segment] - line)
        deviation[0] = 0.0
        deviation[-1] = 0.0
        local = int(np.argmax(deviation))
        if deviation[local] > epsilon:
            index = start + local
            keep[index] = True
            stack.append((start, index))
            stack.append((index, end))
    return np.flatnonzero(keep)


def _drop_forbidden(indices: np.ndarray, forbidden: np.ndarray, n: int) -> np.ndarray:
    """
    Drop non-endpoint anchors that fall on a forbidden (peak) sample.

    Parameters
    ----------
    indices : np.ndarray
        Candidate anchor indices (sorted, includes the endpoints).
    forbidden : np.ndarray
        Boolean peak-region mask.
    n : int
        Number of grid points, used to identify the endpoints.

    Returns
    -------
    np.ndarray
        Filtered indices, always retaining ``0`` and ``n - 1``.
    """
    endpoints = {0, n - 1}
    kept = [int(i) for i in indices if int(i) in endpoints or not forbidden[i]]
    return np.array(sorted(set(kept)), dtype=int)


def _cap_by_deviation(
    x: np.ndarray,
    curve: np.ndarray,
    indices: np.ndarray,
    n_points: int,
) -> np.ndarray:
    """
    Reduce anchors to ``n_points``, keeping the endpoints.

    The two endpoints are always retained; the remaining slots go to the
    interior anchors that deviate most from the straight chord between
    them. Guarantees the cap even when the RDP tolerance cannot reduce
    the count (e.g. zero-noise data, where the tolerance stays zero).

    Parameters
    ----------
    x : np.ndarray
        Grid coordinates.
    curve : np.ndarray
        Background curve.
    indices : np.ndarray
        Candidate anchor indices (sorted, includes the endpoints).
    n_points : int
        Target maximum number of anchors (``>= 2``).

    Returns
    -------
    np.ndarray
        ``min(indices.size, n_points)`` sorted indices.
    """
    if indices.size <= n_points:
        return indices
    first = indices[0]
    last = indices[-1]
    interior = indices[1:-1]
    keep_count = max(n_points - 2, 0)
    span = x[last] - x[first]
    if span <= 0 or keep_count == 0:
        chosen = interior[:keep_count]
    else:
        line = curve[first] + (curve[last] - curve[first]) * (x[interior] - x[first]) / span
        deviation = np.abs(curve[interior] - line)
        start = interior.size - keep_count
        chosen = interior[np.sort(np.argsort(deviation)[start:])]
    return np.concatenate(([first], chosen, [last]))


def _thin_to_anchors(
    x: np.ndarray,
    curve: np.ndarray,
    epsilon: float,
    forbidden: np.ndarray,
    n_points: int | None,
) -> np.ndarray:
    """
    Select anchor indices: RDP, drop peak-region anchors, cap the count.

    When more than ``n_points`` anchors survive, the RDP tolerance is
    grown geometrically and re-run until the count fits; if that cannot
    reduce it (e.g. zero noise), a deviation-based cap guarantees the
    bound. The endpoints are always retained.

    Parameters
    ----------
    x : np.ndarray
        Grid coordinates.
    curve : np.ndarray
        Background curve to thin.
    epsilon : float
        RDP tolerance (intensity units).
    forbidden : np.ndarray
        Boolean peak-region mask; non-endpoint anchors here are dropped.
    n_points : int | None
        Optional maximum number of anchors (endpoints included).

    Returns
    -------
    np.ndarray
        Sorted anchor indices, always including the two endpoints.
    """
    indices = _drop_forbidden(_rdp_indices(x, curve, epsilon), forbidden, x.size)
    if n_points is None or indices.size <= n_points:
        return indices
    tolerance = epsilon
    for _ in range(_MAX_CAP_ITERATIONS):
        if tolerance <= 0 or indices.size <= n_points:
            break
        tolerance *= _TOLERANCE_GROWTH
        indices = _drop_forbidden(_rdp_indices(x, curve, tolerance), forbidden, x.size)
    if indices.size > n_points:
        indices = _cap_by_deviation(x, curve, indices, n_points)
    return indices


def _flat_estimate(
    x: np.ndarray,
    y: np.ndarray,
    method: str,
    width: float | None,
    noise: float,
) -> BackgroundEstimate:
    """
    Build a trivial flat-background estimate for degenerate input.

    Parameters
    ----------
    x : np.ndarray
        Grid coordinates.
    y : np.ndarray
        Intensities.
    method : str
        Resolved method (recorded for the summary).
    width : float | None
        Supplied width, if any.
    noise : float
        Noise estimate.

    Returns
    -------
    BackgroundEstimate
        A flat curve at the data minimum with two endpoint anchors.
    """
    level = float(np.min(y)) if y.size else 0.0
    curve = np.full(x.size, level)
    anchors = np.array([[x[0], level], [x[-1], level]]) if x.size else np.empty((0, 2))
    return BackgroundEstimate(
        curve=curve,
        anchors=anchors,
        method=method,
        width=float(width) if width is not None else _FALLBACK_WIDTH,
        noise=noise,
        tolerance=_NOISE_TOLERANCE_FACTOR * noise,
        backend_params={},
    )


def estimate_background_curve(
    x: np.ndarray,
    y: np.ndarray,
    *,
    method: str = 'arpls',
    peaks: np.ndarray | None = None,
    width: float | None = None,
    smoothness: float | None = None,
    n_points: int | None = None,
) -> BackgroundEstimate:
    """
    Estimate background control points from a measured pattern.

    Stage 1 builds a peak-insensitive curve ``B(x)`` with the resolved
    ``method``; Stage 2 thins it to sparse anchors. Every per-dataset
    parameter defaults to a data-derived value, so a bare call works.

    Parameters
    ----------
    x : np.ndarray
        Grid coordinates (e.g. 2theta or time-of-flight), monotonic.
    y : np.ndarray
        Intensities to baseline: the measured pattern (data-only) or the
        peak-subtracted measured pattern (model-guided).
    method : str, default='arpls'
        Resolved Stage-1 routine: ``arpls`` (default), ``snip`` or
        ``fabc``. ``auto`` is resolved by the caller, never here.
    peaks : np.ndarray | None, default=None
        Boolean mask aligned with ``x``; ``True`` forbids a non-endpoint
        anchor. When ``None`` the mask is derived from ``y`` itself.
    width : float | None, default=None
        Peak width in points; derived from ``y`` when ``None``.
    smoothness : float | None, default=None
        Whittaker penalty override for ``arpls``/``fabc``; ignored by
        ``snip``.
    n_points : int | None, default=None
        Maximum number of anchors (endpoints included); uncapped when
        ``None``.

    Returns
    -------
    BackgroundEstimate
        The curve, anchors, and metadata describing the run.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    noise = _robust_noise(y)

    if y.size < _MIN_POINTS:
        log.warning('Pattern too short to estimate a background; returning a flat one.')
        return _flat_estimate(x, y, method, width, noise)

    detected: np.ndarray = np.array([], dtype=int)
    if width is None or peaks is None:
        measured_width, detected = _measure_width(y, noise)
        if width is None:
            width = measured_width

    if peaks is None:
        forbidden = _forbidden_from_peaks(y.size, detected, width)
        if not detected.size:
            log.warning('No peaks detected; background anchors may be unreliable.')
    else:
        forbidden = np.asarray(peaks, dtype=bool)

    curve, backend_params = _stage1_baseline(x, y, method, width, smoothness)
    tolerance = _NOISE_TOLERANCE_FACTOR * noise
    indices = _thin_to_anchors(x, curve, tolerance, forbidden, n_points)
    anchors = np.column_stack((x[indices], curve[indices]))
    return BackgroundEstimate(
        curve=curve,
        anchors=anchors,
        method=method,
        width=float(width),
        noise=noise,
        tolerance=float(tolerance),
        backend_params=backend_params,
    )
