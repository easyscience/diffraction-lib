# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 DMSC
"""Tests for validating metadata structure in CIF files."""

import gemmi
import pytest


def test_validate_meta_data__block_exists(
    cif_document: gemmi.cif.Document,
) -> None:
    """Verify that single datablock 'reduced_tof' is present."""
    assert len(cif_document) == 1
    assert cif_document[0].name == 'reduced_tof'


def test_validate_meta_data__diffrn_radiation(
    cif_block: gemmi.cif.Block,
) -> None:
    """Verify _diffrn_radiation.probe is 'neutron'."""
    probe = cif_block.find_value('_diffrn_radiation.probe')
    assert probe is not None
    assert str(probe).strip('\'"') == 'neutron'


def test_validate_meta_data__d_to_tof_loop(
    cif_block: gemmi.cif.Block,
) -> None:
    """Verify the d_to_tof calibration loop exists with correct structure."""
    loop = cif_block.find(['_pd_calib_d_to_tof.id']).loop
    assert loop is not None

    # Check all expected columns exist
    tags = [tag for tag in loop.tags]
    assert '_pd_calib_d_to_tof.id' in tags
    assert '_pd_calib_d_to_tof.power' in tags
    assert '_pd_calib_d_to_tof.coeff' in tags


def test_validate_meta_data__d_to_tof_difc(
    cif_block: gemmi.cif.Block,
) -> None:
    """Verify DIFC calibration coefficient is approximately 9819.35."""
    table = cif_block.find([
        '_pd_calib_d_to_tof.id',
        '_pd_calib_d_to_tof.power',
        '_pd_calib_d_to_tof.coeff',
    ])

    difc_row = None
    for row in table:
        if row[0] == 'DIFC':
            difc_row = row
            break

    assert difc_row is not None, 'DIFC row not found in calibration loop'
    assert int(difc_row[1]) == 1, 'DIFC power should be 1'
    assert pytest.approx(float(difc_row[2]), rel=0.01) == 9819.35


def test_validate_meta_data__data_loop_exists(
    cif_block: gemmi.cif.Block,
) -> None:
    """Verify the main data loop exists with required columns."""
    loop = cif_block.find(['_pd_data.point_id']).loop
    assert loop is not None

    # Check all expected columns exist
    tags = [tag for tag in loop.tags]
    assert '_pd_data.point_id' in tags
    assert '_pd_meas.time_of_flight' in tags
    assert '_pd_proc.intensity_norm' in tags
    assert '_pd_proc.intensity_norm_su' in tags
