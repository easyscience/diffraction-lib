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

from easydiffraction.core.category import CategoryItem

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
