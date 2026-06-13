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
from easydiffraction.core.display_handler import DisplayHandler
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.variable import EnumDescriptor
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

    _category_code = 'experiment_type'

    type_info = TypeInfo(
        tag='default',
        description='Experiment type descriptor',
    )

    def __init__(self) -> None:
        super().__init__()

        self._sample_form = EnumDescriptor(
            name='sample_form',
            enum=SampleFormEnum,
            description='Powder diffraction or single crystal diffraction',
            cif_handler=CifHandler(
                names=['_experiment_type.sample_form'],
                import_names=['_expt_type.sample_form'],
                iucr_name='_easydiffraction_experiment_type.sample_form',
            ),
            display_handler=DisplayHandler(
                display_name='Sample form',
                latex_name='Sample form',
            ),
        )

        self._beam_mode = EnumDescriptor(
            name='beam_mode',
            enum=BeamModeEnum,
            description='Constant wavelength (CW) or time-of-flight (TOF) measurement',
            cif_handler=CifHandler(
                names=['_experiment_type.beam_mode'],
                import_names=['_expt_type.beam_mode'],
                iucr_name='_easydiffraction_experiment_type.beam_mode',
            ),
            display_handler=DisplayHandler(
                display_name='Beam mode',
                latex_name='Beam mode',
            ),
        )
        self._radiation_probe = EnumDescriptor(
            name='radiation_probe',
            enum=RadiationProbeEnum,
            description='Neutron or X-ray diffraction measurement',
            cif_handler=CifHandler(
                names=['_experiment_type.radiation_probe'],
                import_names=['_expt_type.radiation_probe'],
                iucr_name='_easydiffraction_experiment_type.radiation_probe',
            ),
            display_handler=DisplayHandler(
                display_name='Probe',
                latex_name='Probe',
            ),
        )
        self._scattering_type = EnumDescriptor(
            name='scattering_type',
            enum=ScatteringTypeEnum,
            description='Conventional Bragg diffraction or total scattering (PDF)',
            cif_handler=CifHandler(
                names=['_experiment_type.scattering_type'],
                import_names=['_expt_type.scattering_type'],
                iucr_name='_easydiffraction_experiment_type.scattering_type',
            ),
            display_handler=DisplayHandler(
                display_name='Scattering type',
                latex_name='Scattering type',
            ),
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
    def sample_form(self) -> EnumDescriptor:
        """
        Powder diffraction or single crystal diffraction.

        Reading this property returns the underlying ``EnumDescriptor``
        object.
        """
        return self._sample_form

    @property
    def beam_mode(self) -> EnumDescriptor:
        """
        Constant wavelength (CW) or time-of-flight (TOF) measurement.

        Reading this property returns the underlying ``EnumDescriptor``
        object.
        """
        return self._beam_mode

    @property
    def radiation_probe(self) -> EnumDescriptor:
        """
        Neutron or X-ray diffraction measurement.

        Reading this property returns the underlying ``EnumDescriptor``
        object.
        """
        return self._radiation_probe

    @property
    def scattering_type(self) -> EnumDescriptor:
        """
        Conventional Bragg diffraction or total scattering (PDF).

        Reading this property returns the underlying ``EnumDescriptor``
        object.
        """
        return self._scattering_type
