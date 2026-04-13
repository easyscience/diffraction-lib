# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for experiment enum description methods and defaults."""

from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import PeakProfileTypeEnum
from easydiffraction.datablocks.experiment.item.enums import RadiationProbeEnum
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum


# ------------------------------------------------------------------
# SampleFormEnum
# ------------------------------------------------------------------


class TestSampleFormEnum:
    def test_values(self):
        assert SampleFormEnum.POWDER == 'powder'
        assert SampleFormEnum.SINGLE_CRYSTAL == 'single crystal'

    def test_default(self):
        assert SampleFormEnum.default() is SampleFormEnum.POWDER

    def test_description_powder(self):
        desc = SampleFormEnum.POWDER.description()
        assert isinstance(desc, str)
        assert 'Powder' in desc or 'powder' in desc.lower()

    def test_description_single_crystal(self):
        desc = SampleFormEnum.SINGLE_CRYSTAL.description()
        assert isinstance(desc, str)
        assert 'crystal' in desc.lower()


# ------------------------------------------------------------------
# ScatteringTypeEnum
# ------------------------------------------------------------------


class TestScatteringTypeEnum:
    def test_values(self):
        assert ScatteringTypeEnum.BRAGG == 'bragg'
        assert ScatteringTypeEnum.TOTAL == 'total'

    def test_default(self):
        assert ScatteringTypeEnum.default() is ScatteringTypeEnum.BRAGG

    def test_description_bragg(self):
        desc = ScatteringTypeEnum.BRAGG.description()
        assert isinstance(desc, str)
        assert 'Bragg' in desc

    def test_description_total(self):
        desc = ScatteringTypeEnum.TOTAL.description()
        assert isinstance(desc, str)
        assert 'Total' in desc or 'PDF' in desc


# ------------------------------------------------------------------
# RadiationProbeEnum
# ------------------------------------------------------------------


class TestRadiationProbeEnum:
    def test_values(self):
        assert RadiationProbeEnum.NEUTRON == 'neutron'
        assert RadiationProbeEnum.XRAY == 'xray'

    def test_default(self):
        assert RadiationProbeEnum.default() is RadiationProbeEnum.NEUTRON

    def test_description_neutron(self):
        desc = RadiationProbeEnum.NEUTRON.description()
        assert isinstance(desc, str)
        assert 'Neutron' in desc or 'neutron' in desc.lower()

    def test_description_xray(self):
        desc = RadiationProbeEnum.XRAY.description()
        assert isinstance(desc, str)
        assert 'ray' in desc.lower()


# ------------------------------------------------------------------
# BeamModeEnum
# ------------------------------------------------------------------


class TestBeamModeEnum:
    def test_values(self):
        assert BeamModeEnum.CONSTANT_WAVELENGTH == 'constant wavelength'
        assert BeamModeEnum.TIME_OF_FLIGHT == 'time-of-flight'

    def test_default(self):
        assert BeamModeEnum.default() is BeamModeEnum.CONSTANT_WAVELENGTH

    def test_description_cwl(self):
        desc = BeamModeEnum.CONSTANT_WAVELENGTH.description()
        assert isinstance(desc, str)
        assert 'CW' in desc or 'wavelength' in desc.lower()

    def test_description_tof(self):
        desc = BeamModeEnum.TIME_OF_FLIGHT.description()
        assert isinstance(desc, str)
        assert 'TOF' in desc or 'time' in desc.lower()


# ------------------------------------------------------------------
# PeakProfileTypeEnum
# ------------------------------------------------------------------


class TestPeakProfileTypeEnum:
    def test_default_bragg_cwl(self):
        result = PeakProfileTypeEnum.default(
            scattering_type=ScatteringTypeEnum.BRAGG,
            beam_mode=BeamModeEnum.CONSTANT_WAVELENGTH,
        )
        assert result is PeakProfileTypeEnum.PSEUDO_VOIGT

    def test_default_bragg_tof(self):
        result = PeakProfileTypeEnum.default(
            scattering_type=ScatteringTypeEnum.BRAGG,
            beam_mode=BeamModeEnum.TIME_OF_FLIGHT,
        )
        assert result is PeakProfileTypeEnum.JORGENSEN

    def test_default_total_cwl(self):
        result = PeakProfileTypeEnum.default(
            scattering_type=ScatteringTypeEnum.TOTAL,
            beam_mode=BeamModeEnum.CONSTANT_WAVELENGTH,
        )
        assert result is PeakProfileTypeEnum.GAUSSIAN_DAMPED_SINC

    def test_default_total_tof(self):
        result = PeakProfileTypeEnum.default(
            scattering_type=ScatteringTypeEnum.TOTAL,
            beam_mode=BeamModeEnum.TIME_OF_FLIGHT,
        )
        assert result is PeakProfileTypeEnum.GAUSSIAN_DAMPED_SINC

    def test_default_none_uses_defaults(self):
        result = PeakProfileTypeEnum.default()
        expected = PeakProfileTypeEnum.default(
            scattering_type=ScatteringTypeEnum.default(),
            beam_mode=BeamModeEnum.default(),
        )
        assert result is expected

    def test_description_pseudo_voigt(self):
        desc = PeakProfileTypeEnum.PSEUDO_VOIGT.description()
        assert isinstance(desc, str)
        assert 'Pseudo-Voigt' in desc

    def test_description_pseudo_voigt_empirical_asymmetry(self):
        desc = PeakProfileTypeEnum.PSEUDO_VOIGT_EMPIRICAL_ASYMMETRY.description()
        assert isinstance(desc, str)
        assert 'asymmetry' in desc.lower()

    def test_description_thompson_cox_hastings(self):
        desc = PeakProfileTypeEnum.THOMPSON_COX_HASTINGS.description()
        assert isinstance(desc, str)
        assert 'Thompson' in desc

    def test_description_jorgensen(self):
        desc = PeakProfileTypeEnum.JORGENSEN.description()
        assert isinstance(desc, str)
        assert 'Jorgensen' in desc

    def test_description_jorgensen_von_dreele(self):
        desc = PeakProfileTypeEnum.JORGENSEN_VON_DREELE.description()
        assert isinstance(desc, str)
        assert 'Jorgensen' in desc

    def test_description_double_jorgensen_von_dreele(self):
        desc = PeakProfileTypeEnum.DOUBLE_JORGENSEN_VON_DREELE.description()
        assert isinstance(desc, str)
        assert 'type0m' in desc

    def test_description_gaussian_damped_sinc(self):
        desc = PeakProfileTypeEnum.GAUSSIAN_DAMPED_SINC.description()
        assert isinstance(desc, str)
        assert 'sinc' in desc.lower() or 'PDF' in desc
