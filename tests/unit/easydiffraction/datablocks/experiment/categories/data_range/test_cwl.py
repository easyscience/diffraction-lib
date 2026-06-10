# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import math
from types import SimpleNamespace

import pytest

from easydiffraction.datablocks.experiment.categories.data_range.base import DEFAULT_NUM_POINTS
from easydiffraction.datablocks.experiment.categories.data_range.cwl import _DEFAULT_MAX_TWO_THETA
from easydiffraction.datablocks.experiment.categories.data_range.cwl import CwlPdDataRange


def _parent(*, wavelength=None, measured=False, x=None):
    instrument = (
        SimpleNamespace(setup_wavelength=SimpleNamespace(value=wavelength))
        if wavelength is not None
        else None
    )
    category = SimpleNamespace(unfiltered_x=x)
    return SimpleNamespace(
        instrument=instrument,
        _has_measured_data=lambda: measured,
        _intensity_category=lambda: category,
        name='sim',
    )


def test_default_range_projected_from_wavelength():
    dr = CwlPdDataRange()
    dr._parent = _parent(wavelength=1.5)

    sthovl_min, sthovl_max = dr._default_sin_theta_over_lambda_bounds()
    expected_min = dr._two_theta_from_sin_theta_over_lambda(sthovl_min, 1.5)
    expected_max = min(
        dr._two_theta_from_sin_theta_over_lambda(sthovl_max, 1.5), _DEFAULT_MAX_TWO_THETA
    )

    assert dr.two_theta_min.value == pytest.approx(expected_min)
    assert dr.two_theta_max.value == pytest.approx(expected_max)
    assert dr.two_theta_inc.value == pytest.approx(
        (expected_max - expected_min) / (DEFAULT_NUM_POINTS - 1)
    )


def test_default_upper_bound_capped_at_backscattering_limit():
    dr = CwlPdDataRange()
    dr._parent = _parent(wavelength=2.0)
    # A long wavelength would project past 180°, so the default is capped.
    assert dr.two_theta_max.value == pytest.approx(_DEFAULT_MAX_TWO_THETA)


def test_bounds_stay_nan_without_wavelength():
    dr = CwlPdDataRange()
    dr._parent = _parent(wavelength=None)
    assert math.isnan(dr.two_theta_min.value)
    assert math.isnan(dr.two_theta_max.value)


def test_effective_range_from_measured_scan():
    dr = CwlPdDataRange()
    dr._parent = _parent(measured=True, x=[10.0, 10.5, 11.0, 11.5])
    assert dr.x_min == pytest.approx(10.0)
    assert dr.x_max == pytest.approx(11.5)
    assert dr.x_step == pytest.approx(0.5)


def test_setter_rejected_while_measured():
    dr = CwlPdDataRange()
    dr._parent = _parent(measured=True, x=[10.0, 11.0])
    with pytest.raises(ValueError, match='read-only while a measured'):
        dr.two_theta_min = 5.0


def test_setter_updates_bound_without_measured_scan():
    dr = CwlPdDataRange()
    dr._parent = _parent(wavelength=1.5)
    dr.two_theta_min = 12.0
    assert dr.two_theta_min.value == pytest.approx(12.0)


def test_derived_reciprocal_views_consistent_with_bounds():
    dr = CwlPdDataRange()
    dr._parent = _parent(wavelength=1.5)
    dr.two_theta_min = 20.0
    dr.two_theta_max = 80.0
    # sinθ/λ increases with 2θ.
    assert dr.sin_theta_over_lambda_min < dr.sin_theta_over_lambda_max
    # Largest d-spacing sits at the lower 2θ bound.
    assert dr.d_spacing_max > dr.d_spacing_min
