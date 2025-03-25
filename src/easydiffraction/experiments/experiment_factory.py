from easydiffraction.experiments.experiment_base import BaseExperiment
from easydiffraction.experiments.mixins.powder import PowderExperimentMixin

# Component imports
from easydiffraction.experiments.components.instr_setup import (
    InstrSetupBase,
    InstrSetupConstWavelengthMixin,
    InstrSetupTimeOfFlightMixin,
)
from easydiffraction.experiments.components.instr_calib import (
    InstrCalibBase,
    InstrCalibConstWavelengthMixin,
    InstrCalibTimeOfFlightMixin,
)
from easydiffraction.experiments.components.peak_profile import (
    PeakProfileBase,
    PeakProfileConstWavelengthMixin,
    PeakProfileTimeOfFlightMixin,
)
from easydiffraction.experiments.components.peak_broad import (
    PeakBroadBase,
    PeakBroadConstWavelengthMixin,
    PeakBroadTimeOfFlightMixin,
)
from easydiffraction.experiments.components.peak_asymm import (
    PeakAsymmBase,
    PeakAsymmConstWavelengthMixin,
    PeakAsymmTimeOfFlightMixin,
)
from easydiffraction.experiments.components.linked_phases import (
    LinkedPhase,
    LinkedPhases,
)
from easydiffraction.experiments.background import BackgroundFactory
from easydiffraction.experiments.datastore import DatastoreFactory


class ExperimentFactory:
    """Factory for creating dynamically assembled Experiment instances."""

    @staticmethod
    def create_experiment(id, diffr_mode, expt_mode, radiation_probe):
        experiment_mixins = ExperimentFactory._collect_experiment_mixins(diffr_mode, expt_mode)

        if diffr_mode == "powder":
            experiment_mixins.append(PowderExperimentMixin)

        # BaseExperiment comes last
        bases = tuple(experiment_mixins + [BaseExperiment])

        # Dynamically assemble class
        ExperimentCls = type(
            f"Experiment_{diffr_mode}_{expt_mode}_{radiation_probe}",
            bases,
            {}
        )

        # Create instance of dynamically assembled class
        instance = ExperimentCls(id=id,
                                 diffr_mode=diffr_mode,
                                 expt_mode=expt_mode,
                                 radiation_probe=radiation_probe)

        # Attach instrument setup and calibration components
        instance.instr_setup = ExperimentFactory._create_component(
            InstrSetupBase,
            ExperimentFactory.get_instr_setup_mixins(expt_mode),
            "InstrSetup"
        )
        instance.instr_calib = ExperimentFactory._create_component(
            InstrCalibBase,
            ExperimentFactory.get_instr_calib_mixins(expt_mode),
            "InstrCalib"
        )

        # Attach peak profile, broadening, and asymmetry components
        instance.peak_profile = ExperimentFactory._create_component(
            PeakProfileBase,
            ExperimentFactory.get_peak_profile_mixins(diffr_mode, expt_mode),
            "PeakProfile"
        )
        instance.peak_broad = ExperimentFactory._create_component(
            PeakBroadBase,
            ExperimentFactory.get_peak_broad_mixins(diffr_mode, expt_mode),
            "PeakBroad"
        )
        instance.peak_asymm = ExperimentFactory._create_component(
            PeakAsymmBase,
            ExperimentFactory.get_peak_asymm_mixins(diffr_mode, expt_mode),
            "PeakAsymm"
        )

        # Attach linked phases component
        instance.linked_phases = LinkedPhases()

        # Attach background component
        instance.background = BackgroundFactory.create_background("point")

        # Attach datastore component
        instance.datastore = DatastoreFactory.create_datastore(diffr_mode, instance)

        return instance

    @staticmethod
    def _create_component(base_cls, mixins, class_name):
        if not mixins:
            return None
        bases = tuple([base_cls] + mixins)
        ComponentCls = type(class_name, bases, {})
        return ComponentCls()

    @staticmethod
    def _collect_experiment_mixins(diffr_mode, expt_mode):
        mixins = []
        mixins.extend(ExperimentFactory.get_instr_calib_mixins(expt_mode))
        mixins.extend(ExperimentFactory.get_peak_profile_mixins(diffr_mode, expt_mode))
        mixins.extend(ExperimentFactory.get_peak_broad_mixins(diffr_mode, expt_mode))
        mixins.extend(ExperimentFactory.get_peak_asymm_mixins(diffr_mode, expt_mode))
        return mixins

    @staticmethod
    def get_instr_setup_mixins(expt_mode):
        return {
            "constant_wavelength": [InstrSetupConstWavelengthMixin],
            "time_of_flight": [InstrSetupTimeOfFlightMixin]
        }.get(expt_mode, [])

    @staticmethod
    def get_instr_calib_mixins(expt_mode):
        return {
            "constant_wavelength": [InstrCalibConstWavelengthMixin],
            "time_of_flight": [InstrCalibTimeOfFlightMixin]
        }.get(expt_mode, [])

    @staticmethod
    def get_peak_profile_mixins(diffr_mode, expt_mode):
        if diffr_mode != "powder":
            return []
        return {
            "constant_wavelength": [PeakProfileConstWavelengthMixin],
            "time_of_flight": [PeakProfileTimeOfFlightMixin]
        }.get(expt_mode, [])

    @staticmethod
    def get_peak_broad_mixins(diffr_mode, expt_mode):
        if diffr_mode != "powder":
            return []
        return {
            "constant_wavelength": [PeakBroadConstWavelengthMixin],
            "time_of_flight": [PeakBroadTimeOfFlightMixin]
        }.get(expt_mode, [])

    @staticmethod
    def get_peak_asymm_mixins(diffr_mode, expt_mode):
        if diffr_mode != "powder":
            return []
        return {
            "constant_wavelength": [PeakAsymmConstWavelengthMixin],
            "time_of_flight": [PeakAsymmTimeOfFlightMixin]
        }.get(expt_mode, [])