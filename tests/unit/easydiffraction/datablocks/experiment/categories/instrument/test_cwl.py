# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.datablocks.experiment.categories.instrument.cwl import CwlPdInstrument


def test_cwl_instrument_parameters_settable():
    instr = CwlPdInstrument()
    instr.setup_wavelength = 2.0
    instr.calib_twotheta_offset = 0.1
    assert instr.setup_wavelength.value == 2.0
    assert instr.calib_twotheta_offset.value == 0.1
