import numpy as np
import tabulate

from abc import ABC, abstractmethod

from easydiffraction.experiments.components.experiment_type import ExperimentType
from easydiffraction.experiments.components.instrument import InstrumentFactory
from easydiffraction.experiments.components.peak import PeakFactory

from easydiffraction.experiments.collections.linked_phases import LinkedPhases
from easydiffraction.experiments.collections.background import BackgroundFactory
from easydiffraction.experiments.collections.datastore import DatastoreFactory

from easydiffraction.utils.formatting import paragraph, warning
from easydiffraction.utils.chart_plotter import ChartPlotter

from easydiffraction.core.objects import Datablock

from easydiffraction.core.constants import (
    DEFAULT_SAMPLE_FORM,
    DEFAULT_BEAM_MODE,
    DEFAULT_RADIATION_PROBE,
    DEFAULT_PEAK_PROFILE_TYPE,
    DEFAULT_BACKGROUND_TYPE
)


class BaseExperiment(Datablock):
    """
    Base class for all experiments with only core attributes.
    Wraps experiment type, instrument and datastore.
    """

    # TODO: Find better name for the attribute 'type'.
    #  1. It shadows the built-in type() function.
    #  2. It is not very clear what it refers to.
    def __init__(self,
                 name: str,
                 type: ExperimentType):
        super().__init__()
        self._name = name
        self.type = type
        self.instrument = InstrumentFactory.create(
            beam_mode=self.type.beam_mode.value)
        self.datastore = DatastoreFactory.create(
            sample_form=self.type.sample_form.value,
            experiment=self)

    # ----------------------
    # Name (ID) of the model
    # ----------------------

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, new_name: str):
        if not isinstance(new_name, str):
            raise TypeError("Name must be a string.")
        self._name = new_name

    # ---------------
    # Experiment type
    # ---------------

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, new_type):
        self._type = new_type
        #self._type.datablock_id = self.name

    # ----------
    # Instrument
    # ----------

    @property
    def instrument(self):
        return self._instrument

    @instrument.setter
    def instrument(self, new_instrument):
        self._instrument = new_instrument
        #self._instrument.datablock_id = self.name

    # ----------------
    # Misc. Need to be sorted
    # ----------------

    def as_cif(self, max_points=None):
        """
        Export the sample model to CIF format.
        Returns:
            str: CIF string representation of the experiment.
        """
        # Data block header
        cif_lines = [f"data_{self.name}"]

        # Experiment type
        cif_lines += ["", self.type.as_cif()]

        # Instrument setup and calibration
        cif_lines += ["", self.instrument.as_cif()]

        # Peak profile, broadening and asymmetry
        if hasattr(self, "peak"):
            cif_lines += ["", self.peak.as_cif()]

        # Phase scale factors for powder experiments
        if hasattr(self, "linked_phases"):
            cif_lines += ["", self.linked_phases.as_cif()]

        # Crystal scale factor for single crystal experiments
        if hasattr(self, "linked_crystal"):
            cif_lines += ["", self.linked_crystal.as_cif()]

        # Background points
        if hasattr(self, "background") and self.background:
            cif_lines += ["", self.background.as_cif()]

        # Measured data
        # TODO: This functionality should be moved to datastore.py
        # TODO: We need meas_data component which will use datastore to extract data
        # TODO: Datastore should be moved out of collections/
        if hasattr(self, "datastore") and hasattr(self.datastore, "pattern"):
            cif_lines.append("")
            cif_lines.append("loop_")
            category = '_pd_meas'  # TODO: Add category to pattern component
            attributes = ('2theta_scan', 'intensity_total', 'intensity_total_su')
            for attribute in attributes:
                cif_lines.append(f"{category}.{attribute}")
            pattern = self.datastore.pattern
            if max_points is not None and len(pattern.x) > 2 * max_points:
                for i in range(max_points):
                    x = pattern.x[i]
                    meas = pattern.meas[i]
                    meas_su = pattern.meas_su[i]
                    cif_lines.append(f"{x} {meas} {meas_su}")
                cif_lines.append("...")
                for i in range(-max_points, 0):
                    x = pattern.x[i]
                    meas = pattern.meas[i]
                    meas_su = pattern.meas_su[i]
                    cif_lines.append(f"{x} {meas} {meas_su}")
            else:
                for x, meas, meas_su in zip(pattern.x, pattern.meas, pattern.meas_su):
                    cif_lines.append(f"{x} {meas} {meas_su}")

        return "\n".join(cif_lines)

    def show_as_cif(self):
        cif_text = self.as_cif(max_points=5)
        lines = cif_text.splitlines()
        max_width = max(len(line) for line in lines)
        padded_lines = [f"│ {line.ljust(max_width)} │" for line in lines]
        top = f"╒{'═' * (max_width + 2)}╕"
        bottom = f"╘{'═' * (max_width + 2)}╛"

        print(paragraph(f"Experiment 🔬 '{self.name}' as cif"))
        print(top)
        print("\n".join(padded_lines))
        print(bottom)

    @abstractmethod
    def _load_ascii_data_to_experiment(self, data_path):
        pass

    @abstractmethod
    def show_meas_chart(self, x_min=None, x_max=None):
        """
        Abstract method to display data chart. Should be implemented in specific experiment mixins.
        """
        raise NotImplementedError("show_meas_chart() must be implemented in the subclass")


