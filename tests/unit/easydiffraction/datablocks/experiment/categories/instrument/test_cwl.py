# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import pytest

from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.datablocks.experiment.categories.instrument.cwl import CwlPdNeutronInstrument
from easydiffraction.datablocks.experiment.categories.instrument.cwl import CwlPdXrayInstrument
from easydiffraction.utils.logging import Logger


def test_cwl_instrument_parameters_settable():
    instr = CwlPdNeutronInstrument()
    instr.setup_wavelength = 2.0
    instr.calib_twotheta_offset = 0.1
    instr.calib_sample_displacement = 0.05
    instr.calib_sample_transparency = 0.09
    assert instr.setup_wavelength.value == 2.0
    assert instr.calib_twotheta_offset.value == 0.1
    assert instr.calib_sample_displacement.value == 0.05
    assert instr.calib_sample_transparency.value == 0.09


def test_cwl_sample_corrections_default_to_zero_in_degrees():
    instr = CwlPdNeutronInstrument()
    # SyCos/SySin corrections are off by default (no peak-position shift).
    assert instr.calib_sample_displacement.value == 0.0
    assert instr.calib_sample_transparency.value == 0.0
    # Degrees, matching the FullProf SyCos/SySin convention.
    assert instr.calib_sample_displacement.units == 'degrees'
    assert instr.calib_sample_transparency.units == 'degrees'


def test_cwl_second_wavelength_defaults_off():
    instr = CwlPdNeutronInstrument()
    # No second component by default: monochromatic, as before.
    assert instr.setup_wavelength_2.value == 0.0
    assert instr.setup_wavelength_2_to_1_ratio.value == 0.0
    assert instr.setup_wavelength_2.units == 'angstroms'


def test_cwl_second_wavelength_settable():
    instr = CwlPdNeutronInstrument()
    instr.setup_wavelength_2 = 1.5444
    instr.setup_wavelength_2_to_1_ratio = 0.5
    assert instr.setup_wavelength_2.value == 1.5444
    assert instr.setup_wavelength_2_to_1_ratio.value == 0.5


def test_cwl_second_wavelength_fields_are_non_refinable():
    instr = CwlPdNeutronInstrument()
    # Placeholder fields are NumericDescriptors, not refinable
    # Parameters, so a fit cannot silently move a value no engine
    # consumes yet (NumericDescriptor has no `free` flag).
    assert isinstance(instr.setup_wavelength_2, NumericDescriptor)
    assert isinstance(instr.setup_wavelength_2_to_1_ratio, NumericDescriptor)
    assert not hasattr(instr.setup_wavelength_2, 'free')
    assert not hasattr(instr.setup_wavelength_2_to_1_ratio, 'free')
    # The primary wavelength stays a refinable Parameter.
    assert hasattr(instr.setup_wavelength, 'free')


def test_cwl_second_wavelength_ratio_rejects_out_of_range(monkeypatch):
    monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.RAISE, raising=True)
    instr = CwlPdNeutronInstrument()
    # Ratio is a relative intensity bounded to [0, 1].
    with pytest.raises(TypeError):
        instr.setup_wavelength_2_to_1_ratio = 1.5
    with pytest.raises(TypeError):
        instr.setup_wavelength_2_to_1_ratio = -0.1
    # A negative second wavelength is rejected too.
    with pytest.raises(TypeError):
        instr.setup_wavelength_2 = -1.0


def test_cwl_xray_polarization_optics_defaults_off():
    instr = CwlPdXrayInstrument()

    assert isinstance(instr.setup_polarization_coefficient, NumericDescriptor)
    assert isinstance(instr.setup_monochromator_twotheta, NumericDescriptor)
    assert instr.setup_polarization_coefficient.value == 0.0
    assert instr.setup_monochromator_twotheta.value == 0.0
    assert not hasattr(instr.setup_polarization_coefficient, 'free')
    assert not hasattr(instr.setup_monochromator_twotheta, 'free')


def test_cwl_xray_polarization_optics_settable():
    instr = CwlPdXrayInstrument()

    instr.setup_polarization_coefficient = 0.5
    instr.setup_monochromator_twotheta = 26.565

    assert instr.setup_polarization_coefficient.value == 0.5
    assert instr.setup_monochromator_twotheta.value == 26.565


def test_cwl_xray_polarization_optics_reject_invalid_values(monkeypatch):
    monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.RAISE, raising=True)
    instr = CwlPdXrayInstrument()

    with pytest.raises(TypeError):
        instr.setup_polarization_coefficient = -0.1
    with pytest.raises(TypeError):
        instr.setup_polarization_coefficient = 1.1
    with pytest.raises(TypeError):
        instr.setup_polarization_coefficient = 'bad'
    with pytest.raises(TypeError):
        instr.setup_monochromator_twotheta = -0.1
    with pytest.raises(TypeError):
        instr.setup_monochromator_twotheta = 180.0
    with pytest.raises(TypeError):
        instr.setup_monochromator_twotheta = 'bad'


def test_cwl_neutron_instrument_has_no_polarization_optics():
    instr = CwlPdNeutronInstrument()

    assert not hasattr(instr, 'setup_polarization_coefficient')
    assert not hasattr(instr, 'setup_monochromator_twotheta')


def test_cwl_xray_polarization_optics_round_trip_through_cif():
    import gemmi

    instr = CwlPdXrayInstrument()
    instr.setup_polarization_coefficient = 0.5
    instr.setup_monochromator_twotheta = 26.565

    block = gemmi.cif.read_string('data_x\n' + instr.as_cif + '\n').sole_block()
    restored = CwlPdXrayInstrument()
    restored.from_cif(block)

    assert restored.setup_polarization_coefficient.value == 0.5
    assert restored.setup_monochromator_twotheta.value == 26.565
