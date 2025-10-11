# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from typing import Optional

from easydiffraction.core.categories import CategoryItem
from easydiffraction.core.parameters import CifHandler
from easydiffraction.core.parameters import Parameter
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import DataTypes
from easydiffraction.core.validation import RangeValidator
from easydiffraction.experiments.components.experiment_type import BeamModeEnum
from easydiffraction.experiments.components.experiment_type import ScatteringTypeEnum


class InstrumentBase(CategoryItem):
    def __init__(
        self,
    ) -> None:
        super().__init__()
        self._identity.category_code = 'instrument'


class ConstantWavelengthInstrument(InstrumentBase):
    def __init__(
        self,
        *,
        setup_wavelength=None,
        calib_twotheta_offset=None,
    ) -> None:
        super().__init__()

        self._setup_wavelength: Parameter = Parameter(
            name='wavelength',
            description='Incident neutron or X-ray wavelength',
            value_spec=AttributeSpec(
                value=setup_wavelength,
                type_=DataTypes.NUMERIC,
                default=1.5406,
                content_validator=RangeValidator(),
            ),
            units='Å',
            cif_handler=CifHandler(
                names=[
                    '_instr.wavelength',
                ]
            ),
        )
        self._calib_twotheta_offset: Parameter = Parameter(
            name='twotheta_offset',
            description='Instrument misalignment offset',
            value_spec=AttributeSpec(
                value=calib_twotheta_offset,
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),
            units='deg',
            cif_handler=CifHandler(
                names=[
                    '_instr.2theta_offset',
                ]
            ),
        )

    @property
    def setup_wavelength(self):
        return self._setup_wavelength

    @setup_wavelength.setter
    def setup_wavelength(self, value):
        self._setup_wavelength.value = value

    @property
    def calib_twotheta_offset(self):
        return self._calib_twotheta_offset

    @calib_twotheta_offset.setter
    def calib_twotheta_offset(self, value):
        self._calib_twotheta_offset.value = value


class TimeOfFlightInstrument(InstrumentBase):
    def __init__(
        self,
        *,
        setup_twotheta_bank=None,
        calib_d_to_tof_offset=None,
        calib_d_to_tof_linear=None,
        calib_d_to_tof_quad=None,
        calib_d_to_tof_recip=None,
    ) -> None:
        super().__init__()

        self._setup_twotheta_bank: Parameter = Parameter(
            name='twotheta_bank',
            description='Detector bank position',
            value_spec=AttributeSpec(
                value=setup_twotheta_bank,
                type_=DataTypes.NUMERIC,
                default=150.0,
                content_validator=RangeValidator(),
            ),
            units='deg',
            cif_handler=CifHandler(
                names=[
                    '_instr.2theta_bank',
                ]
            ),
        )
        self._calib_d_to_tof_offset: Parameter = Parameter(
            name='d_to_tof_offset',
            description='TOF offset',
            value_spec=AttributeSpec(
                value=calib_d_to_tof_offset,
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),
            units='µs',
            cif_handler=CifHandler(
                names=[
                    '_instr.d_to_tof_offset',
                ]
            ),
        )
        self._calib_d_to_tof_linear: Parameter = Parameter(
            name='d_to_tof_linear',
            description='TOF linear conversion',
            value_spec=AttributeSpec(
                value=calib_d_to_tof_linear,
                type_=DataTypes.NUMERIC,
                default=10000.0,
                content_validator=RangeValidator(),
            ),
            units='µs/Å',
            cif_handler=CifHandler(
                names=[
                    '_instr.d_to_tof_linear',
                ]
            ),
        )
        self._calib_d_to_tof_quad: Parameter = Parameter(
            name='d_to_tof_quad',
            description='TOF quadratic correction',
            value_spec=AttributeSpec(
                value=calib_d_to_tof_quad,
                type_=DataTypes.NUMERIC,
                default=-0.00001,
                content_validator=RangeValidator(),
            ),
            units='µs/Å²',
            cif_handler=CifHandler(
                names=[
                    '_instr.d_to_tof_quad',
                ]
            ),
        )
        self._calib_d_to_tof_recip: Parameter = Parameter(
            name='d_to_tof_recip',
            description='TOF reciprocal velocity correction',
            value_spec=AttributeSpec(
                value=calib_d_to_tof_recip,
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),
            units='µs·Å',
            cif_handler=CifHandler(
                names=[
                    '_instr.d_to_tof_recip',
                ]
            ),
        )

    @property
    def setup_twotheta_bank(self):
        return self._setup_twotheta_bank

    @setup_twotheta_bank.setter
    def setup_twotheta_bank(self, value):
        self._setup_twotheta_bank.value = value

    @property
    def calib_d_to_tof_offset(self):
        return self._calib_d_to_tof_offset

    @calib_d_to_tof_offset.setter
    def calib_d_to_tof_offset(self, value):
        self._calib_d_to_tof_offset.value = value

    @property
    def calib_d_to_tof_linear(self):
        return self._calib_d_to_tof_linear

    @calib_d_to_tof_linear.setter
    def calib_d_to_tof_linear(self, value):
        self._calib_d_to_tof_linear.value = value

    @property
    def calib_d_to_tof_quad(self):
        return self._calib_d_to_tof_quad

    @calib_d_to_tof_quad.setter
    def calib_d_to_tof_quad(self, value):
        self._calib_d_to_tof_quad.value = value

    @property
    def calib_d_to_tof_recip(self):
        return self._calib_d_to_tof_recip

    @calib_d_to_tof_recip.setter
    def calib_d_to_tof_recip(self, value):
        self._calib_d_to_tof_recip.value = value


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