class PowderExperiment(BaseExperiment):
    """
    Powder experiment class with specific attributes.
    Wraps background, peak profile, and linked phases.
    """

    def __init__(self,
                 name: str,
                 type: ExperimentType):
        super().__init__(name=name,
                         type=type)
        self._background_type = DEFAULT_BACKGROUND_TYPE
        self._peak_profile_type = DEFAULT_PEAK_PROFILE_TYPE
        self.background = BackgroundFactory.create(
            background_type=self.background_type)
        self.peak = PeakFactory.create(
            beam_mode=self.type.beam_mode.value,
            profile_type=self.peak_profile_type)
        self.linked_phases = LinkedPhases()

    # -------------
    # Measured data
    # -------------

    def _load_ascii_data_to_experiment(self, data_path):
        """
        Loads x, y, sy values from an ASCII data file into the experiment.

        The file must be structured as:
            x  y  sy
        """
        try:
            data = np.loadtxt(data_path)
        except Exception as e:
            raise IOError(f"Failed to read data from {data_path}: {e}")

        if data.shape[1] < 2:
            raise ValueError("Data file must have at least two columns: x and y.")

        if data.shape[1] < 3:
            print("Warning: No uncertainty (sy) column provided. Defaulting to sqrt(y).")

        # Extract x, y, and sy data
        x = data[:, 0]
        y = data[:, 1]
        sy = data[:, 2] if data.shape[1] > 2 else np.sqrt(y)

        # Attach the data to the experiment's datastore
        self.datastore.pattern.x = x
        self.datastore.pattern.meas = y
        self.datastore.pattern.meas_su = sy

        print(paragraph("Data loaded successfully"))
        print(f"Experiment 🔬 '{self.name}'. Number of data points: {len(x)}")

    def show_meas_chart(self, x_min=None, x_max=None):
        pattern = self.datastore.pattern

        if pattern.meas is None or pattern.x is None:
            print(f"No measured data available for experiment {self.name}")
            return

        plotter = ChartPlotter()
        plotter.plot(
            y_values_list=[pattern.meas],
            x_values=pattern.x,
            x_min=x_min,
            x_max=x_max,
            title=paragraph(f"Measured data for experiment 🔬 '{self.name}'"),
            labels=['meas']
        )

    # ----------
    # Background
    # -----------

    @property
    def background(self):
        return self._background

    @background.setter
    def background(self, new_background):
        self._background = new_background
        #self._background.datablock_id = self.name

    @property
    def background_type(self):
        return self._background_type

    @background_type.setter
    def background_type(self, new_type):
        if new_type not in BackgroundFactory._supported:
            supported_types = list(BackgroundFactory._supported.keys())
            print(warning(f"Unknown background type '{new_type}'"))
            print(f'Supported background types: {supported_types}')
            print(f"For more information, use 'show_supported_background_types()'")
            return
        self._background_type = new_type
        print(paragraph(f"Background type for experiment '{self.name}' changed to"))
        print(new_type)
        # Recreate the background object with the new type
        self.background = BackgroundFactory.create(new_type)

    def show_supported_background_types(self):
        header = ["Background type", "Description"]
        table_data = []

        for name, config in BackgroundFactory._supported.items():
            description = getattr(config, '_description', 'No description provided.')
            table_data.append([name, description])

        print(paragraph("Supported background types"))
        print(tabulate.tabulate(
            table_data,
            headers=header,
            tablefmt="fancy_outline",
            numalign="left",
            stralign="left",
            showindex=False
        ))

    def show_current_background_type(self):
        print(paragraph("Current background type"))
        print(self.background_type)

    # ----
    # Peak
    # ----

    @property
    def peak(self):
        return self._peak

    @peak.setter
    def peak(self, new_peak):
        self._peak = new_peak
        #self._peak.datablock_id = self.name

    @property
    def peak_profile_type(self):
        return self._peak_profile_type

    @peak_profile_type.setter
    def peak_profile_type(self, new_type: str):
        if new_type not in PeakFactory._supported[self.type.beam_mode.value]:
            supported_types = list(PeakFactory._supported[self.type.beam_mode.value].keys())
            print(warning(f"Unsupported peak profile '{new_type}'"))
            print(f'Supported peak profiles: {supported_types}')
            print(f"For more information, use 'show_supported_peak_profile_types()'")
            return
        self._peak_profile_type = new_type
        print(paragraph(f"Peak profile type for experiment '{self.name}' changed to"))
        print(new_type)
        # Recreate the peak object with the new type
        self.peak = PeakFactory.create(beam_mode=self.type.beam_mode.value,
                                       profile_type=new_type)

    def show_supported_peak_profile_types(self):
        header = ["Peak profile type", "Description"]
        table_data = []

        for name, config in PeakFactory._supported[self.type.beam_mode.value].items():
            description = getattr(config, '_description', 'No description provided.')
            table_data.append([name, description])

        print(paragraph("Supported peak profile types"))
        print(tabulate.tabulate(
            table_data,
            headers=header,
            tablefmt="fancy_outline",
            numalign="left",
            stralign="left",
            showindex=False
        ))

    def show_current_peak_profile_type(self):
        print(paragraph("Current peak profile type"))
        print(self.peak_profile_type)

    # -------------
    # Linked phases
    # -------------

    @property
    def linked_phases(self):
        return self._linked_phases

    @linked_phases.setter
    def linked_phases(self, new_phases):
        self._linked_phases = new_phases
        #self._linked_phases.datablock_id = self.name


