# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.experiments.category_items.experiment_type import ExperimentType
from easydiffraction.experiments.enums import BeamModeEnum
from easydiffraction.experiments.enums import RadiationProbeEnum
from easydiffraction.experiments.enums import SampleFormEnum
from easydiffraction.experiments.enums import ScatteringTypeEnum
from easydiffraction.experiments.experiment_types import PairDistributionFunctionExperiment
from easydiffraction.experiments.experiment_types import PowderExperiment
from easydiffraction.experiments.experiment_types import SingleCrystalExperiment


class ExperimentFactory:
    """Creates Experiment instances with only relevant attributes."""

    _valid_arg_sets = [
        {
            'required': ['cif_path'],
            'optional': [],
        },
        {
            'required': ['cif_str'],
            'optional': [],
        },
        {
            'required': [
                'name',
                'data_path',
            ],
            'optional': [
                'sample_form',
                'beam_mode',
                'radiation_probe',
                'scattering_type',
            ],
        },
        {
            'required': ['name'],
            'optional': [
                'sample_form',
                'beam_mode',
                'radiation_probe',
                'scattering_type',
            ],
        },
    ]

    _supported = {
        ScatteringTypeEnum.BRAGG: {
            SampleFormEnum.POWDER: PowderExperiment,
            SampleFormEnum.SINGLE_CRYSTAL: SingleCrystalExperiment,
        },
        ScatteringTypeEnum.TOTAL: {
            SampleFormEnum.POWDER: PairDistributionFunctionExperiment,
        },
    }

    @classmethod
    def create(cls, **kwargs):
        """Main factory method for creating an experiment instance.

        Validates argument combinations and dispatches to the
        appropriate creation method. Raises ValueError if arguments are
        invalid or no valid dispatch is found.
        """
        # Check for valid argument combinations
        user_args = [k for k, v in kwargs.items() if v is not None]
        if not cls.is_valid_args(user_args):
            raise ValueError(f'Invalid argument combination: {user_args}')

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
            return cls._create_from_cif_path(kwargs)
        elif 'cif_str' in kwargs:
            return cls._create_from_cif_str(kwargs)
        elif 'data_path' in kwargs:
            return cls._create_from_data_path(kwargs)
        elif 'name' in kwargs:
            return cls._create_without_data(kwargs)

    @staticmethod
    def _create_from_cif_path(cif_path):
        """Create an experiment from a CIF file path.

        Not yet implemented.
        """
        # TODO: Implement CIF file loading logic
        raise NotImplementedError('CIF file loading not implemented yet.')

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
        expt_class = cls._supported[scattering_type][sample_form]
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
        expt_class = cls._supported[scattering_type][sample_form]
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
    def is_valid_args(user_args):
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


class Experiment:
    """User-facing API for creating an experiment.

    Accepts keyword arguments and delegates validation and creation to
    ExperimentFactory.
    """

    def __new__(cls, **kwargs):
        return ExperimentFactory.create(**kwargs)
