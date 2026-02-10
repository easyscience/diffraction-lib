# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 DMSC
"""Tests for validating physical data values in CIF files.

These tests verify that numerical data columns contain valid,
physically meaningful values (positive TOF, non-negative intensity).
"""

import gemmi
import numpy as np
import pytest

# Expected number of data points in the loop (from scipp reduction)
LOOP_SIZE = 2000


def get_column_values(
    cif_block: gemmi.cif.Block,
    tag: str,
) -> np.ndarray:
    """Extract column values from CIF block as numpy array."""
    column = cif_block.find([tag])
    return np.array([float(row[0]) for row in column])


def test_validate_physical_data__data_size(
    cif_block: gemmi.cif.Block,
) -> None:
    """Verify the data loop contains exactly 2000 points."""
    loop = cif_block.find(['_pd_data.point_id']).loop
    assert loop.length() == LOOP_SIZE


def test_validate_physical_data__point_id_type(
    cif_block: gemmi.cif.Block,
) -> None:
    """Verify _pd_data.point_id contains sequential integers."""
    point_ids = get_column_values(cif_block, '_pd_data.point_id').astype(int)

    assert len(point_ids) == LOOP_SIZE
    assert point_ids[0] == 0
    assert point_ids[-1] == LOOP_SIZE - 1
    np.testing.assert_array_equal(point_ids, np.arange(LOOP_SIZE))


def test_validate_physical_data__tof_positive(
    cif_block: gemmi.cif.Block,
) -> None:
    """Verify _pd_meas.time_of_flight values are positive."""
    tof_values = get_column_values(cif_block, '_pd_meas.time_of_flight')
    assert np.all(tof_values > 0), 'TOF values must be positive'


def test_validate_physical_data__tof_increasing(
    cif_block: gemmi.cif.Block,
) -> None:
    """Verify _pd_meas.time_of_flight values are strictly increasing."""
    tof_values = get_column_values(cif_block, '_pd_meas.time_of_flight')
    assert np.all(np.diff(tof_values) > 0), 'TOF values must be strictly increasing'


def test_validate_physical_data__tof_range(
    cif_block: gemmi.cif.Block,
) -> None:
    """Verify TOF range spans approx. 8530 to 66504 microseconds."""
    tof_values = get_column_values(cif_block, '_pd_meas.time_of_flight')
    assert pytest.approx(tof_values[0], rel=0.01) == 8530.1
    assert pytest.approx(tof_values[-1], rel=0.01) == 66503.7


def test_validate_physical_data__intensity_values(
    cif_block: gemmi.cif.Block,
) -> None:
    """Verify _pd_proc.intensity_norm values are non-negative."""
    intensity = get_column_values(cif_block, '_pd_proc.intensity_norm')

    assert np.all(intensity >= 0), 'Intensity values must be non-negative'
    assert intensity[0] == pytest.approx(0.0, abs=0.01)
    assert intensity[-1] == pytest.approx(0.68, rel=0.1)


def test_validate_physical_data__intensity_su_values(
    cif_block: gemmi.cif.Block,
) -> None:
    """Verify _pd_proc.intensity_norm_su values are non-negative."""
    intensity_su = get_column_values(cif_block, '_pd_proc.intensity_norm_su')

    assert np.all(intensity_su >= 0), 'Intensity SU values must be non-negative'
    assert intensity_su[0] == pytest.approx(0.0, abs=0.01)
    assert intensity_su[-1] == pytest.approx(0.04, rel=0.1)
