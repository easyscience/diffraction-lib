from easydiffraction.core.parameter import Parameter
from easydiffraction.experiments.standard_components.standard_component_base import StandardComponentBase


class PeakBroadBase(StandardComponentBase):
    """
    Base class for peak broadening component.
    Dynamically combined with experiment_mixins depending on expt_mode.
    """
    cif_category_name = "_peak_broad"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class PeakBroadConstWavelengthMixin:
    """
    <<mixin>> Adds constant wavelength peak broadening parameters.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gauss_u = Parameter(
            value=0.0,
            cif_name="gauss_u"
        )
        self.gauss_v = Parameter(
            value=0.0,
            cif_name="gauss_v"
        )
        self.gauss_w = Parameter(
            value=0.0,
            cif_name="gauss_w"
        )
        self.lorentz_x = Parameter(
            value=0.0,
            cif_name="lorentz_x"
        )
        self.lorentz_y = Parameter(
            value=0.0,
            cif_name="lorentz_y"
        )
        self.mix_eta = Parameter(
            value=0.0,
            cif_name="mix_eta"
        )

class PeakBroadTimeOfFlightMixin:
    """
    <<mixin>> Adds time-of-flight peak broadening parameters.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gauss_sigma_0 = Parameter(
            value=0.0,
            cif_name="gauss_sigma_0"
        )
        self.gauss_sigma_1 = Parameter(
            value=0.0,
            cif_name="gauss_sigma_1"
        )
        self.gauss_sigma_2 = Parameter(
            value=0.0,
            cif_name="gauss_sigma_2"
        )
        self.lorentz_gamma_0 = Parameter(
            value=0.0,
            cif_name="lorentz_gamma_0"
        )
        self.lorentz_gamma_1 = Parameter(
            value=0.0,
            cif_name="lorentz_gamma_1"
        )
        self.lorentz_gamma_2 = Parameter(
            value=0.0,
            cif_name="lorentz_gamma_2"
        )
        self.mix_beta_0 = Parameter(
            value=0.0,
            cif_name="mix_beta_0"
        )
        self.mix_beta_1 = Parameter(
            value=0.0,
            cif_name="mix_beta_1"
        )
