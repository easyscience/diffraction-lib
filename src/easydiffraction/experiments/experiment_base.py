from abc import ABC, abstractmethod

from easydiffraction.experiments.components.expt_type import ExperimentType


class BaseExperiment(ABC):
    """
    Base class for all dynamically generated experiments.
    """

    def __init__(self,
                 id,
                 diffr_mode="powder",
                 expt_mode="constant_wavelength",
                 radiation_probe="neutron",
                 **kwargs):
        self.id = id
        self.expt_type = ExperimentType(diffr_mode=diffr_mode,
                                        expt_mode=expt_mode,
                                        radiation_probe=radiation_probe)
        super().__init__(**kwargs)

    def as_cif(self):
        """
        Generate CIF content (example placeholder)
        """
        return f"data_{self.id}\n# experiment CIF content here"

    @abstractmethod
    def show_meas_chart(self, x_min=None, x_max=None):
        """
        Abstract method to display data chart. Should be implemented in specific experiment mixins.
        """
        raise NotImplementedError("show_meas_chart() must be implemented in the subclass")