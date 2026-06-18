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
    y_ref = reference[:, 1]
    zeros = np.zeros_like(y_ref)
    rms = float(np.sqrt(np.mean(y_ref * y_ref)))
    reference_norm = max(float(np.max(np.abs(y_ref))), 1.0)
    return Comparison(
        label=label,
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


def plot_comparisons(title: str, x_values: np.ndarray, comparisons: Iterable[Comparison]) -> None:
    plt = importlib.import_module('matplotlib.pyplot')
    for comparison in comparisons:
        plt.plot(x_values, comparison.reference, 'o', label=f'{comparison.label} FullProf')
        plt.plot(x_values, comparison.scaled, '-', label=f'{comparison.label} CrysFML')
    plt.title(title)
    plt.xlabel('2theta, TOF, or reflection index')
    plt.ylabel('calculated intensity')
    plt.legend()
    plt.tight_layout()
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
    if np.all(np.isfinite(y_interp)):
        return y_interp, None
    error = 'patterns_simulation returned non-finite intensities.'
    return np.nan_to_num(y_interp, nan=0.0, posinf=0.0, neginf=0.0), error
