# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from types import SimpleNamespace

import numpy as np
import pytest

from easydiffraction.datablocks.experiment.categories.data_range.base import DEFAULT_D_SPACING_MAX
from easydiffraction.datablocks.experiment.categories.data_range.base import DEFAULT_D_SPACING_MIN
from easydiffraction.datablocks.experiment.categories.data_range.base import DataRangeBase
from easydiffraction.datablocks.experiment.categories.data_range.base import _representative_step


def test_representative_step_uniform_grid_returns_step():
    values = np.array([0.0, 0.5, 1.0, 1.5, 2.0])
    assert _representative_step(values) == pytest.approx(0.5)


def test_representative_step_non_uniform_grid_returns_none():
    values = np.array([0.0, 0.5, 1.0, 5.0])
    assert _representative_step(values) is None


def test_representative_step_zero_median_returns_none():
    values = np.array([1.0, 1.0, 1.0])
    assert _representative_step(values) is None


def test_default_sin_theta_over_lambda_bounds_from_d_window():
    lo, hi = DataRangeBase._default_sin_theta_over_lambda_bounds()
    assert lo == pytest.approx(1.0 / (2.0 * DEFAULT_D_SPACING_MAX))
    assert hi == pytest.approx(1.0 / (2.0 * DEFAULT_D_SPACING_MIN))


def test_has_measured_data_false_when_parent_lacks_checker():
    base = DataRangeBase()
    base._parent = None
    assert base._has_measured_data() is False


def test_has_measured_data_delegates_to_parent():
    base = DataRangeBase()
    base._parent = SimpleNamespace(_has_measured_data=lambda: True)
    assert base._has_measured_data() is True


def test_measured_axis_range_none_without_measured_data():
    base = DataRangeBase()
    base._parent = SimpleNamespace(_has_measured_data=lambda: False)
    assert base._measured_axis_range() is None


def test_measured_axis_range_uniform_grid_reports_step():
    base = DataRangeBase()
    category = SimpleNamespace(unfiltered_x=[2.0, 1.0, 3.0, 4.0])  # unsorted on purpose
    base._parent = SimpleNamespace(
        _has_measured_data=lambda: True,
        _intensity_category=lambda: category,
    )
    range_min, range_max, step = base._measured_axis_range()
    assert range_min == pytest.approx(1.0)
    assert range_max == pytest.approx(4.0)
    assert step == pytest.approx(1.0)


def test_measured_axis_range_non_uniform_grid_has_no_step():
    base = DataRangeBase()
    category = SimpleNamespace(unfiltered_x=[0.0, 1.0, 5.0])
    base._parent = SimpleNamespace(
        _has_measured_data=lambda: True,
        _intensity_category=lambda: category,
    )
    range_min, range_max, step = base._measured_axis_range()
    assert (range_min, range_max) == (0.0, 5.0)
    assert step is None


def test_raise_if_measured_blocks_writes_with_measured_scan():
    base = DataRangeBase()
    base._parent = SimpleNamespace(_has_measured_data=lambda: True, name='hrpt')
    with pytest.raises(ValueError, match='read-only while a measured'):
        base._raise_if_measured()


def test_raise_if_measured_allows_writes_without_measured_scan():
    base = DataRangeBase()
    base._parent = SimpleNamespace(_has_measured_data=lambda: False)
    # Does not raise.
    assert base._raise_if_measured() is None
