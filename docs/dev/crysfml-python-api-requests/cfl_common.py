from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from collections.abc import Iterable

try:
    from pycrysfml import cfml_py_utilities
except ImportError:
    from crysfml import cfml_py_utilities


@dataclass(frozen=True)
class Comparison:
    label: str
    x_values: np.ndarray
    reference: np.ndarray
    calculated: np.ndarray
    scaled: np.ndarray
    scale: float
    rms: float
    relative_rms: float
    max_abs_delta: float
    error: str | None


def fullprof_array(values: list[list[float]]) -> np.ndarray:
    return np.asarray(values, dtype=float)


def simulate_cfl(cfl: str) -> tuple[np.ndarray, np.ndarray]:
    lines = [line.rstrip() for line in cfl.strip().splitlines()]
    patterns = cfml_py_utilities.patterns_simulation(lines)
    if not patterns:
        msg = 'patterns_simulation returned no patterns.'
        raise RuntimeError(msg)
    pattern = patterns[0]
    return np.asarray(pattern['x'], dtype=float), np.asarray(pattern['y'], dtype=float)


def compare_to_fullprof(
    label: str,
    cfl: str,
    reference: np.ndarray,
    *,
    x_shift: float = 0.0,
    scale_override: float | None = None,
) -> Comparison:
    x_ref = reference[:, 0]
    y_ref = reference[:, 1]
    error = None
    try:
        y_interp, error = _interpolate_cfl(cfl, x_ref, x_shift)
    except Exception as exc:  # noqa: BLE001 - diagnostic scripts must keep running.
        error = f'{type(exc).__name__}: {exc}'
        y_interp = np.zeros_like(y_ref)
    scale = least_squares_scale(y_ref, y_interp) if scale_override is None else scale_override
    y_scaled = y_interp * scale
    delta = y_ref - y_scaled
    rms = float(np.sqrt(np.mean(delta * delta)))
    relative_rms = rms / max(float(np.max(np.abs(y_ref))), 1.0)
    return Comparison(
        label=label,
        x_values=x_ref,
        reference=y_ref,
        calculated=y_interp,
        scaled=y_scaled,
        scale=scale,
        rms=rms,
        relative_rms=relative_rms,
        max_abs_delta=float(np.max(np.abs(delta))),
        error=error,
    )


def compare_unavailable(label: str, reference: np.ndarray, reason: str) -> Comparison:
    x_ref = reference[:, 0]
    y_ref = reference[:, 1]
    zeros = np.zeros_like(y_ref)
    rms = float(np.sqrt(np.mean(y_ref * y_ref)))
    reference_norm = max(float(np.max(np.abs(y_ref))), 1.0)
    return Comparison(
        label=label,
        x_values=x_ref,
        reference=y_ref,
        calculated=zeros,
        scaled=zeros,
        scale=0.0,
        rms=rms,
        relative_rms=rms / reference_norm,
        max_abs_delta=float(np.max(np.abs(y_ref))),
        error=reason,
    )


def least_squares_scale(reference: np.ndarray, calculated: np.ndarray) -> float:
    denominator = float(np.dot(calculated, calculated))
    if denominator <= np.finfo(float).tiny:
        return 0.0
    return float(np.dot(reference, calculated) / denominator)


def print_summary(title: str, comparisons: Iterable[Comparison]) -> None:
    print(f'\n{title}')
    print('-' * len(title))
    for comparison in comparisons:
        print(f'{comparison.label}')
        print(f'  scale applied to CrysFML: {comparison.scale:.8g}')
        print(f'  RMS delta:               {comparison.rms:.8g}')
        print(f'  relative RMS:            {comparison.relative_rms:.6f}')
        print(f'  max abs delta:           {comparison.max_abs_delta:.8g}')
        if comparison.error is not None:
            print(f'  CrysFML status:          {comparison.error}')


def print_reference_window(name: str, reference: np.ndarray) -> None:
    print(f'\n{name}')
    print('-' * len(name))
    for x_value, y_value in reference:
        print(f'{x_value:12.6g} {y_value:14.8g}')


def plot_comparisons(title: str, comparisons: Iterable[Comparison]) -> None:
    plt = importlib.import_module('matplotlib.pyplot')
    comparisons = list(comparisons)
    figure_height = max(5.25, 4.5 * len(comparisons))
    _, axes = plt.subplots(len(comparisons), 1, figsize=(9.5, figure_height))
    if len(comparisons) == 1:
        axes = [axes]

    for axis, comparison in zip(axes, comparisons, strict=True):
        residual = comparison.reference - comparison.scaled
        axis.plot(
            comparison.x_values,
            comparison.reference,
            color='tab:blue',
            linestyle='-',
            linewidth=2.2,
            label='FullProf',
            zorder=2,
        )
        axis.plot(
            comparison.x_values,
            comparison.scaled,
            color='tab:red',
            linestyle='--',
            linewidth=2.0,
            label='CrysFML',
            zorder=3,
        )
        axis.plot(
            comparison.x_values,
            residual,
            color='tab:green',
            linestyle='-',
            linewidth=1.5,
            label='residual',
            zorder=1,
        )
        axis.axhline(0.0, color='0.65', linewidth=0.8)
        axis.set_title(comparison.label)
        axis.set_xlabel('2theta, TOF, or reflection index')
        axis.set_ylabel('intensity / residual')
        axis.legend()

    plt.suptitle(title)
    plt.tight_layout(rect=(0.0, 0.0, 1.0, 0.97))
    plt.show()


def should_plot(argv: list[str]) -> bool:
    return '--plot' in argv


def _interpolate_cfl(
    cfl: str,
    x_ref: np.ndarray,
    x_shift: float,
) -> tuple[np.ndarray, str | None]:
    x_calc, y_calc = simulate_cfl(cfl)
    x_calc += x_shift
    y_interp = np.interp(x_ref, x_calc, y_calc, left=0.0, right=0.0)
    _restore_close_endpoint_values(x_ref, x_calc, y_calc, y_interp)
    if np.all(np.isfinite(y_interp)):
        return y_interp, None
    error = 'patterns_simulation returned non-finite intensities.'
    return np.nan_to_num(y_interp, nan=0.0, posinf=0.0, neginf=0.0), error


def _restore_close_endpoint_values(
    x_ref: np.ndarray,
    x_calc: np.ndarray,
    y_calc: np.ndarray,
    y_interp: np.ndarray,
) -> None:
    tolerance = 1e-5
    if x_ref[0] < x_calc[0] and np.isclose(x_ref[0], x_calc[0], atol=tolerance, rtol=0.0):
        y_interp[0] = y_calc[0]
    if x_ref[-1] > x_calc[-1] and np.isclose(x_ref[-1], x_calc[-1], atol=tolerance, rtol=0.0):
        y_interp[-1] = y_calc[-1]
