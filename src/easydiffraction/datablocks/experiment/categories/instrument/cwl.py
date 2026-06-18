# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Constant-wavelength powder and single-crystal instruments."""

from __future__ import annotations

from easydiffraction.core.display_handler import DisplayHandler
from easydiffraction.core.metadata import CalculatorSupport
from easydiffraction.core.metadata import Compatibility
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.core.variable import Parameter
from easydiffraction.datablocks.experiment.categories.instrument.base import InstrumentBase
from easydiffraction.datablocks.experiment.categories.instrument.factory import InstrumentFactory
from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import CalculatorEnum
from easydiffraction.datablocks.experiment.item.enums import RadiationProbeEnum
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

        # Second incident wavelength (the X-ray Cu K-alpha1/K-alpha2
        # doublet). These are non-refinable NumericDescriptors: only
        # fixed doublet values are currently consumed by CrysFML, so a
        # refinable Parameter would let a fit silently move a value
        # with no effect. Defaults of 0.0 mean monochromatic, as today.
        self._setup_wavelength_2: NumericDescriptor = NumericDescriptor(
            name='wavelength_2',
            description='Second incident wavelength (e.g. X-ray K-alpha2)',
            units='angstroms',
            display_handler=DisplayHandler(
                display_name='Wavelength 2',
                display_units='Å',
                latex_name='Wavelength 2',
                latex_units=r'\AA',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0.0),
            ),
            tags=TagSpec(
                edi_names=['_instrument.setup_wavelength_2'],
                cif_names=['_instr.wavelength_2'],
            ),
        )
        self._setup_wavelength_2_to_1_ratio: NumericDescriptor = NumericDescriptor(
            name='wavelength_2_to_1_ratio',
            description='Relative intensity of wavelength_2 to wavelength (I₂/I₁)',
            units='',
            display_handler=DisplayHandler(
                display_name='Wavelength 2/1 ratio',
                display_units='',
                latex_name='Wavelength 2/1 ratio',
                latex_units='',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0.0, le=1.0),
            ),
            tags=TagSpec(
                edi_names=['_instrument.setup_wavelength_2_to_1_ratio'],
                cif_names=['_instr.wavelength_2_to_1_ratio'],
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

    @property
    def setup_wavelength_2(self) -> NumericDescriptor:
        """
        Second incident wavelength λ₂ (Å), e.g. the X-ray K-alpha2 line.

        Reading returns the underlying ``NumericDescriptor``; assigning
        a number updates its value. Default ``0.0`` means no second
        component (monochromatic). Non-refinable; CrysFML consumes it
        when ``setup_wavelength_2_to_1_ratio`` is positive.
        """
        return self._setup_wavelength_2

    @setup_wavelength_2.setter
    def setup_wavelength_2(self, value: float) -> None:
        """Set the second incident wavelength λ₂ (Å)."""
        self._setup_wavelength_2.value = value

    @property
    def setup_wavelength_2_to_1_ratio(self) -> NumericDescriptor:
        """
        Relative intensity of wavelength_2 to wavelength (I₂/I₁).

        The ``_2_to_1_`` ordering names the direction: numerator is the
        second component, denominator the first. Range ``[0, 1]``;
        default ``0.0`` disables the second component. Non-refinable;
        CrysFML consumes it together with ``setup_wavelength_2``.
        """
        return self._setup_wavelength_2_to_1_ratio

    @setup_wavelength_2_to_1_ratio.setter
    def setup_wavelength_2_to_1_ratio(self, value: float) -> None:
        """
        Set the wavelength_2-to-wavelength intensity ratio (I₂/I₁).
        """
        self._setup_wavelength_2_to_1_ratio.value = value


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


class CwlPdInstrumentBase(CwlInstrumentBase):
    """Base class for CW powder diffractometers."""

    def __init__(self) -> None:
        """Initialize the CW powder diffractometer base."""
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


@InstrumentFactory.register
class CwlPdNeutronInstrument(CwlPdInstrumentBase):
    """CW neutron powder diffractometer."""

    type_info = TypeInfo(
        tag='cwl-pd-neutron',
        description='CW neutron powder diffractometer',
    )
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.CONSTANT_WAVELENGTH}),
        sample_form=frozenset({SampleFormEnum.POWDER}),
        radiation_probe=frozenset({RadiationProbeEnum.NEUTRON}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({
            CalculatorEnum.CRYSPY,
            CalculatorEnum.CRYSFML,
        }),
    )

    def __init__(self) -> None:
        """Initialize the CW neutron powder diffractometer."""
        super().__init__()


@InstrumentFactory.register
class CwlPdXrayInstrument(CwlPdInstrumentBase):
    """CW X-ray powder diffractometer."""

    type_info = TypeInfo(
        tag='cwl-pd-xray',
        description='CW X-ray powder diffractometer',
    )
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.CONSTANT_WAVELENGTH}),
        sample_form=frozenset({SampleFormEnum.POWDER}),
        radiation_probe=frozenset({RadiationProbeEnum.XRAY}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({
            CalculatorEnum.CRYSPY,
            CalculatorEnum.CRYSFML,
        }),
    )

    def __init__(self) -> None:
        """Initialize the CW X-ray powder diffractometer."""
        super().__init__()

        self._setup_polarization_coefficient: Parameter = Parameter(
            name='polarization_coefficient',
            description='CW Lorentz-polarization coefficient',
            units='',
            display_handler=DisplayHandler(
                display_name='Polarization coefficient',
                display_units='',
                latex_name='Polarization coefficient',
                latex_units='',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0.0, le=1.0),
            ),
            tags=TagSpec(
                edi_names=['_instrument.setup_polarization_coefficient'],
                cif_names=['_instr.polarization_coefficient'],
            ),
        )

        self._setup_monochromator_twotheta: Parameter = Parameter(
            name='monochromator_twotheta',
            description='Pre-specimen monochromator 2theta angle',
            units='degrees',
            display_handler=DisplayHandler(
                display_name='Monochromator 2θ',
                display_units='deg',
                latex_name=r'Monochromator $2\theta$',
                latex_units=r'\mathrm{deg}',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0.0, lt=180.0),
            ),
            tags=TagSpec(
                edi_names=['_instrument.setup_monochromator_twotheta'],
                cif_names=['_instr.monochromator_twotheta'],
            ),
        )

    @property
    def setup_polarization_coefficient(self) -> NumericDescriptor:
        """
        CW Lorentz-polarization coefficient.

        Reading returns the underlying ``NumericDescriptor``; assigning
        a number updates its value. Default ``0.0`` disables the
        polarization correction.
        """
        return self._setup_polarization_coefficient

    @setup_polarization_coefficient.setter
    def setup_polarization_coefficient(self, value: float) -> None:
        """Set the CW Lorentz-polarization coefficient."""
        self._setup_polarization_coefficient.value = value

    @property
    def setup_monochromator_twotheta(self) -> NumericDescriptor:
        """
        Pre-specimen monochromator 2theta angle (deg).

        Reading returns the underlying ``NumericDescriptor``; assigning
        a number updates its value. Default ``0.0`` means no
        monochromator.
        """
        return self._setup_monochromator_twotheta

    @setup_monochromator_twotheta.setter
    def setup_monochromator_twotheta(self, value: float) -> None:
        """Set the pre-specimen monochromator 2theta angle (deg)."""
        self._setup_monochromator_twotheta.value = value
