from easydiffraction.experiments.categories.instrument.cwl import CwlInstrument


def test_cwl_instrument_parameters_settable():
    instr = CwlInstrument()
    instr.setup_wavelength = 2.0
    instr.calib_twotheta_offset = 0.1
    assert instr.setup_wavelength.value == 2.0
    assert instr.calib_twotheta_offset.value == 0.1
