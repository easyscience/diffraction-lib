import numpy as np
import tabulate

from abc import abstractmethod

from easydiffraction.experiments.components.experiment_type import ExperimentType
from easydiffraction.experiments.components.instrument import InstrumentFactory
from easydiffraction.experiments.components.peak import PeakFactory

from easydiffraction.experiments.collections.linked_phases import LinkedPhases
from easydiffraction.experiments.collections.background import BackgroundFactory
from easydiffraction.experiments.collections.datastore import DatastoreFactory

from easydiffraction.utils.formatting import paragraph, warning

from easydiffraction.core.objects import Datablock
from easydiffraction.core.constants import (
    DEFAULT_SAMPLE_FORM,
    DEFAULT_BEAM_MODE,
    DEFAULT_RADIATION_PROBE,
    DEFAULT_PEAK_PROFILE_TYPE,
    DEFAULT_BACKGROUND_TYPE,
    DEFAULT_DIFFRACTION_TYPE
)


class BaseExperiment(Datablock):
    """Base class for all experiments with only core attributes."""

    def __init__(self,
                 name: str,
                 type: ExperimentType):
        self.name = name
        self.type = type
        self.instrument = InstrumentFactory.create(beam_mode=self.type.beam_mode.value,
                                                   diffraction_type=self.type.diffraction_type.value)
        self.datastore = DatastoreFactory.create(sample_form=self.type.sample_form.value,
                                                 experiment=self)

    def as_cif(self, max_points=None):
        """
        Generate CIF content by collecting values from all components.
        """
        lines = [f"data_{self.name}"]

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
        # TODO: This functionality should be moved to datastore.py
        # TODO: We need meas_data component which will use datastore to extract data
        # TODO: Datastore should be moved out of collections/
        if hasattr(self, "datastore") and hasattr(self.datastore, "pattern"):
            lines.append("")
            lines.append("loop_")
            category = '_pd_meas'  # TODO: Add category to pattern component
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


class PowderExperiment(BaseExperiment):
    """Powder experiment class with specific attributes."""

    def __init__(self,
                 name: str,
                 type: ExperimentType):
        super().__init__(name=name,
                         type=type)
        self._peak_profile_type = DEFAULT_PEAK_PROFILE_TYPE
        self._background_type = DEFAULT_BACKGROUND_TYPE
        self.peak = PeakFactory.create(beam_mode=self.type.beam_mode.value)
        self.linked_phases = LinkedPhases()
        self.background = BackgroundFactory.create()

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
        self.peak = PeakFactory.create(beam_mode=self.type.beam_mode.value,
                                       profile_type=new_type)
        self._peak_profile_type = new_type
        print(paragraph(f"Peak profile type for experiment '{self.name}' changed to"))
        print(new_type)

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
        self.background = BackgroundFactory.create(new_type)
        self._background_type = new_type
        print(paragraph(f"Background type for experiment '{self.name}' changed to"))
        print(new_type)

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

class PDFExperiment(BaseExperiment):
    """PDF experiment class with specific attributes."""

    def __init__(self,
                 name: str,
                 type: ExperimentType):
        super().__init__(name=name,
                         type=type)

        self._background_type = DEFAULT_BACKGROUND_TYPE
        self.linked_phases = LinkedPhases()
        self.background = BackgroundFactory.create()

    def _load_ascii_data_to_experiment(self, data_path):
        """
        Loads x, y, sy values from an ASCII data file into the experiment.

        The file must be structured as:
            x  y  sy
        """
        try:
            from diffpy.utils.parsers.loaddata import loadData
        except ImportError:
            raise ImportError("diffpy module not found.")
        try:
            data = loadData(data_path)
        except Exception as e:
            raise IOError(f"Failed to read data from {data_path}: {e}")

        if data.shape[1] < 2:
            raise ValueError("Data file must have at least two columns: x and y.")

        if data.shape[1] < 3:
            print("Warning: No uncertainty (sy) column provided. Defaulting to sqrt(y).")

        # Extract x, y, and sy data
        x = data[:, 0]
        y = data[:, 1]
        sy = data[:, 3] if data.shape[1] > 2 else np.sqrt(y)

        # Attach the data to the experiment's datastore
        self.datastore.pattern.x = x
        self.datastore.pattern.meas = y
        self.datastore.pattern.meas_su = sy

        print(paragraph("Data loaded successfully"))
        print(f"Experiment 🔬 '{self.name}'. Number of data points: {len(x)}")

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
        self.background = BackgroundFactory.create(new_type)
        self._background_type = new_type
        print(paragraph(f"Background type for experiment '{self.name}' changed to"))
        print(new_type)

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

class ExperimentFactory:
    """Creates Experiment instances with only relevant attributes."""

    _supported = {
    "powder": {
        "conventional": PowderExperiment,
        "total": PDFExperiment,
    },
    "single crystal": {
        "conventional": SingleCrystalExperiment,
        "total": PDFExperiment,}
    }
    @classmethod
    def create(cls,
               name: str,
               sample_form: DEFAULT_SAMPLE_FORM,
               beam_mode: DEFAULT_BEAM_MODE,
               radiation_probe: DEFAULT_RADIATION_PROBE,
               diffraction_type: DEFAULT_DIFFRACTION_TYPE,
               ) -> BaseExperiment:
        # TODO: Add checks for expt_type and expt_class
        expt_type = ExperimentType(sample_form=sample_form,
                                   beam_mode=beam_mode,
                                   radiation_probe=radiation_probe,
                                   diffraction_type=diffraction_type)

        expt_class = cls._supported[sample_form][diffraction_type]
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
               diffraction_type: str = DEFAULT_DIFFRACTION_TYPE,
               data_path: str = None):
    experiment = ExperimentFactory.create(
        name=name,
        sample_form=sample_form,
        beam_mode=beam_mode,
        radiation_probe=radiation_probe,
        diffraction_type=diffraction_type
    )
    experiment._load_ascii_data_to_experiment(data_path)
    return experiment
