import numpy as np
import tabulate

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Type

from easydiffraction.utils.decorators import enforce_type
from easydiffraction.experiments.components.experiment_type import ExperimentType
from easydiffraction.experiments.components.instrument import (
    InstrumentBase,
    InstrumentFactory
)
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
                 type: ExperimentType) -> None:
        super().__init__()
        self._name: str = name
        self.type: ExperimentType = type
        self.instrument = InstrumentFactory.create(
            beam_mode=self.type.beam_mode.value)
        self.datastore = DatastoreFactory.create(
            sample_form=self.type.sample_form.value,
            experiment=self)

    # ---------------------------
    # Name (ID) of the experiment
    # ---------------------------

    @property
    def name(self):
        return self._name

    @name.setter
    @enforce_type
    def name(self, new_name: str):
        self._name = new_name

    # ---------------
    # Experiment type
    # ---------------

    @property
    def type(self):
        return self._type

    @type.setter
    @enforce_type
    def type(self, new_experiment_type: ExperimentType):
        self._type = new_experiment_type

    # ----------
    # Instrument
    # ----------

    @property
    def instrument(self):
        return self._instrument

    @instrument.setter
    @enforce_type
    def instrument(self, new_instrument: InstrumentBase):
        self._instrument = new_instrument

    # ----------------
    # Misc. Need to be sorted
    # ----------------

    def as_cif(self, max_points: Optional[int] = None) -> str:
        """
        Export the sample model to CIF format.
        Returns:
            str: CIF string representation of the experiment.
        """
        # Data block header
        cif_lines: List[str] = [f"data_{self.name}"]

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

    def show_as_cif(self) -> None:
        cif_text: str = self.as_cif(max_points=5)
        lines: List[str] = cif_text.splitlines()
        max_width: int = max(len(line) for line in lines)
        padded_lines: List[str] = [f"│ {line.ljust(max_width)} │" for line in lines]
        top: str = f"╒{'═' * (max_width + 2)}╕"
        bottom: str = f"╘{'═' * (max_width + 2)}╛"

        print(paragraph(f"Experiment 🔬 '{self.name}' as cif"))
        print(top)
        print("\n".join(padded_lines))
        print(bottom)

    @abstractmethod
    def _load_ascii_data_to_experiment(self, data_path: str) -> None:
        pass

    @abstractmethod
    def show_meas_chart(self, x_min: Optional[float] = None, x_max: Optional[float] = None) -> None:
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
                 type: ExperimentType) -> None:
        super().__init__(name=name,
                         type=type)
        self._background_type: str = DEFAULT_BACKGROUND_TYPE
        self._peak_profile_type: str = DEFAULT_PEAK_PROFILE_TYPE
        self.background = BackgroundFactory.create(
            background_type=self.background_type)
        self.peak = PeakFactory.create(
            beam_mode=self.type.beam_mode.value,
            profile_type=self.peak_profile_type)
        self.linked_phases = LinkedPhases()

    # -------------
    # Measured data
    # -------------

    def _load_ascii_data_to_experiment(self, data_path: str) -> None:
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
        x: np.ndarray = data[:, 0]
        y: np.ndarray = data[:, 1]
        sy: np.ndarray = data[:, 2] if data.shape[1] > 2 else np.sqrt(y)

        # Attach the data to the experiment's datastore
        self.datastore.pattern.x = x
        self.datastore.pattern.meas = y
        self.datastore.pattern.meas_su = sy

        print(paragraph("Data loaded successfully"))
        print(f"Experiment 🔬 '{self.name}'. Number of data points: {len(x)}")

    def show_meas_chart(self, x_min: Optional[float] = None, x_max: Optional[float] = None) -> None:
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
    # TODO: check new_type type
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
    # TODO: check new_peak type
    def peak(self, new_peak):
        self._peak = new_peak

    @property
    def peak_profile_type(self) -> str:
        return self._peak_profile_type

    @peak_profile_type.setter
    def peak_profile_type(self, new_type: str) -> None:
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

    def show_supported_peak_profile_types(self) -> None:
        header: List[str] = ["Peak profile type", "Description"]
        table_data: List[List[str]] = []

        for name, config in PeakFactory._supported[self.type.beam_mode.value].items():
            description: str = getattr(config, '_description', 'No description provided.')
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

    def show_current_peak_profile_type(self) -> None:
        print(paragraph("Current peak profile type"))
        print(self.peak_profile_type)

    # -------------
    # Linked phases
    # -------------

    @property
    def linked_phases(self):
        return self._linked_phases

    @linked_phases.setter
    @enforce_type
    def linked_phases(self, new_linked_phases: LinkedPhases):
        self._linked_phases = new_linked_phases


class SingleCrystalExperiment(BaseExperiment):
    """Single crystal experiment class with specific attributes."""

    def __init__(self,
                 name: str,
                 type: ExperimentType) -> None:
        super().__init__(name=name,
                         type=type)
        self.linked_crystal = None

    def show_meas_chart(self) -> None:
        print('Showing measured data chart is not implemented yet.')


class ExperimentFactory:
    """Creates Experiment instances with only relevant attributes."""
    _supported: Dict[str, Type[BaseExperiment]] = {
        "powder": PowderExperiment,
        "single crystal": SingleCrystalExperiment
    }

    @classmethod
    def create(cls,
               name: str,
               sample_form: str,
               beam_mode: str,
               radiation_probe: str) -> BaseExperiment:
        expt_type: ExperimentType = ExperimentType(sample_form=sample_form,
                                                   beam_mode=beam_mode,
                                                   radiation_probe=radiation_probe)
        expt_class: Type[BaseExperiment] = cls._supported[sample_form]
        instance: BaseExperiment = expt_class(name=name, type=expt_type)
        return instance


def Experiment(name: str,
               sample_form: str = DEFAULT_SAMPLE_FORM,
               beam_mode: str = DEFAULT_BEAM_MODE,
               radiation_probe: str = DEFAULT_RADIATION_PROBE,
               data_path: Optional[str] = None) -> BaseExperiment:
    experiment: BaseExperiment = ExperimentFactory.create(
        name=name,
        sample_form=sample_form,
        beam_mode=beam_mode,
        radiation_probe=radiation_probe
    )
    if data_path:
        experiment._load_ascii_data_to_experiment(data_path)
    return experiment