class SingleCrystalExperiment(BaseExperiment):
    """Powder experiment class with specific attributes."""

    def __init__(self,
                 name: str,
                 type: ExperimentType):
        super().__init__(name=name,
                         type=type)
        self.linked_crystal = None

    def show_meas_chart(self):
        print('Showing measured data chart is not implemented yet.')


class ExperimentFactory:
    """Creates Experiment instances with only relevant attributes."""
    _supported = {
        "powder": PowderExperiment,
        "single crystal": SingleCrystalExperiment
    }

    @classmethod
    def create(cls,
               name: str,
               sample_form: DEFAULT_SAMPLE_FORM,
               beam_mode: DEFAULT_BEAM_MODE,
               radiation_probe: DEFAULT_RADIATION_PROBE) -> BaseExperiment:
        # TODO: Add checks for expt_type and expt_class
        expt_type = ExperimentType(sample_form=sample_form,
                                   beam_mode=beam_mode,
                                   radiation_probe=radiation_probe)
        expt_class = cls._supported[sample_form]
        instance = expt_class(name=name, type=expt_type)
        return instance


# User exposed API for convenience
# TODO: Refactor based on the implementation of method add() in class Experiments
# TODO: Think of where to keep default values for sample_form, beam_mode, radiation_probe, as they are also defined in the
#  class ExperimentType
def Experiment(name: str,
               sample_form: str = DEFAULT_SAMPLE_FORM,
               beam_mode: str = DEFAULT_BEAM_MODE,
               radiation_probe: str = DEFAULT_RADIATION_PROBE,
               data_path: str = None):
    experiment = ExperimentFactory.create(
        name=name,
        sample_form=sample_form,
        beam_mode=beam_mode,
        radiation_probe=radiation_probe
    )
    experiment._load_ascii_data_to_experiment(data_path)
    return experiment
