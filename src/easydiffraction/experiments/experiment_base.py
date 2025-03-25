from abc import ABC, abstractmethod
from unicodedata import category

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
        Generate CIF content by collecting values from all components.
        """
        lines = [f"data_{self.id}"]

        # Experiment type
        lines.append("")
        lines.append(f"{self.expt_type.cif_category_name}.diffr_mode {self.expt_type.diffr_mode}")
        lines.append(f"{self.expt_type.cif_category_name}.expt_mode {self.expt_type.expt_mode}")
        lines.append(f"{self.expt_type.cif_category_name}.radiation_probe {self.expt_type.radiation_probe}")

        # Instrument setup
        if hasattr(self, "instr_setup"):
            lines.append("")
            if hasattr(self.instr_setup, "wavelength"):
                lines.append(f"{self.instr_setup.cif_category_name}.wavelength {self.instr_setup.wavelength}")

        # Instrument calibration
        if hasattr(self, "instr_calib"):
            lines.append("")
            if hasattr(self.instr_calib, "twotheta_offset"):
                lines.append(f"{self.instr_calib.cif_category_name}.twotheta_offset {self.instr_calib.twotheta_offset}")

        # Peak profile
        if hasattr(self, "peak_profile"):
            lines.append("")
            if hasattr(self.peak_profile, "profile_type"):
                lines.append(f"{self.peak_profile.cif_category_name}.profile_type {self.peak_profile.profile_type}")

        # Peak broadening
        if hasattr(self, "peak_broad"):
            lines.append("")
            if hasattr(self.peak_broad, "gauss_u"):
                lines.append(f"{self.peak_broad.cif_category_name}.gauss_u {self.peak_broad.gauss_u}")
            if hasattr(self.peak_broad, "gauss_v"):
                lines.append(f"{self.peak_broad.cif_category_name}.gauss_v {self.peak_broad.gauss_v}")
            if hasattr(self.peak_broad, "gauss_w"):
                lines.append(f"{self.peak_broad.cif_category_name}.gauss_w {self.peak_broad.gauss_w}")
            if hasattr(self.peak_broad, "lorentz_x"):
                lines.append(f"{self.peak_broad.cif_category_name}.lorentz_x {self.peak_broad.lorentz_x}")
            if hasattr(self.peak_broad, "lorentz_y"):
                lines.append(f"{self.peak_broad.cif_category_name}.lorentz_y {self.peak_broad.lorentz_y}")

        # Phase scale factors
        if hasattr(self, "linked_phases") and self.linked_phases:
            lines.append("")
            lines.append("loop_")
            category = self.linked_phases.phases[0].cif_category_name
            attributes = ('id', 'scale')
            for attribute in attributes:
                lines.append(f"{category}.{attribute}")
            for phase in self.linked_phases.phases:
                lines.append(f"{phase.id} {phase.scale}")

        # Background points
        if hasattr(self, "background") and hasattr(self.background, "points") and self.background.points:
            lines.append("")
            lines.append("loop_")
            category = '_pd_background'  # TODO: Add category to background component
            attributes = ('line_segment_X', 'line_segment_intensity')
            for attribute in attributes:
                lines.append(f"{category}.{attribute}")
            for point in self.background.points:
                x = point[0]
                y = point[1]
                lines.append(f"{x} {y}")

        return "\n".join(lines)

    @abstractmethod
    def show_meas_chart(self, x_min=None, x_max=None):
        """
        Abstract method to display data chart. Should be implemented in specific experiment mixins.
        """
        raise NotImplementedError("show_meas_chart() must be implemented in the subclass")