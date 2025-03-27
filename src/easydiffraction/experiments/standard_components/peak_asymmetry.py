from easydiffraction.core.parameter import Parameter
from easydiffraction.core.component_base import StandardComponentBase


class PeakAsymmBase(StandardComponentBase):
    """
    Base class for peak asymmetry component.
    Dynamically combined with experiment_mixins depending on expt_mode.
    """
    cif_category_name = "_peak_asymm"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class PeakAsymmConstWavelengthMixin:
    """
    <<mixin>> Adds constant wavelength peak asymmetry parameters.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.asy_1 = Parameter(
            value=0.0,
            cif_name="asy_1"
        )
        self.asy_2 = Parameter(
            value=0.0,
            cif_name="asy_2"
        )
        self.asy_3 = Parameter(
            value=0.0,
            cif_name="asy_3"
        )
        self.asy_4 = Parameter(
            value=0.0,
            cif_name="asy_4"
        )
        self.s_l = Parameter(
            value=0.0,
            cif_name="s_l"
        )
        self.d_l = Parameter(
            value=0.0,
            cif_name="d_l"
        )


class PeakAsymmTimeOfFlightMixin:
    """
    <<mixin>> Adds time-of-flight peak asymmetry parameters.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.alpha_0 = Parameter(
            value=0.0,
            cif_name="alpha_0"
        )
        self.alpha_1 = Parameter(
            value=0.0,
            cif_name="alpha_1"
        )
