from easydiffraction.core.parameter import Parameter
from easydiffraction.experiments.standard_components.standard_component_base import StandardComponentBase


class InstrCalibBase(StandardComponentBase):
    """
    Base class for instrument calibration.
    Dynamically combined with experiment_mixins depending on expt_mode.
    """
    cif_category_name = "_instr_calib"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class InstrCalibConstWavelengthMixin:
    """
    <<mixin>> Adds constant wavelength calibration parameters.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.twotheta_offset = Parameter(
            value=0,
            units="degree",
            cif_name="twotheta_offset"
        )

class InstrCalibTimeOfFlightMixin:
    """
    <<mixin>> Adds time-of-flight calibration parameters.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.d_to_tof_offset = Parameter(
            value=0,
            units="µs",
            cif_name="d_to_tof_offset"
        )
        self.d_to_tof_linear = Parameter(
            value=0,
            units="µs/Å",
            cif_name="d_to_tof_linear"
        )
        self.d_to_tof_quad = Parameter(
            value=0,
            units="µs/Å²",
            cif_name="d_to_tof_quad"
        )
        self.d_to_tof_recip = Parameter(
            value=0,
            units="µs·Å",
            cif_name="d_to_tof_recip"
        )
