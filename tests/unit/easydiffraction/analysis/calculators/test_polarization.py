# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for the Lorentz-polarization helper."""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from easydiffraction.analysis.calculators import polarization
from easydiffraction.datablocks.experiment.categories.instrument.cwl import CwlPdNeutronInstrument
from easydiffraction.datablocks.experiment.categories.instrument.cwl import CwlPdXrayInstrument


def test_monochromator_cthm_zero_angle_is_one():
    assert polarization.monochromator_cthm(0.0) == pytest.approx(1.0)


def test_monochromator_cthm_matches_cos_squared_identity():
    assert polarization.monochromator_cthm(60.0) == pytest.approx(0.25)


def test_lp_factor_is_one_when_coefficient_is_zero():
    two_theta = np.array([0.0, 45.0, 90.0])

    factor = polarization.lp_factor(two_theta, 0.0, 0.25)

    np.testing.assert_allclose(factor, np.ones_like(two_theta))


def test_apply_is_noop_for_neutron_instrument():
    y = np.array([1.0, 2.0, 3.0])
    experiment = SimpleNamespace(
        instrument=CwlPdNeutronInstrument(),
        data=SimpleNamespace(x=np.array([10.0, 20.0, 30.0])),
    )

    result = polarization.apply(y, experiment)

    assert result is y


def test_apply_multiplies_xray_pattern():
    y = np.array([2.0, 2.0, 2.0])
    instrument = CwlPdXrayInstrument()
    instrument.setup_polarization_coefficient = 0.5
    instrument.setup_monochromator_twotheta = 60.0
    two_theta = np.array([0.0, 45.0, 90.0])
    experiment = SimpleNamespace(
        instrument=instrument,
        data=SimpleNamespace(x=two_theta),
    )

    result = polarization.apply(y, experiment)

    expected = y * polarization.lp_factor(two_theta, 0.5, 0.25)
    np.testing.assert_allclose(result, expected)
