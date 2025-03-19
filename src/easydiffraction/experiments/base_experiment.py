from abc import ABC, abstractmethod


class BaseExperiment(ABC):
    """
    Base class for all dynamically generated experiments.
    """

    def __init__(self, id, diffr_mode, expt_mode, radiation_probe, **kwargs):
        self.id = id
        self.diffr_mode = diffr_mode
        self.expt_mode = expt_mode
        self.radiation_probe = radiation_probe
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