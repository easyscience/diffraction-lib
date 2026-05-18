# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Experiment type descriptor (form, beam, probe, scattering).

This lightweight container stores the categorical attributes defining an
experiment configuration and handles CIF serialization via
``CifHandler``.
"""

from __future__ import annotations

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import MembershipValidator
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.datablocks.experiment.categories.experiment_type.factory import (
    ExperimentTypeFactory,
)
from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import RadiationProbeEnum
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
from easydiffraction.io.cif.handler import CifHandler


@ExperimentTypeFactory.register
class ExperimentType(CategoryItem):
    """Container of attributes defining the experiment type."""

    _category_code = 'expt_type'

    type_info = TypeInfo(
        tag='default',
        description='Experiment type descriptor',
    )

    def __init__(self) -> None:
        super().__init__()

        self._sample_form = StringDescriptor(
            name='sample_form',
            description='Powder diffraction or single crystal diffraction',
            value_spec=AttributeSpec(
                default=SampleFormEnum.default().value,
                validator=MembershipValidator(allowed=[member.value for member in SampleFormEnum]),
            ),
            cif_handler=CifHandler(names=['_expt_type.sample_form']),
        )

        self._beam_mode = StringDescriptor(
            name='beam_mode',
            description='Constant wavelength (CW) or time-of-flight (TOF) measurement',
            value_spec=AttributeSpec(
                default=BeamModeEnum.default().value,
                validator=MembershipValidator(allowed=[member.value for member in BeamModeEnum]),
            ),
            cif_handler=CifHandler(names=['_expt_type.beam_mode']),
        )
        self._radiation_probe = StringDescriptor(
            name='radiation_probe',
            description='Neutron or X-ray diffraction measurement',
            value_spec=AttributeSpec(
                default=RadiationProbeEnum.default().value,
                validator=MembershipValidator(
                    allowed=[member.value for member in RadiationProbeEnum]
                ),
            ),
            cif_handler=CifHandler(names=['_expt_type.radiation_probe']),
        )
        self._scattering_type = StringDescriptor(
            name='scattering_type',
            description='Conventional Bragg diffraction or total scattering (PDF)',
            value_spec=AttributeSpec(
                default=ScatteringTypeEnum.default().value,
                validator=MembershipValidator(
                    allowed=[member.value for member in ScatteringTypeEnum]
                ),
            ),
            cif_handler=CifHandler(names=['_expt_type.scattering_type']),
        )

    # ------------------------------------------------------------------
    #  Private setters (used by factories and loaders only)
    # ------------------------------------------------------------------

    def _set_sample_form(self, value: str) -> None:
        self._sample_form.value = value

    def _set_beam_mode(self, value: str) -> None:
        self._beam_mode.value = value

    def _set_radiation_probe(self, value: str) -> None:
        self._radiation_probe.value = value

    def _set_scattering_type(self, value: str) -> None:
        self._scattering_type.value = value

    # ------------------------------------------------------------------
    #  Public read-only properties
    # ------------------------------------------------------------------

    @property
    def sample_form(self) -> StringDescriptor:
        """
        Powder diffraction or single crystal diffraction.

        Reading this property returns the underlying
        ``StringDescriptor`` object.
        """
        return self._sample_form

    @property
    def beam_mode(self) -> StringDescriptor:
        """
        Constant wavelength (CW) or time-of-flight (TOF) measurement.

        Reading this property returns the underlying
        ``StringDescriptor`` object.
        """
        return self._beam_mode

    @property
    def radiation_probe(self) -> StringDescriptor:
        """
        Neutron or X-ray diffraction measurement.

        Reading this property returns the underlying
        ``StringDescriptor`` object.
        """
        return self._radiation_probe

    @property
    def scattering_type(self) -> StringDescriptor:
        """
        Conventional Bragg diffraction or total scattering (PDF).

        Reading this property returns the underlying
        ``StringDescriptor`` object.
        """
        return self._scattering_type
