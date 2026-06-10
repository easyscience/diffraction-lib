# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from types import SimpleNamespace

import pytest

from easydiffraction.datablocks.experiment.categories.data_range.base import DEFAULT_D_SPACING_MAX
from easydiffraction.datablocks.experiment.categories.data_range.base import DEFAULT_D_SPACING_MIN
from easydiffraction.datablocks.experiment.categories.data_range.sc import ScDataRange


def _parent(*, measured=False, sthovl=None):
    category = SimpleNamespace(sin_theta_over_lambda=sthovl)
    return SimpleNamespace(
        _has_measured_data=lambda: measured,
        _intensity_category=lambda: category,
        name='sim',
    )


def test_default_range_filled_from_d_window_without_instrument():
    dr = ScDataRange()
    dr._parent = _parent()
    assert dr.sin_theta_over_lambda_min.value == pytest.approx(1.0 / (2.0 * DEFAULT_D_SPACING_MAX))
    assert dr.sin_theta_over_lambda_max.value == pytest.approx(1.0 / (2.0 * DEFAULT_D_SPACING_MIN))


def test_single_crystal_has_no_profile_step():
    dr = ScDataRange()
    dr._parent = _parent()
    assert dr.x_step is None
    # _measured_step always reports None for single-crystal reflections.
    assert dr._measured_step([0.1, 0.2, 0.3]) is None


def test_effective_range_from_measured_reflections():
    dr = ScDataRange()
    dr._parent = _parent(measured=True, sthovl=[0.2, 0.1, 0.5])
    assert dr.x_min == pytest.approx(0.1)
    assert dr.x_max == pytest.approx(0.5)
    assert dr.x_step is None


def test_setter_rejected_while_measured():
    dr = ScDataRange()
    dr._parent = _parent(measured=True, sthovl=[0.1, 0.5])
    with pytest.raises(ValueError, match='read-only while a measured'):
        dr.sin_theta_over_lambda_max = 0.8


def test_derived_d_spacing_views():
    dr = ScDataRange()
    dr._parent = _parent()
    dr.sin_theta_over_lambda_min = 0.05
    dr.sin_theta_over_lambda_max = 0.5
    assert dr.d_spacing_max == pytest.approx(1.0 / (2.0 * 0.05))
    assert dr.d_spacing_min == pytest.approx(1.0 / (2.0 * 0.5))
