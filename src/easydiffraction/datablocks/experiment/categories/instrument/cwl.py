# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.core.metadata import CalculatorSupport
from easydiffraction.core.metadata import Compatibility
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.display_handler import DisplayHandler
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


class CwlInstrumentBase(InstrumentBase):
    """Base class for constant-wavelength instruments."""

    def __init__(self) -> None:
        super().__init__()

        self._setup_wavelength: Parameter = Parameter(
            name='wavelength',
            description='Incident neutron or X-ray wavelength',
            units='angstroms',
            display_handler=DisplayHandler(
                display_units='Å',
                latex_units=r'\AA',
            ),
            value_spec=AttributeSpec(
                default=1.5406,
                validator=RangeValidator(ge=0.0),
            ),
            cif_handler=CifHandler(
                names=[
                    '_instr.wavelength',
                ]
            ),
        )

    @property
    def setup_wavelength(self) -> Parameter:
        """
        Incident neutron or X-ray wavelength (Å).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._setup_wavelength

    @setup_wavelength.setter
    def setup_wavelength(self, value: float) -> None:
        self._setup_wavelength.value = value


@InstrumentFactory.register
class CwlScInstrument(CwlInstrumentBase):
    """CW single-crystal diffractometer."""

    type_info = TypeInfo(
        tag='cwl-sc',
        description='CW single-crystal diffractometer',
    )
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.CONSTANT_WAVELENGTH}),
        sample_form=frozenset({SampleFormEnum.SINGLE_CRYSTAL}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY}),
    )

    def __init__(self) -> None:
        super().__init__()


@InstrumentFactory.register
class CwlPdInstrument(CwlInstrumentBase):
    """CW powder diffractometer."""

    type_info = TypeInfo(
        tag='cwl-pd',
        description='CW powder diffractometer',
    )
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG, ScatteringTypeEnum.TOTAL}),
        beam_mode=frozenset({BeamModeEnum.CONSTANT_WAVELENGTH}),
        sample_form=frozenset({SampleFormEnum.POWDER}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({
            CalculatorEnum.CRYSPY,
            CalculatorEnum.CRYSFML,
            CalculatorEnum.PDFFIT,
        }),
    )

    def __init__(self) -> None:
        super().__init__()

        self._calib_twotheta_offset: Parameter = Parameter(
            name='twotheta_offset',
            description='Instrument misalignment offset',
            units='degrees',
            display_handler=DisplayHandler(
                display_units='deg',
                latex_units=r'$^\circ$',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=[
                    '_instr.2theta_offset',
                ]
            ),
        )

    @property
    def calib_twotheta_offset(self) -> Parameter:
        """
        Instrument misalignment offset (deg).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._calib_twotheta_offset

    @calib_twotheta_offset.setter
    def calib_twotheta_offset(self, value: float) -> None:
        self._calib_twotheta_offset.value = value
