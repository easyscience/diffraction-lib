# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Calculator-independent CW Lorentz-polarization correction factor.

The public instrument stores the physical monochromator angle in
degrees. Backends that expose the FullProf/Cryspy form consume ``cthm =
cos^2(2theta_m)``, while backends without a native field use the same
value in the pointwise multiplier here.
"""

from __future__ import annotations

import numpy as np


def monochromator_cthm(two_theta_m: float) -> float:
    """
    Return the backend monochromator ``cthm`` value.

    Parameters
    ----------
    two_theta_m : float
        Pre-specimen monochromator 2-theta angle in degrees.

    Returns
    -------
    float
        ``cos^2(two_theta_m)`` with the angle interpreted in degrees.
    """
    return float(np.cos(np.radians(two_theta_m)) ** 2)


def lp_factor(
    two_theta: np.ndarray,
    polarization_coefficient: float,
    cthm: float,
) -> np.ndarray:
    """
    Return the CW Lorentz-polarization multiplier.

    Parameters
    ----------
    two_theta : np.ndarray
        Scattering angle 2-theta grid in degrees.
    polarization_coefficient : float
        Dimensionless polarization coefficient, ``0`` to ``1``.
    cthm : float
        Monochromator factor ``cos^2(two_theta_m)``.

    Returns
    -------
    np.ndarray
        Multiplicative Lorentz-polarization factor.
    """
    two_theta = np.asarray(two_theta, dtype=float)
    cos2 = np.cos(np.radians(two_theta)) ** 2
    return 1.0 - polarization_coefficient + polarization_coefficient * cthm * cos2


def apply(y: object, experiment: object) -> object:
    """
    Apply the CW Lorentz-polarization factor to calculated intensities.

    The pattern is returned unchanged unless the experiment has an X-ray
    CW powder instrument with a nonzero polarization coefficient. Empty
    arrays and backend no-data paths whose shape does not match the
    experiment 2-theta grid are also left unchanged.

    Parameters
    ----------
    y : object
        Calculated intensities (NumPy array or list).
    experiment : object
        Experiment providing ``instrument`` and ``data.x``.

    Returns
    -------
    object
        Corrected intensities, or ``y`` unchanged when no correction
        applies.
    """
    instrument = getattr(experiment, 'instrument', None)
    if not _instrument_exposes_polarization(instrument):
        return y

    coefficient = instrument.setup_polarization_coefficient.value
    if not coefficient:
        return y

    y_values = np.asarray(y, dtype=float)
    two_theta = np.asarray(experiment.data.x, dtype=float)
    if y_values.size == 0 or y_values.shape != two_theta.shape:
        return y

    cthm = monochromator_cthm(instrument.setup_monochromator_twotheta.value)
    return y_values * lp_factor(two_theta, coefficient, cthm)


def _instrument_exposes_polarization(instrument: object | None) -> bool:
    """Return whether an instrument has polarization attributes."""
    if instrument is None:
        return False
    if hasattr(type(instrument), 'setup_polarization_coefficient'):
        return True
    try:
        attrs = vars(instrument)
    except TypeError:
        return False
    return 'setup_polarization_coefficient' in attrs
