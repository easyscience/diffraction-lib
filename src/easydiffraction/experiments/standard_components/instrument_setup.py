from easydiffraction.core.parameter import Parameter
from easydiffraction.experiments.standard_components.standard_component_base import StandardComponentBase


class InstrSetupBase(StandardComponentBase):
    """
    Base class for instrument setup.
    Dynamically combined with experiment_mixins depending on expt_mode.
    """
    cif_category_name = "_instr_setup"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class InstrSetupConstWavelengthMixin:
    """
    Mixin for constant wavelength instrument setup.
    Adds wavelength as a parameter.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wavelength = Parameter(
            value=1.5406,
            units="Å",
            cif_name="wavelength"
        )


class InstrSetupTimeOfFlightMixin:
    """
    Mixin for time-of-flight instrument setup.
    Adds twotheta_bank as a parameter.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.twotheta_bank = Parameter(
            value=144.845,
            units="degree",
            cif_name="2theta_bank"
        )
