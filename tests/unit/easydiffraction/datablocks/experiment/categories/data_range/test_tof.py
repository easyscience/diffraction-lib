# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import math
from types import SimpleNamespace

import pytest

from easydiffraction.datablocks.experiment.categories.data_range.base import DEFAULT_D_SPACING_MAX
from easydiffraction.datablocks.experiment.categories.data_range.base import DEFAULT_D_SPACING_MIN
from easydiffraction.datablocks.experiment.categories.data_range.base import DEFAULT_NUM_POINTS
from easydiffraction.datablocks.experiment.categories.data_range.tof import TofPdDataRange


def _parent(*, calib=None, measured=False, x=None):
    if calib is not None:
        offset, linear, quad = calib
        instrument = SimpleNamespace(
            calib_d_to_tof_offset=SimpleNamespace(value=offset),
            calib_d_to_tof_linear=SimpleNamespace(value=linear),
            calib_d_to_tof_quad=SimpleNamespace(value=quad),
        )
    else:
        instrument = None
    category = SimpleNamespace(unfiltered_x=x)
    return SimpleNamespace(
        instrument=instrument,
        _has_measured_data=lambda: measured,
        _intensity_category=lambda: category,
        name='sim',
    )


def test_tof_from_d_quadratic_calibration():
    assert TofPdDataRange._tof_from_d(2.0, 100.0, 1000.0, -5.0) == pytest.approx(
        100.0 + 1000.0 * 2.0 - 5.0 * 4.0
    )


def test_default_range_projected_from_calibration():
    offset, linear, quad = 0.0, 7000.0, -1.0
    dr = TofPdDataRange()
    dr._parent = _parent(calib=(offset, linear, quad))

    expected_min = dr._tof_from_d(DEFAULT_D_SPACING_MIN, offset, linear, quad)
    expected_max = dr._tof_from_d(DEFAULT_D_SPACING_MAX, offset, linear, quad)

    assert dr.time_of_flight_min.value == pytest.approx(expected_min)
    assert dr.time_of_flight_max.value == pytest.approx(expected_max)
    assert dr.time_of_flight_inc.value == pytest.approx(
        (expected_max - expected_min) / (DEFAULT_NUM_POINTS - 1)
    )


def test_bounds_stay_nan_without_calibration():
    dr = TofPdDataRange()
    dr._parent = _parent(calib=None)
    assert math.isnan(dr.time_of_flight_min.value)
    assert math.isnan(dr.time_of_flight_max.value)


def test_effective_range_from_measured_scan():
    dr = TofPdDataRange()
    dr._parent = _parent(measured=True, x=[10000.0, 10002.0, 10004.0])
    assert dr.x_min == pytest.approx(10000.0)
    assert dr.x_max == pytest.approx(10004.0)
    assert dr.x_step == pytest.approx(2.0)


def test_setter_rejected_while_measured():
    dr = TofPdDataRange()
    dr._parent = _parent(measured=True, x=[10000.0, 10002.0])
    with pytest.raises(ValueError, match='read-only while a measured'):
        dr.time_of_flight_max = 40000.0


def test_derived_d_spacing_views_from_calibration():
    dr = TofPdDataRange()
    dr._parent = _parent(calib=(0.0, 7000.0, -1.0))
    dr.time_of_flight_min = 5000.0
    dr.time_of_flight_max = 15000.0
    # Larger TOF maps to larger d-spacing for a positive linear term.
    assert dr.d_spacing_max > dr.d_spacing_min
    assert dr.sin_theta_over_lambda_max > dr.sin_theta_over_lambda_min
