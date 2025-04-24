import numpy as np
import tabulate

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Type

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
    """Base class for all experiments with only core attributes."""

    def __init__(self,
                 name: str,
                 type: ExperimentType) -> None:
        self.name: str = name
        self.type: ExperimentType = type
        self.instrument = InstrumentFactory.create(beam_mode=self.type.beam_mode.value)
        self.datastore = DatastoreFactory.create(sample_form=self.type.sample_form.value,
                                                 experiment=self)

    def as_cif(self, max_points: Optional[int] = None) -> str:
        """
        Generate CIF content by collecting values from all components.
        """
        lines: List[str] = [f"data_{self.name}"]

        # Experiment type
        if hasattr(self, "type"):
            lines.append("")
            lines.append(self.type.as_cif())

        # Instrument setup and calibration
        if hasattr(self, "instrument"):
            lines.append("")
            lines.append(self.instrument.as_cif())

        # Peak profile, broadening and asymmetry
        if hasattr(self, "peak"):
            lines.append("")
            lines.append(self.peak.as_cif())

        # Phase scale factors for powder experiments
        if hasattr(self, "linked_phases"):
            lines.append("")
            lines.append(self.linked_phases.as_cif())

        # Crystal scale factor for single crystal experiments
        if hasattr(self, "linked_crystal"):
            lines.append("")
            lines.append(self.linked_crystal.as_cif())

        # Background points
        if hasattr(self, "background") and self.background:
            lines.append("")
            lines.append(self.background.as_cif())

        # Measured data
        if hasattr(self, "datastore") and hasattr(self.datastore, "pattern"):
            lines.append("")
            lines.append("loop_")
            category = '_pd_meas'
            attributes = ('2theta_scan', 'intensity_total', 'intensity_total_su')
            for attribute in attributes:
                lines.append(f"{category}.{attribute}")
            pattern = self.datastore.pattern
            if max_points is not None and len(pattern.x) > 2 * max_points:
                for i in range(max_points):
                    x = pattern.x[i]
                    meas = pattern.meas[i]
                    meas_su = pattern.meas_su[i]
                    lines.append(f"{x} {meas} {meas_su}")
                lines.append("...")
                for i in range(-max_points, 0):
                    x = pattern.x[i]
                    meas = pattern.meas[i]
                    meas_su = pattern.meas_su[i]
                    lines.append(f"{x} {meas} {meas_su}")
            else:
                for x, meas, meas_su in zip(pattern.x, pattern.meas, pattern.meas_su):
                    lines.append(f"{x} {meas} {meas_su}")

        return "\n".join(lines)

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
    """Powder experiment class with specific attributes."""

    def __init__(self,
                 name: str,
                 type: ExperimentType) -> None:
        super().__init__(name=name,
                         type=type)
        self._peak_profile_type: str = DEFAULT_PEAK_PROFILE_TYPE
        self._background_type: str = DEFAULT_BACKGROUND_TYPE
        self.peak = PeakFactory.create(beam_mode=self.type.beam_mode.value)
        self.linked_phases = LinkedPhases()
        self.background = BackgroundFactory.create()

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
        self.peak = PeakFactory.create(beam_mode=self.type.beam_mode.value,
                                       profile_type=new_type)
        self._peak_profile_type = new_type
        print(paragraph(f"Peak profile type for experiment '{self.name}' changed to"))
        print(new_type)

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

    @property
    def background_type(self) -> str:
        return self._background_type

    @background_type.setter
    def background_type(self, new_type: str) -> None:
        if new_type not in BackgroundFactory._supported:
            supported_types = list(BackgroundFactory._supported.keys())
            print(warning(f"Unknown background type '{new_type}'"))
            print(f'Supported background types: {supported_types}')
            print(f"For more information, use 'show_supported_background_types()'")
            return
        self.background = BackgroundFactory.create(new_type)
        self._background_type = new_type
        print(paragraph(f"Background type for experiment '{self.name}' changed to"))
        print(new_type)

    def show_supported_background_types(self) -> None:
        header: List[str] = ["Background type", "Description"]
        table_data: List[List[str]] = []

        for name, config in BackgroundFactory._supported.items():
            description: str = getattr(config, '_description', 'No description provided.')
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

    def show_current_background_type(self) -> None:
        print(paragraph("Current background type"))
        print(self.background_type)


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
