# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Calculator-independent sample-absorption correction factor.

The correction is a slowly varying envelope of ``sin^2(theta)``, so it
is applied pointwise to the calculated pattern by both backends rather
than per reflection. This keeps the cryspy and crysfml results
bit-for-bit consistent on the absorption term.
"""

from __future__ import annotations

import numpy as np

from easydiffraction.datablocks.experiment.item.enums import AbsorptionTypeEnum
from easydiffraction.utils.logging import log

# Upper muR for which the Hewat cylindrical expansion is validated to
# four decimals against FullProf. Beyond this a Lobanov form is
# preferable; the current code extrapolates and warns rather than fails.
HEWAT_MAX_VALIDATED_MU_R = 1.5

# muR values already warned about, so the out-of-range warning fires
# once per distinct value rather than on every pattern evaluation during
# a refinement.
_WARNED_MU_R: set[float] = set()


def factor(two_theta: np.ndarray, absorption: object) -> np.ndarray:
    """
    Return the per-point sample-absorption correction A.

    Parameters
    ----------
    two_theta : np.ndarray
        Scattering angle 2-theta grid in degrees.
    absorption : object
        Active absorption category (its ``type_info.tag`` selects the
        correction form).

    Returns
    -------
    np.ndarray
        Multiplicative correction A with the same shape as
        ``two_theta``; all ones when no correction applies.
    """
    two_theta = np.asarray(two_theta, dtype=float)
    tag = absorption.type_info.tag
    if tag == AbsorptionTypeEnum.CYLINDER_HEWAT.value:
        return _hewat_cylinder(two_theta, absorption.mu_r.value)
    return np.ones_like(two_theta)


def _hewat_cylinder(two_theta: np.ndarray, mu_r: float) -> np.ndarray:
    """
    Return the Hewat cylindrical Debye-Scherrer absorption factor.

    Parameters
    ----------
    two_theta : np.ndarray
        Scattering angle 2-theta grid in degrees.
    mu_r : float
        Linear absorption coefficient times sample radius (muR).

    Returns
    -------
    np.ndarray
        ``A = exp(-(1.7133 - 0.0368 sin^2 t) muR
        + (0.0927 + 0.375 sin^2 t) muR^2)``.
    """
    if mu_r > HEWAT_MAX_VALIDATED_MU_R:
        rounded = round(mu_r, 4)
        if rounded not in _WARNED_MU_R:
            _WARNED_MU_R.add(rounded)
            log.warning(
                f'Absorption muR={mu_r:g} exceeds the Hewat-validated '
                f'range (<= {HEWAT_MAX_VALIDATED_MU_R}); the result is '
                'extrapolated. A Lobanov form is preferable for large muR.'
            )
    theta = np.radians(two_theta) / 2.0
    sin2 = np.sin(theta) ** 2
    return np.exp(-(1.7133 - 0.0368 * sin2) * mu_r + (0.0927 + 0.375 * sin2) * mu_r**2)
