# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.core.metadata import CalculatorSupport
from easydiffraction.core.metadata import Compatibility
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.variable import Parameter
from easydiffraction.datablocks.experiment.categories.instrument.base import InstrumentBase
from easydiffraction.datablocks.experiment.categories.instrument.factory import InstrumentFactory
from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import CalculatorEnum
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
from easydiffraction.io.cif.handler import CifHandler


@InstrumentFactory.register
class TofScInstrument(InstrumentBase):
    type_info = TypeInfo(tag='tof-sc', description='TOF single-crystal diffractometer')
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.TIME_OF_FLIGHT}),
        sample_form=frozenset({SampleFormEnum.SINGLE_CRYSTAL}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY}),
    )

    def __init__(self) -> None:
        super().__init__()


@InstrumentFactory.register
class TofPdInstrument(InstrumentBase):
    type_info = TypeInfo(tag='tof-pd', description='TOF powder diffractometer')
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.TIME_OF_FLIGHT}),
        sample_form=frozenset({SampleFormEnum.POWDER}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY, CalculatorEnum.CRYSFML}),
    )

    def __init__(self) -> None:
        super().__init__()

        self._setup_twotheta_bank: Parameter = Parameter(
            name='twotheta_bank',
            description='Detector bank position',
            units='deg',
            value_spec=AttributeSpec(
                default=150.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_instr.2theta_bank']),
        )
        self._calib_d_to_tof_offset: Parameter = Parameter(
            name='d_to_tof_offset',
            description='TOF offset',
            units='µs',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_instr.d_to_tof_offset']),
        )
        self._calib_d_to_tof_linear: Parameter = Parameter(
            name='d_to_tof_linear',
            description='TOF linear conversion',
            units='µs/Å',
            value_spec=AttributeSpec(
                default=10000.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_instr.d_to_tof_linear']),
        )
        self._calib_d_to_tof_quad: Parameter = Parameter(
            name='d_to_tof_quad',
            description='TOF quadratic correction',
            units='µs/Å²',
            value_spec=AttributeSpec(
                default=-0.00001,  # TODO: Fix CrysPy to accept 0
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_instr.d_to_tof_quad']),
        )
        self._calib_d_to_tof_recip: Parameter = Parameter(
            name='d_to_tof_recip',
            description='TOF reciprocal velocity correction',
            units='µs·Å',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_instr.d_to_tof_recip']),
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
