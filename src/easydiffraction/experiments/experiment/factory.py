# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import gemmi

from easydiffraction.core.factory import FactoryBase
from easydiffraction.experiments.categories.experiment_type import ExperimentType
from easydiffraction.experiments.experiment import BraggPdExperiment
from easydiffraction.experiments.experiment import BraggScExperiment
from easydiffraction.experiments.experiment import TotalPdExperiment
from easydiffraction.experiments.experiment.base import ExperimentBase
from easydiffraction.experiments.experiment.enums import BeamModeEnum
from easydiffraction.experiments.experiment.enums import RadiationProbeEnum
from easydiffraction.experiments.experiment.enums import SampleFormEnum
from easydiffraction.experiments.experiment.enums import ScatteringTypeEnum


class ExperimentFactory(FactoryBase):
    """Creates Experiment instances with only relevant attributes."""

    _ALLOWED_ARG_SPECS = [
        {'required': ['cif_path'], 'optional': []},
        {'required': ['cif_str'], 'optional': []},
        {
            'required': ['name', 'data_path'],
            'optional': ['sample_form', 'beam_mode', 'radiation_probe', 'scattering_type'],
        },
        {
            'required': ['name'],
            'optional': ['sample_form', 'beam_mode', 'radiation_probe', 'scattering_type'],
        },
    ]

    _SUPPORTED = {
        ScatteringTypeEnum.BRAGG: {
            SampleFormEnum.POWDER: BraggPdExperiment,
            SampleFormEnum.SINGLE_CRYSTAL: BraggScExperiment,
        },
        ScatteringTypeEnum.TOTAL: {
            SampleFormEnum.POWDER: TotalPdExperiment,
        },
    }

    @classmethod
    def create(cls, **kwargs):
        """Create an `ExperimentBase` using a validated argument
        combination.
        """
        # Check for valid argument combinations
        user_args = {k for k, v in kwargs.items() if v is not None}
        cls._validate_args(user_args, cls._ALLOWED_ARG_SPECS, cls.__name__)

        # Validate enum arguments if provided
        if 'sample_form' in kwargs:
            SampleFormEnum(kwargs['sample_form'])
        if 'beam_mode' in kwargs:
            BeamModeEnum(kwargs['beam_mode'])
        if 'radiation_probe' in kwargs:
            RadiationProbeEnum(kwargs['radiation_probe'])
        if 'scattering_type' in kwargs:
            ScatteringTypeEnum(kwargs['scattering_type'])

        # Dispatch to the appropriate creation method
        if 'cif_path' in kwargs:
            return cls._create_from_cif_path(kwargs['cif_path'])
        elif 'cif_str' in kwargs:
            return cls._create_from_cif_str(kwargs['cif_str'])
        elif 'data_path' in kwargs:
            return cls._create_from_data_path(kwargs)
        elif 'name' in kwargs:
            return cls._create_without_data(kwargs)

    # -------------
    # gemmi helpers
    # -------------

    # TODO: Move to a common CIF utility module? io.cif.parse?
    @staticmethod
    def _read_cif_document_from_path(path: str) -> gemmi.cif.Document:
        """Read a CIF document from a file path."""
        return gemmi.cif.read_file(path)

    # TODO: Move to a common CIF utility module? io.cif.parse?
    @staticmethod
    def _read_cif_document_from_string(text: str) -> gemmi.cif.Document:
        """Read a CIF document from a raw text string."""
        return gemmi.cif.read_string(text)

    # TODO: Move to a common CIF utility module? io.cif.parse?
    @classmethod
    def _pick_first_block(
        cls,
        doc: gemmi.cif.Document,
    ) -> gemmi.cif.Block:
        """Pick the first experimental block from a CIF document."""
        try:
            return doc.sole_block()
        except Exception:
            return doc[0]

    # TODO: Move to a common CIF utility module? io.cif.parse?
    @classmethod
    def _extract_name_from_block(cls, block: gemmi.cif.Block) -> str:
        """Extract a model name from the CIF block name."""
        return block.name or 'model'

    # TODO: Move to a common CIF utility module? io.cif.parse?
    @classmethod
    def _create_experiment_from_block(
        cls,
        block: gemmi.cif.Block,
    ) -> ExperimentBase:
        """Build a model instance from a single CIF block."""
        name = cls._extract_name_from_block(block)

        # TODO: experiment type need to be read from CIF block
        kwargs = {'beam_mode': BeamModeEnum.CONSTANT_WAVELENGTH}
        expt_type = cls._make_experiment_type(kwargs)

        # Create experiment instance of appropriate class
        scattering_type = expt_type.scattering_type.value
        sample_form = expt_type.sample_form.value
        expt_class = cls._SUPPORTED[scattering_type][sample_form]
        expt_obj = expt_class(name=name, type=expt_type)

        # TODO: Read all categories from CIF block into experiment

        # TODO: Read data from CIF block into experiment datastore

        return expt_obj

    # -------------------------------
    # Private creation helper methods
    # -------------------------------

    @classmethod
    def _create_from_cif_path(cls, cif_path):
        """Create an experiment from a CIF file path."""
        doc = cls._read_cif_document_from_path(cif_path)
        block = cls._pick_first_block(doc)
        return cls._create_experiment_from_block(block)

    @staticmethod
    def _create_from_cif_str(cif_str):
        """Create an experiment from a CIF string.

        Not yet implemented.
        """
        # TODO: Implement CIF string loading logic
        raise NotImplementedError('CIF string loading not implemented yet.')

    @classmethod
    def _create_from_data_path(cls, kwargs):
        """Create an experiment from a raw data ASCII file.

        Loads the experiment and attaches measured data from the
        specified file.
        """
        expt_type = cls._make_experiment_type(kwargs)
        scattering_type = expt_type.scattering_type.value
        sample_form = expt_type.sample_form.value
        expt_class = cls._SUPPORTED[scattering_type][sample_form]
        expt_name = kwargs['name']
        expt_obj = expt_class(name=expt_name, type=expt_type)
        data_path = kwargs['data_path']
        expt_obj._load_ascii_data_to_experiment(data_path)
        return expt_obj

    @classmethod
    def _create_without_data(cls, kwargs):
        """Create an experiment without measured data.

        Returns an experiment instance with only metadata and
        configuration.
        """
        expt_type = cls._make_experiment_type(kwargs)
        scattering_type = expt_type.scattering_type.value
        sample_form = expt_type.sample_form.value
        expt_class = cls._SUPPORTED[scattering_type][sample_form]
        expt_name = kwargs['name']
        expt_obj = expt_class(name=expt_name, type=expt_type)
        return expt_obj

    @classmethod
    def _make_experiment_type(cls, kwargs):
        """Helper to construct an ExperimentType from keyword arguments,
        using defaults as needed.
        """
        return ExperimentType(
            sample_form=kwargs.get('sample_form', SampleFormEnum.default()),
            beam_mode=kwargs.get('beam_mode', BeamModeEnum.default()),
            radiation_probe=kwargs.get('radiation_probe', RadiationProbeEnum.default()),
            scattering_type=kwargs.get('scattering_type', ScatteringTypeEnum.default()),
        )

    @staticmethod
    def _is_valid_args(user_args):
        """Validate user argument set against allowed combinations.

        Returns True if the argument set matches any valid combination,
        else False.
        """
        user_arg_set = set(user_args)
        for arg_set in ExperimentFactory._valid_arg_sets:
            required = set(arg_set['required'])
            optional = set(arg_set['optional'])
            # Must have all required, and only required+optional
            if required.issubset(user_arg_set) and user_arg_set <= (required | optional):
                return True
        return False
