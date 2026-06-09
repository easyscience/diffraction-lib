# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Data-range category base definition.

The data range defines the reciprocal-space region (and, for powder, the
profile step) used to build the calculation grid when no measured scan
exists. Concrete per-type classes live alongside this module.

Defaults are authored in d-spacing (a fixed, instrument-independent
window) and projected onto each stored axis through the instrument, so a
``from_scratch`` experiment is calculable with no manual setup and the
time-of-flight default — meaningless in absolute microseconds without a
calibration — stays well defined. The shared reciprocal currency is
``sinθ/λ = 1/(2·d)``.
"""

from __future__ import annotations

import numpy as np

from easydiffraction.core.category import CategoryItem

# A measured x-grid is treated as uniform when every step is within this
# fraction of the median step; otherwise no representative step is
# reported for the measured range.
_MEASURED_RANGE_UNIFORM_TOLERANCE = 0.01

# Default d-spacing window (Å) authored once and projected onto each
# stored axis. The bounds bracket a typical Bragg powder pattern; users
# override the per-axis values when they need a different range.
DEFAULT_D_SPACING_MIN = 0.5
DEFAULT_D_SPACING_MAX = 10.0

# Default number of calculation points across the window, used to derive
# the powder profile step (``inc``) from the projected axis bounds.
DEFAULT_NUM_POINTS = 1000


class DataRangeBase(CategoryItem):
    """
    Base class for data-range category items.

    Sets the common ``category_code`` shared by the concrete CWL, TOF,
    and single-crystal data-range definitions, and projects the default
    d-spacing window onto the stored axis whenever a bound is still unset.
    """

    _category_code = 'data_range'

    def __init__(self) -> None:
        """Initialize the data-range base."""
        super().__init__()

    # ------------------------------------------------------------------
    #  Defaults projection
    # ------------------------------------------------------------------

    def _update(
        self,
        *,
        called_by_minimizer: bool = False,
    ) -> None:
        """Fill any unset bound before categories that read the range."""
        del called_by_minimizer
        self._ensure_default_range()

    def _ensure_default_range(self) -> None:
        """
        Project the default d-spacing window onto unset axis bounds.

        Subclasses fill their stored ``NaN`` bounds from
        :data:`DEFAULT_D_SPACING_MIN`/:data:`DEFAULT_D_SPACING_MAX`
        through the instrument. The base implementation is a no-op so the
        category stays usable when no projection is defined.
        """

    def _instrument(self) -> object | None:
        """Return the owning experiment's instrument, if any."""
        return getattr(self._parent, 'instrument', None)

    @staticmethod
    def _default_sin_theta_over_lambda_bounds() -> tuple[float, float]:
        """Return the default ``(min, max)`` sinθ/λ window (Å⁻¹)."""
        return (
            1.0 / (2.0 * DEFAULT_D_SPACING_MAX),
            1.0 / (2.0 * DEFAULT_D_SPACING_MIN),
        )

    # ------------------------------------------------------------------
    #  Measured-data subsumption
    # ------------------------------------------------------------------

    def _intensity_category(self) -> object | None:
        """Return the owning experiment's intensity category, if any."""
        parent = self._parent
        resolver = getattr(parent, '_intensity_category', None)
        if resolver is None:
            return None
        try:
            return resolver()
        except AttributeError:
            return None

    def _has_measured_data(self) -> bool:
        """Return whether the experiment holds measured intensities."""
        category = self._intensity_category()
        values = getattr(category, 'intensity_meas', None)
        if values is None:
            return False
        array = np.asarray(values, dtype=float)
        return bool(array.size) and bool(np.any(np.isfinite(array)))

    def _measured_axis_values(self) -> np.ndarray | None:
        """Return measured active-axis values (powder x-grid by default)."""
        category = self._intensity_category()
        values = getattr(category, 'unfiltered_x', None)
        if values is None:
            return None
        return np.asarray(values, dtype=float)

    def _measured_step(self, values: np.ndarray) -> float | None:  # noqa: PLR6301
        """Return the representative step of a measured grid, if uniform."""
        return _representative_step(values)

    def _measured_axis_range(self) -> tuple[float, float, float | None] | None:
        """Return measured ``(min, max, step)`` on the active axis, or None."""
        if not self._has_measured_data():
            return None
        values = self._measured_axis_values()
        if values is None or values.size == 0:
            return None
        values = np.sort(values)
        range_min = float(values[0])
        range_max = float(values[-1])
        if values.size == 1:
            return (range_min, range_max, None)
        return (range_min, range_max, self._measured_step(values))

    def _stored_axis(self) -> tuple[float, float, float | None]:
        """Return stored ``(min, max, inc)`` after projecting defaults."""
        raise NotImplementedError

    def _effective_axis(self) -> tuple[float, float, float | None]:
        """
        Return effective ``(min, max, inc)`` on the active axis.

        Measured-derived while a measured scan is present (``inc`` is
        ``None`` for a non-uniform measured grid), and the stored or
        default range otherwise.
        """
        measured = self._measured_axis_range()
        if measured is not None:
            return measured
        self._ensure_default_range()
        return self._stored_axis()

    def _raise_if_measured(self) -> None:
        """Reject writes to the range while a measured scan is present."""
        if not self._has_measured_data():
            return
        name = getattr(self._parent, 'name', None) or '?'
        msg = (
            f"Cannot set the calculation range for experiment '{name}': it is "
            'determined by the measured data and is read-only while a measured '
            'scan is present.'
        )
        raise ValueError(msg)


def _representative_step(values: np.ndarray) -> float | None:
    """Return a representative step for sorted x-axis values, or None."""
    steps = np.diff(values)
    median_step = float(np.median(steps))
    if median_step == 0:
        return None
    tolerance = abs(median_step) * _MEASURED_RANGE_UNIFORM_TOLERANCE
    if np.max(np.abs(steps - median_step)) > tolerance:
        return None
    return median_step
