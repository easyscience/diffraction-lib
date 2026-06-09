# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.datablocks.experiment.categories.instrument.cwl import CwlPdInstrument


def test_cwl_instrument_parameters_settable():
    instr = CwlPdInstrument()
    instr.setup_wavelength = 2.0
    instr.calib_twotheta_offset = 0.1
    instr.calib_sample_displacement = 0.05
    instr.calib_sample_transparency = 0.09
    assert instr.setup_wavelength.value == 2.0
    assert instr.calib_twotheta_offset.value == 0.1
    assert instr.calib_sample_displacement.value == 0.05
    assert instr.calib_sample_transparency.value == 0.09


def test_cwl_sample_corrections_default_to_zero_in_degrees():
    instr = CwlPdInstrument()
    # SyCos/SySin corrections are off by default (no peak-position shift).
    assert instr.calib_sample_displacement.value == 0.0
    assert instr.calib_sample_transparency.value == 0.0
    # Degrees, matching the FullProf SyCos/SySin convention.
    assert instr.calib_sample_displacement.units == 'degrees'
    assert instr.calib_sample_transparency.units == 'degrees'
