from easydiffraction.parameter import Parameter, Descriptor
from easydiffraction.experiments.components.base import ComponentBase


class PeakProfileBase(ComponentBase):
    """
    Base class for peak profile.
    Dynamically combined with mixins depending on expt_mode.
    """
    cif_category_name = "_peak_profile"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class PeakProfileConstWavelengthMixin:
    """
    <<mixin>> Adds peak profile behavior for constant wavelength experiments.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.profile_type = Descriptor(
            value="Pseudo-Voigt",
            cif_name="function_type"
        )


class PeakProfileTimeOfFlightMixin:
    """
    <<mixin>> Adds peak profile behavior for time-of-flight experiments.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.profile_type = Parameter(
            value="Pseudo-Voigt",
            cif_name="function_type"
        )
