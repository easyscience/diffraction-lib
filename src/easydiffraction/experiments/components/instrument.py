# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from typing import Optional

from easydiffraction.core.categories import CategoryItem
from easydiffraction.core.guards import RangeValidator
from easydiffraction.core.parameters import Parameter
from easydiffraction.crystallography.cif import CifHandler
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
            validator=RangeValidator(default=1.5406),
            value=setup_wavelength,
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
            validator=RangeValidator(default=0.0),
            value=calib_twotheta_offset,
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
            validator=RangeValidator(default=150.0),
            value=setup_twotheta_bank,
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
            validator=RangeValidator(default=0.0),
            value=calib_d_to_tof_offset,
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
            validator=RangeValidator(default=10000.0),
            value=calib_d_to_tof_linear,
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
            validator=RangeValidator(default=-0.00001),
            value=calib_d_to_tof_quad,
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
            validator=RangeValidator(default=0.0),
            value=calib_d_to_tof_recip,
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
