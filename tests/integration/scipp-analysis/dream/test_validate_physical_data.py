# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 DMSC
"""Tests for validating physical data values in CIF files."""

import gemmi
import numpy as np
import pytest

# Expected number of data points in the loop
LOOP_SIZE = 200


def _get_column_values(cif_block: gemmi.cif.Block, tag: str) -> np.ndarray:
    """Helper to extract column values as numpy array."""
    column = cif_block.find([tag])
    return np.array([float(row[0]) for row in column])


def test_validate_phys_data__data_size(
    cif_block: gemmi.cif.Block,
) -> None:
    """Verify the data loop contains exactly 2000 points."""
    loop = cif_block.find(['_pd_data.point_id']).loop
    assert loop.length() == LOOP_SIZE


def test_validate_phys_data__point_id_type(
    cif_block: gemmi.cif.Block,
) -> None:
    """Verify _pd_data.point_id contains integers from 0 to 1999."""
    point_ids = _get_column_values(cif_block, '_pd_data.point_id').astype(int)

    assert len(point_ids) == LOOP_SIZE
    assert point_ids[0] == 0
    assert point_ids[-1] == LOOP_SIZE - 1
    # Verify sequential integers
    np.testing.assert_array_equal(point_ids, np.arange(LOOP_SIZE))


def test_validate_phys_data__tof_positive(
    cif_block: gemmi.cif.Block,
) -> None:
    """Verify _pd_meas.time_of_flight values are positive floats."""
    tof_values = _get_column_values(cif_block, '_pd_meas.time_of_flight')

    assert np.all(tof_values > 0), 'TOF values must be positive'


def test_validate_phys_data__tof_increasing(
    cif_block: gemmi.cif.Block,
) -> None:
    """Verify _pd_meas.time_of_flight values constantly increase."""
    tof_values = _get_column_values(cif_block, '_pd_meas.time_of_flight')

    assert np.all(np.diff(tof_values) > 0), 'TOF values must be strictly increasing'


def test_validate_phys_data__tof_range(
    cif_block: gemmi.cif.Block,
) -> None:
    """Verify TOF range: first ~57.53, last ~22953.14."""
    tof_values = _get_column_values(cif_block, '_pd_meas.time_of_flight')

    assert pytest.approx(tof_values[0], rel=0.01) == 57.53
    assert pytest.approx(tof_values[-1], rel=0.01) == 22953.14


def test_validate_phys_data__intensity_range(
    cif_block: gemmi.cif.Block,
) -> None:
    """Verify _pd_proc.intensity_norm is non-negative."""
    intensity = _get_column_values(cif_block, '_pd_proc.intensity_norm')

    assert np.all(intensity >= 0), 'Intensity values must be non-negative'
    # First and last values in actual file are 0.0
    assert intensity[0] == pytest.approx(0.0, abs=0.01)
    assert intensity[-1] == pytest.approx(0.0, abs=0.01)


def test_validate_phys_data__intensity_su(
    cif_block: gemmi.cif.Block,
) -> None:
    """Verify _pd_proc.intensity_norm_su is non-negative."""
    intensity_su = _get_column_values(cif_block, '_pd_proc.intensity_norm_su')

    assert np.all(intensity_su >= 0), 'Intensity SU values must be non-negative'
    # First and last values in actual file are 0.0
    assert intensity_su[0] == pytest.approx(0.0, abs=0.01)
    assert intensity_su[-1] == pytest.approx(0.0, abs=0.01)
