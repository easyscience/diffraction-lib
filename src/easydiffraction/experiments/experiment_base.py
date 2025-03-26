from abc import ABC, abstractmethod

from easydiffraction.experiments.components.expt_type import ExperimentType
from easydiffraction.utils.utils import paragraph


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

    def as_cif(self, max_points=None):
        """
        Generate CIF content by collecting values from all components.
        """
        lines = [f"data_{self.id}"]

        # Experiment type
        lines.append("")
        lines.append(self.expt_type.as_cif())

        # Instrument setup and calibration
        if hasattr(self, "instr_setup"):
            lines.append("")
            lines.append(self.instr_setup.as_cif())
        if hasattr(self, "instr_calib"):
            lines.append(self.instr_calib.as_cif())

        # Peak profile, broadening and asymmetry
        if hasattr(self, "peak_profile"):
            lines.append("")
            lines.append(self.peak_profile.as_cif())
        if hasattr(self, "peak_broad"):
            lines.append(self.peak_broad.as_cif())
        if hasattr(self, "peak_asymm"):
            lines.append(self.peak_asymm.as_cif())

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

        # Measured data
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

        print(paragraph(f"Experiment 🔬 '{self.id}' as cif"))
        print(top)
        print("\n".join(padded_lines))
        print(bottom)

    @abstractmethod
    def show_meas_chart(self, x_min=None, x_max=None):
        """
        Abstract method to display data chart. Should be implemented in specific experiment mixins.
        """
        raise NotImplementedError("show_meas_chart() must be implemented in the subclass")