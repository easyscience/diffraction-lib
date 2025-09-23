# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from typing import Optional

from easydiffraction.core.categories import CategoryItem
from easydiffraction.core.parameters import Parameter
from easydiffraction.experiments.components.experiment_type import BeamModeEnum
from easydiffraction.experiments.components.experiment_type import ScatteringTypeEnum


class InstrumentBase(CategoryItem):
    _class_public_attrs = {
        'setup_wavelength',
        'calib_twotheta_offset',
    }

    @property
    def category_key(self) -> str:
        return 'instrument'


class ConstantWavelengthInstrument(InstrumentBase):
    def __init__(
        self,
        setup_wavelength: float = 1.5406,
        calib_twotheta_offset: float = 0.0,
    ) -> None:
        super().__init__()

        self.setup_wavelength: Parameter = Parameter(
            value=setup_wavelength,
            name='wavelength',
            full_cif_names=['_instr.wavelength'],
            default_value=1.5406,
            units='Å',
            description='Incident neutron or X-ray wavelength',
        )
        self.calib_twotheta_offset: Parameter = Parameter(
            value=calib_twotheta_offset,
            name='twotheta_offset',
            full_cif_names=['_instr.2theta_offset'],
            default_value=0.0,
            units='deg',
            description='Instrument misalignment offset',
        )


class TimeOfFlightInstrument(InstrumentBase):
    _class_public_attrs = {
        'setup_twotheta_bank',
        'calib_d_to_tof_offset',
        'calib_d_to_tof_linear',
        'calib_d_to_tof_quad',
        'calib_d_to_tof_recip',
    }

    def __init__(
        self,
        setup_twotheta_bank: float = 150.0,
        calib_d_to_tof_offset: float = 0.0,
        calib_d_to_tof_linear: float = 10000.0,
        calib_d_to_tof_quad: float = -0.00001,
        calib_d_to_tof_recip: float = 0.0,
    ) -> None:
        super().__init__()

        self.setup_twotheta_bank: Parameter = Parameter(
            value=setup_twotheta_bank,
            name='twotheta_bank',
            full_cif_names=['_instr.2theta_bank'],
            default_value=150.0,
            units='deg',
            description='Detector bank position',
        )
        self.calib_d_to_tof_offset: Parameter = Parameter(
            value=calib_d_to_tof_offset,
            name='d_to_tof_offset',
            full_cif_names=['_instr.d_to_tof_offset'],
            default_value=0.0,
            units='µs',
            description='TOF offset',
        )
        self.calib_d_to_tof_linear: Parameter = Parameter(
            value=calib_d_to_tof_linear,
            name='d_to_tof_linear',
            full_cif_names=['_instr.d_to_tof_linear'],
            default_value=10000.0,
            units='µs/Å',
            description='TOF linear conversion',
        )
        self.calib_d_to_tof_quad: Parameter = Parameter(
            value=calib_d_to_tof_quad,
            name='d_to_tof_quad',
            full_cif_names=['_instr.d_to_tof_quad'],
            default_value=-0.00001,
            units='µs/Å²',
            description='TOF quadratic correction',
        )
        self.calib_d_to_tof_recip: Parameter = Parameter(
            value=calib_d_to_tof_recip,
            name='d_to_tof_recip',
            full_cif_names=['_instr.d_to_tof_recip'],
            default_value=0.0,
            units='µs·Å',
            description='TOF reciprocal velocity correction',
        )


class InstrumentFactory:
    ST = ScatteringTypeEnum
    BM = BeamModeEnum
    _supported = {
        ST.BRAGG: {
            BM.CONSTANT_WAVELENGTH: ConstantWavelengthInstrument,
            BM.TIME_OF_FLIGHT: TimeOfFlightInstrument,
        }
    }

    @classmethod
    def create(
        cls,
        scattering_type: Optional[ScatteringTypeEnum] = None,
        beam_mode: Optional[BeamModeEnum] = None,
    ):
        if beam_mode is None:
            beam_mode = BeamModeEnum.default()
        if scattering_type is None:
            scattering_type = ScatteringTypeEnum.default()

        supported_scattering_types = list(cls._supported.keys())
        if scattering_type not in supported_scattering_types:
            raise ValueError(
                f"Unsupported scattering type: '{scattering_type}'.\n "
                f'Supported scattering types: {supported_scattering_types}'
            )

        supported_beam_modes = list(cls._supported[scattering_type].keys())
        if beam_mode not in supported_beam_modes:
            raise ValueError(
                f"Unsupported beam mode: '{beam_mode}' for scattering type: "
                f"'{scattering_type}'.\n "
                f'Supported beam modes: {supported_beam_modes}'
            )

        instrument_class = cls._supported[scattering_type][beam_mode]
        instrument_obj = instrument_class()

        return instrument_obj
