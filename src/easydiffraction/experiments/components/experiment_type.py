# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction Python Library contributors <https://github.com/easyscience/diffraction-lib>
# SPDX-License-Identifier: BSD-3-Clause

from enum import Enum

from easydiffraction.core.objects import Component
from easydiffraction.core.objects import Descriptor


class SampleFormEnum(str, Enum):
    POWDER = 'powder'
    SINGLE_CRYSTAL = 'single crystal'

    @classmethod
    def default(cls) -> 'SampleFormEnum':
        return cls.POWDER

    def description(self) -> str:
        if self is SampleFormEnum.POWDER:
            return 'Powdered or polycrystalline sample.'
        elif self is SampleFormEnum.SINGLE_CRYSTAL:
            return 'Single crystal sample.'


class ScatteringTypeEnum(str, Enum):
    BRAGG = 'bragg'
    TOTAL = 'total'

    @classmethod
    def default(cls) -> 'ScatteringTypeEnum':
        return cls.BRAGG

    def description(self) -> str:
        if self is ScatteringTypeEnum.BRAGG:
            return 'Bragg diffraction for conventional structure refinement.'
        elif self is ScatteringTypeEnum.TOTAL:
            return 'Total scattering for pair distribution function analysis (PDF).'


class RadiationProbeEnum(str, Enum):
    NEUTRON = 'neutron'
    XRAY = 'xray'

    @classmethod
    def default(cls) -> 'RadiationProbeEnum':
        return cls.NEUTRON

    def description(self) -> str:
        if self is RadiationProbeEnum.NEUTRON:
            return 'Neutron diffraction.'
        elif self is RadiationProbeEnum.XRAY:
            return 'X-ray diffraction.'


class BeamModeEnum(str, Enum):
    CONSTANT_WAVELENGTH = 'constant wavelength'
    TIME_OF_FLIGHT = 'time-of-flight'

    @classmethod
    def default(cls) -> 'BeamModeEnum':
        return cls.CONSTANT_WAVELENGTH

    def description(self) -> str:
        if self is BeamModeEnum.CONSTANT_WAVELENGTH:
            return 'Constant wavelength (CW) diffraction.'
        elif self is BeamModeEnum.TIME_OF_FLIGHT:
            return 'Time-of-flight (TOF) diffraction.'


class ExperimentType(Component):
    @property
    def cif_category_key(self) -> str:
        return 'expt_type'

    @property
    def category_key(self) -> str:
        return 'expt_type'

    def __init__(
        self,
        sample_form: str,
        beam_mode: str,
        radiation_probe: str,
        scattering_type: str,
    ):
        super().__init__()

        self.sample_form: Descriptor = Descriptor(
            value=sample_form,
            name='sample_form',
            cif_name='sample_form',
            description='Specifies whether the diffraction data corresponds to powder diffraction or single crystal '
            'diffraction',
        )
        self.beam_mode: Descriptor = Descriptor(
            value=beam_mode,
            name='beam_mode',
            cif_name='beam_mode',
            description='Defines whether the measurement is performed with a constant wavelength (CW) or time-of-flight ('
            'TOF) method',
        )
        self.radiation_probe: Descriptor = Descriptor(
            value=radiation_probe,
            name='radiation_probe',
            cif_name='radiation_probe',
            description='Specifies whether the measurement uses neutrons or X-rays',
        )
        self.scattering_type: Descriptor = Descriptor(
            value=scattering_type,
            name='scattering_type',
            cif_name='scattering_type',
            description='Specifies whether the experiment uses Bragg scattering (for conventional structure refinement) or '
            'total scattering (for pair distribution function analysis - PDF)',
        )

        # Lock further attribute additions to prevent
        # accidental modifications by users
        self._locked: bool = True
