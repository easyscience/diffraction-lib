# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Constant-wavelength powder and single-crystal instruments."""

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
from easydiffraction.io.cif.handler import TagSpec


class CwlInstrumentBase(InstrumentBase):
    """Base class for constant-wavelength instruments."""

    def __init__(self) -> None:
        """Initialize the constant-wavelength instrument base."""
        super().__init__()

        self._setup_wavelength: Parameter = Parameter(
            name='wavelength',
            description='Incident neutron or X-ray wavelength',
            units='angstroms',
            display_handler=DisplayHandler(
                display_name='Wavelength',
                display_units='Å',
                latex_name='Wavelength',
                latex_units=r'\AA',
            ),
            value_spec=AttributeSpec(
                default=1.5406,
                validator=RangeValidator(ge=0.0),
            ),
            tags=TagSpec(
                edi_names=['_instrument.setup_wavelength'],
                cif_names=['_diffrn_radiation_wavelength.value', '_instr.wavelength'],
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
        """Set the incident neutron or X-ray wavelength (Å)."""
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
        """Initialize the CW single-crystal diffractometer."""
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
        """Initialize the CW powder diffractometer."""
        super().__init__()

        self._calib_twotheta_offset: Parameter = Parameter(
            name='twotheta_offset',
            description='Instrument misalignment offset',
            units='degrees',
            display_handler=DisplayHandler(
                display_name='2θ offset',
                display_units='deg',
                latex_name=r'$2\theta$ offset',
                latex_units=r'\mathrm{deg}',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_instrument.calib_twotheta_offset'],
                cif_names=['_pd_calib.2theta_offset', '_instr.2theta_offset'],
            ),
        )

        self._calib_sample_displacement: Parameter = Parameter(
            name='sample_displacement',
            description='Specimen displacement from the diffractometer axis',
            units='degrees',
            display_handler=DisplayHandler(
                display_name='Sample displacement',
                display_units='deg',
                latex_name='Sample displacement',
                latex_units=r'\mathrm{deg}',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_instrument.calib_sample_displacement'],
                cif_names=['_instr.sample_displacement'],
            ),
        )

        self._calib_sample_transparency: Parameter = Parameter(
            name='sample_transparency',
            description='Sample transparency (beam penetration) shift',
            units='degrees',
            display_handler=DisplayHandler(
                display_name='Sample transparency',
                display_units='deg',
                latex_name='Sample transparency',
                latex_units=r'\mathrm{deg}',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_instrument.calib_sample_transparency'],
                cif_names=['_instr.sample_transparency'],
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
        """Set the instrument misalignment offset (deg)."""
        self._calib_twotheta_offset.value = value

    @property
    def calib_sample_displacement(self) -> Parameter:
        """
        Specimen-displacement peak-position correction (deg).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._calib_sample_displacement

    @calib_sample_displacement.setter
    def calib_sample_displacement(self, value: float) -> None:
        """Set the specimen-displacement correction (deg)."""
        self._calib_sample_displacement.value = value

    @property
    def calib_sample_transparency(self) -> Parameter:
        """
        Sample-transparency peak-position correction (deg).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._calib_sample_transparency

    @calib_sample_transparency.setter
    def calib_sample_transparency(self, value: float) -> None:
        """Set the sample-transparency correction (deg)."""
        self._calib_sample_transparency.value = value
