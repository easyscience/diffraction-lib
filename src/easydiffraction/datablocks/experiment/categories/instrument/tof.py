# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Time-of-flight powder and single-crystal instruments."""

from easydiffraction.core.display_handler import DisplayHandler
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
    """TOF single-crystal diffractometer."""

    type_info = TypeInfo(
        tag='tof-sc',
        description='TOF single-crystal diffractometer',
    )
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.TIME_OF_FLIGHT}),
        sample_form=frozenset({SampleFormEnum.SINGLE_CRYSTAL}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY}),
    )

    def __init__(self) -> None:
        """Initialize the TOF single-crystal diffractometer."""
        super().__init__()


@InstrumentFactory.register
class TofPdInstrument(InstrumentBase):
    """TOF powder diffractometer."""

    type_info = TypeInfo(
        tag='tof-pd',
        description='TOF powder diffractometer',
    )
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.TIME_OF_FLIGHT}),
        sample_form=frozenset({SampleFormEnum.POWDER}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY, CalculatorEnum.CRYSFML}),
    )

    def __init__(self) -> None:
        """Initialize the TOF powder diffractometer."""
        super().__init__()

        self._setup_twotheta_bank: Parameter = Parameter(
            name='twotheta_bank',
            description='Detector bank position',
            units='degrees',
            display_handler=DisplayHandler(
                display_name='2θ bank',
                display_units='deg',
                latex_name=r'$2\theta$ bank',
                latex_units=r'\mathrm{deg}',
            ),
            value_spec=AttributeSpec(
                default=150.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=['_instrument.setup_twotheta_bank'],
                import_names=['_instr.2theta_bank'],
            ),
        )
        self._calib_d_to_tof_offset: Parameter = Parameter(
            name='d_to_tof_offset',
            description='TOF offset',
            units='microseconds',
            display_handler=DisplayHandler(
                display_name='TOF offset',
                display_units='μs',
                latex_name='TOF offset',
                latex_units=r'$\mu\mathrm{s}$',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=['_instrument.calib_d_to_tof_offset'],
                import_names=['_instr.d_to_tof_offset'],
            ),
        )
        self._calib_d_to_tof_linear: Parameter = Parameter(
            name='d_to_tof_linear',
            description='TOF linear conversion',
            units='microseconds_per_angstrom',
            display_handler=DisplayHandler(
                display_name='TOF linear',
                display_units='μs/Å',
                latex_name='TOF linear',
                latex_units=r'$\mu\mathrm{s}/\mathrm{\AA}$',
            ),
            value_spec=AttributeSpec(
                default=10000.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=['_instrument.calib_d_to_tof_linear'],
                import_names=['_instr.d_to_tof_linear'],
            ),
        )
        self._calib_d_to_tof_quadratic: Parameter = Parameter(
            name='d_to_tof_quadratic',
            description='TOF quadratic correction',
            units='microseconds_per_angstrom_squared',
            display_handler=DisplayHandler(
                display_name='TOF quadratic',
                display_units='μs/Å²',
                latex_name='TOF quadratic',
                latex_units=r'$\mu\mathrm{s}/\mathrm{\AA}^2$',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=['_instrument.calib_d_to_tof_quadratic'],
                import_names=['_instr.d_to_tof_quad'],
            ),
        )
        self._calib_d_to_tof_reciprocal: Parameter = Parameter(
            name='d_to_tof_reciprocal',
            description='TOF reciprocal velocity correction',
            units='microsecond_angstroms',
            display_handler=DisplayHandler(
                display_name='TOF reciprocal',
                display_units='μs·Å',
                latex_name='TOF reciprocal',
                latex_units=r'$\mu\mathrm{s}\,\mathrm{\AA}$',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=['_instrument.calib_d_to_tof_reciprocal'],
                import_names=['_instr.d_to_tof_recip'],
            ),
        )

    @property
    def setup_twotheta_bank(self) -> Parameter:
        """
        Detector bank position (deg).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._setup_twotheta_bank

    @setup_twotheta_bank.setter
    def setup_twotheta_bank(self, value: float) -> None:
        """Set the detector bank position (deg)."""
        self._setup_twotheta_bank.value = value

    @property
    def calib_d_to_tof_offset(self) -> Parameter:
        """
        TOF offset (μs).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._calib_d_to_tof_offset

    @calib_d_to_tof_offset.setter
    def calib_d_to_tof_offset(self, value: float) -> None:
        """Set the TOF offset (μs)."""
        self._calib_d_to_tof_offset.value = value

    @property
    def calib_d_to_tof_linear(self) -> Parameter:
        """
        TOF linear conversion (μs/Å).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._calib_d_to_tof_linear

    @calib_d_to_tof_linear.setter
    def calib_d_to_tof_linear(self, value: float) -> None:
        """Set the TOF linear conversion (μs/Å)."""
        self._calib_d_to_tof_linear.value = value

    @property
    def calib_d_to_tof_quadratic(self) -> Parameter:
        """
        TOF quadratic correction (μs/Å²).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._calib_d_to_tof_quadratic

    @calib_d_to_tof_quadratic.setter
    def calib_d_to_tof_quadratic(self, value: float) -> None:
        """Set the TOF quadratic correction (μs/Å²)."""
        self._calib_d_to_tof_quadratic.value = value

    @property
    def calib_d_to_tof_reciprocal(self) -> Parameter:
        """
        TOF reciprocal velocity correction (μs·Å).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._calib_d_to_tof_reciprocal

    @calib_d_to_tof_reciprocal.setter
    def calib_d_to_tof_reciprocal(self, value: float) -> None:
        """Set the TOF reciprocal velocity correction (μs·Å)."""
        self._calib_d_to_tof_reciprocal.value = value
