# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Factory for creating experiment instances from various inputs.

Provides individual class methods for each creation pathway:
``from_cif_path``, ``from_cif_str``, ``from_data_path``, and
``from_scratch``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typeguard import typechecked

from easydiffraction.core.factory import FactoryBase
from easydiffraction.datablocks.experiment.categories.experiment_type import ExperimentType
from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
from easydiffraction.io.cif.parse import document_from_path
from easydiffraction.io.cif.parse import document_from_string
from easydiffraction.io.cif.parse import name_from_block
from easydiffraction.io.cif.parse import pick_sole_block
from easydiffraction.utils.logging import log

if TYPE_CHECKING:
    import gemmi

    from easydiffraction.datablocks.experiment.item.base import ExperimentBase


class ExperimentFactory(FactoryBase):
    """Creates Experiment instances with only relevant attributes."""

    _default_rules = {
        frozenset({
            ('scattering_type', ScatteringTypeEnum.BRAGG),
            ('sample_form', SampleFormEnum.POWDER),
        }): 'bragg-pd',
        frozenset({
            ('scattering_type', ScatteringTypeEnum.TOTAL),
            ('sample_form', SampleFormEnum.POWDER),
        }): 'total-pd',
        frozenset({
            ('scattering_type', ScatteringTypeEnum.BRAGG),
            ('sample_form', SampleFormEnum.SINGLE_CRYSTAL),
            ('beam_mode', BeamModeEnum.CONSTANT_WAVELENGTH),
        }): 'bragg-sc-cwl',
        frozenset({
            ('scattering_type', ScatteringTypeEnum.BRAGG),
            ('sample_form', SampleFormEnum.SINGLE_CRYSTAL),
            ('beam_mode', BeamModeEnum.TIME_OF_FLIGHT),
        }): 'bragg-sc-tof',
    }

    # TODO: Add to core/factory.py?
    def __init__(self):
        log.error(
            'Experiment objects must be created using class methods such as '
            '`ExperimentFactory.from_cif_str(...)`, etc.'
        )

    # ------------------------------------------------------------------
    # Private helper methods
    # ------------------------------------------------------------------

    @classmethod
    @typechecked
    def _create_experiment_type(
        cls,
        sample_form: str | None = None,
        beam_mode: str | None = None,
        radiation_probe: str | None = None,
        scattering_type: str | None = None,
    ) -> ExperimentType:
        """Construct an ExperimentType, using defaults for omitted
        values.
        """
        # Note: validation of input values is done via Descriptor setter
        # methods

        et = ExperimentType()

        if sample_form is not None:
            et._set_sample_form(sample_form)
        if beam_mode is not None:
            et._set_beam_mode(beam_mode)
        if radiation_probe is not None:
            et._set_radiation_probe(radiation_probe)
        if scattering_type is not None:
            et._set_scattering_type(scattering_type)

        return et

    @classmethod
    @typechecked
    def _resolve_class(cls, expt_type: ExperimentType):
        """Look up the experiment class from the type enums."""
        tag = cls.default_tag(
            scattering_type=expt_type.scattering_type.value,
            sample_form=expt_type.sample_form.value,
            beam_mode=expt_type.beam_mode.value,
        )
        return cls._supported_map()[tag]

    @classmethod
    # TODO: @typechecked fails to find gemmi?
    def _from_gemmi_block(
        cls,
        block: gemmi.cif.Block,
    ) -> ExperimentBase:
        """Build a model instance from a single CIF block."""
        name = name_from_block(block)

        expt_type = ExperimentType()
        for param in expt_type.parameters:
            param.from_cif(block)

        expt_class = cls._resolve_class(expt_type)
        expt_obj = expt_class(name=name, type=expt_type)

        for category in expt_obj.categories:
            category.from_cif(block)

        return expt_obj

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    @classmethod
    @typechecked
    def from_scratch(
        cls,
        *,
        name: str,
        sample_form: str | None = None,
        beam_mode: str | None = None,
        radiation_probe: str | None = None,
        scattering_type: str | None = None,
    ) -> ExperimentBase:
        """
        Create an experiment without measured data.

        Parameters
        ----------
        name
            Experiment identifier.
        sample_form
            Sample form (e.g. ``'powder'``).
        beam_mode
            Beam mode (e.g. ``'constant wavelength'``).
        radiation_probe
            Radiation probe (e.g. ``'neutron'``).
        scattering_type
            Scattering type (e.g. ``'bragg'``).

        Returns
        -------
            An experiment instance with only metadata.
        """
        expt_type = cls._create_experiment_type(
            sample_form=sample_form,
            beam_mode=beam_mode,
            radiation_probe=radiation_probe,
            scattering_type=scattering_type,
        )
        expt_class = cls._resolve_class(expt_type)
        expt_obj = expt_class(name=name, type=expt_type)
        return expt_obj

    # TODO: add minimal default configuration for missing parameters
    @classmethod
    @typechecked
    def from_cif_str(
        cls,
        cif_str: str,
    ) -> ExperimentBase:
        """
        Create an experiment from a CIF string.


        Parameters
        ----------
        cif_str
            Full CIF document as a string.

        Returns
        -------

            A populated experiment instance.
        """
        doc = document_from_string(cif_str)
        block = pick_sole_block(doc)
        return cls._from_gemmi_block(block)

    # TODO: Read content and call self.from_cif_str
    @classmethod
    @typechecked
    def from_cif_path(
        cls,
        cif_path: str,
    ) -> ExperimentBase:
        """
        Create an experiment from a CIF file path.


        Parameters
        ----------
        cif_path
            Path to a CIF file.

        Returns
        -------

            A populated experiment instance.
        """
        doc = document_from_path(cif_path)
        block = pick_sole_block(doc)
        return cls._from_gemmi_block(block)

    @classmethod
    @typechecked
    def from_data_path(
        cls,
        *,
        name: str,
        data_path: str,
        sample_form: str | None = None,
        beam_mode: str | None = None,
        radiation_probe: str | None = None,
        scattering_type: str | None = None,
    ) -> ExperimentBase:
        """
        Create an experiment from a raw data ASCII file.

        Parameters
        ----------
        name
            Experiment identifier.
        data_path
            Path to the measured data file.
        sample_form
            Sample form (e.g. ``'powder'``).
        beam_mode
            Beam mode (e.g. ``'constant wavelength'``).
        radiation_probe
            Radiation probe (e.g. ``'neutron'``).
        scattering_type
            Scattering type (e.g. ``'bragg'``).

        Returns
        -------
            An experiment instance with measured data attached.
        """
        expt_obj = cls.from_scratch(
            name=name,
            sample_form=sample_form,
            beam_mode=beam_mode,
            radiation_probe=radiation_probe,
            scattering_type=scattering_type,
        )
        expt_obj._load_ascii_data_to_experiment(data_path)
        return expt_obj
