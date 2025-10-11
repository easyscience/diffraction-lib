# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from enum import Enum


class SampleFormEnum(str, Enum):
    POWDER = 'powder'
    SINGLE_CRYSTAL = 'single crystal'

    @classmethod
    def default(cls) -> 'SampleFormEnum':
        return cls.POWDER


class ScatteringTypeEnum(str, Enum):
    BRAGG = 'bragg'
    TOTAL = 'total'

    @classmethod
    def default(cls) -> 'ScatteringTypeEnum':
        return cls.BRAGG


class RadiationProbeEnum(str, Enum):
    NEUTRON = 'neutron'
    XRAY = 'xray'

    @classmethod
    def default(cls) -> 'RadiationProbeEnum':
        return cls.NEUTRON


class BeamModeEnum(str, Enum):
    CONSTANT_WAVELENGTH = 'constant wavelength'
    TIME_OF_FLIGHT = 'time-of-flight'

    @classmethod
    def default(cls) -> 'BeamModeEnum':
        return cls.CONSTANT_WAVELENGTH


class PeakProfileTypeEnum(str, Enum):
    PSEUDO_VOIGT = 'pseudo-voigt'
    SPLIT_PSEUDO_VOIGT = 'split pseudo-voigt'
    THOMPSON_COX_HASTINGS = 'thompson-cox-hastings'
    PSEUDO_VOIGT_IKEDA_CARPENTER = 'pseudo-voigt * ikeda-carpenter'
    PSEUDO_VOIGT_BACK_TO_BACK = 'pseudo-voigt * back-to-back'
    GAUSSIAN_DAMPED_SINC = 'gaussian-damped-sinc'

    @classmethod
    def default(
        cls,
        scattering_type: ScatteringTypeEnum | None = None,
        beam_mode: BeamModeEnum | None = None,
    ) -> 'PeakProfileTypeEnum':
        if scattering_type is None:
            scattering_type = ScatteringTypeEnum.default()
        if beam_mode is None:
            beam_mode = BeamModeEnum.default()
        return {
            (ScatteringTypeEnum.BRAGG, BeamModeEnum.CONSTANT_WAVELENGTH): cls.PSEUDO_VOIGT,
            (
                ScatteringTypeEnum.BRAGG,
                BeamModeEnum.TIME_OF_FLIGHT,
            ): cls.PSEUDO_VOIGT_IKEDA_CARPENTER,
            (ScatteringTypeEnum.TOTAL, BeamModeEnum.CONSTANT_WAVELENGTH): cls.GAUSSIAN_DAMPED_SINC,
            (ScatteringTypeEnum.TOTAL, BeamModeEnum.TIME_OF_FLIGHT): cls.GAUSSIAN_DAMPED_SINC,
        }[(scattering_type, beam_mode)]
