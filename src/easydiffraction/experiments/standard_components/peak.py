from easydiffraction.core.objects import (Descriptor,
                                          Parameter, Component)
from easydiffraction.core.constants import (DEFAULT_BEAM_MODE,
                                            DEFAULT_PEAK_PROFILE_TYPE)


# --- Mixins ---
class ConstantWavelengthBroadeningMixin:
    def _add_constant_wavelength_broadening(self):
        self.broad_gauss_u: Parameter = Parameter(
            value=0.01,
            cif_param_name="broad_gauss_u",
            units="deg²",
            description="Gaussian broadening coefficient (dependent on sample size and instrument resolution)"
        )
        self.broad_gauss_v: Parameter = Parameter(
            value=-0.01,
            cif_param_name="broad_gauss_v",
            units="deg²",
            description="Gaussian broadening coefficient (instrumental broadening contribution)"
        )
        self.broad_gauss_w: Parameter = Parameter(
            value=0.02,
            cif_param_name="broad_gauss_w",
            units="deg²",
            description="Gaussian broadening coefficient (instrumental broadening contribution)"
        )
        self.broad_lorentz_x: Parameter = Parameter(
            value=0.0,
            cif_param_name="broad_lorentz_x",
            units="deg",
            description="Lorentzian broadening coefficient (dependent on sample strain effects)"
        )
        self.broad_lorentz_y: Parameter = Parameter(
            value=0.0,
            cif_param_name="broad_lorentz_y",
            units="deg",
            description="Lorentzian broadening coefficient (dependent on microstructural defects and strain)"
        )


class TimeOfFlightBroadeningMixin:
    def _add_time_of_flight_broadening(self):
        self.broad_gauss_sigma_0: Parameter = Parameter(
            value=0.0,
            cif_param_name="gauss_sigma_0",
            units="µs²",
            description="Gaussian broadening coefficient (instrumental resolution)"
        )
        self.broad_gauss_sigma_1: Parameter = Parameter(
            value=0.0,
            cif_param_name="gauss_sigma_1",
            units="µs/Å",
            description="Gaussian broadening coefficient (dependent on d-spacing)"
        )
        self.broad_gauss_sigma_2: Parameter = Parameter(
            value=0.0,
            cif_param_name="gauss_sigma_2",
            units="µs²/Å²",
            description="Gaussian broadening coefficient (instrument-dependent term)"
        )
        self.broad_lorentz_gamma_0: Parameter = Parameter(
            value=0.0,
            cif_param_name="lorentz_gamma_0",
            units="µs",
            description="Lorentzian broadening coefficient (dependent on microstrain effects)"
        )
        self.broad_lorentz_gamma_1: Parameter = Parameter(
            value=0.0,
            cif_param_name="lorentz_gamma_1",
            units="µs/Å",
            description="Lorentzian broadening coefficient (dependent on d-spacing)"
        )
        self.broad_lorentz_gamma_2: Parameter = Parameter(
            value=0.0,
            cif_param_name="lorentz_gamma_2",
            units="µs²/Å²",
            description="Lorentzian broadening coefficient (instrumental-dependent term)"
        )
        self.broad_mix_beta_0: Parameter = Parameter(
            value=0.0,
            cif_param_name="mix_beta_0",
            units="deg",
            description="Mixing parameter. Defines the ratio of Gaussian to Lorentzian contributions in TOF profiles"
        )
        self.broad_mix_beta_1: Parameter = Parameter(
            value=0.0,
            cif_param_name="mix_beta_1",
            units="deg",
            description="Mixing parameter. Defines the ratio of Gaussian to Lorentzian contributions in TOF profiles"
        )


class EmpiricalAsymmetryMixin:
    def _add_empirical_asymmetry(self):
        self.asym_empir_1: Parameter = Parameter(
            value=0.1,
            cif_param_name="asym_empir_1",
            units="",
            description="Empirical asymmetry coefficient p1"
        )
        self.asym_empir_2: Parameter = Parameter(
            value=0.2,
            cif_param_name="asym_empir_2",
            units="",
            description="Empirical asymmetry coefficient p2"
        )
        self.asym_empir_3: Parameter = Parameter(
            value=0.3,
            cif_param_name="asym_empir_3",
            units="",
            description="Empirical asymmetry coefficient p3"
        )
        self.asym_empir_4: Parameter = Parameter(
            value=0.4,
            cif_param_name="asym_empir_4",
            units="",
            description="Empirical asymmetry coefficient p4"
        )


class FcjAsymmetryMixin:
    def _add_fcj_asymmetry(self):
        self.asym_fcj_1: Parameter = Parameter(
            value=0.01,
            cif_param_name="asym_fcj_1",
            units="",
            description="FCJ asymmetry coefficient 1"
        )
        self.asym_fcj_2: Parameter = Parameter(
            value=0.02,
            cif_param_name="asym_fcj_2",
            units="",
            description="FCJ asymmetry coefficient 2"
        )


class IkedaCarpenterAsymmetryMixin:
    def _add_ikeda_carpenter_asymmetry(self):
        self.asym_alpha_0: Parameter = Parameter(
            value=0.01,
            cif_param_name="asym_alpha_0",
            units="",
            description="Ikeda-Carpenter asymmetry parameter α₀"
        )
        self.asym_alpha_1: Parameter = Parameter(
            value=0.02,
            cif_param_name="asym_alpha_1",
            units="",
            description="Ikeda-Carpenter asymmetry parameter α₁"
        )


# --- Base peak class ---
class PeakBase(Component):
    @property
    def cif_category_key(self):
        return "_peak"


# --- Derived peak classes ---
class ConstantWavelengthPseudoVoigt(PeakBase,
                                    ConstantWavelengthBroadeningMixin):
    _description = "Pseudo-Voigt profile"
    def __init__(self):
        super().__init__()
        self._add_constant_wavelength_broadening()
        self._locked = True  # Lock further attribute additions


class ConstantWavelengthSplitPseudoVoigt(PeakBase,
                                         ConstantWavelengthBroadeningMixin,
                                         EmpiricalAsymmetryMixin):
    _description = "Split pseudo-Voigt profile"
    def __init__(self):
        super().__init__()
        self._add_constant_wavelength_broadening()
        self._add_empirical_asymmetry()
        self._locked = True  # Lock further attribute additions


class ConstantWavelengthThompsonCoxHastings(PeakBase,
                                            ConstantWavelengthBroadeningMixin,
                                            FcjAsymmetryMixin):
    _description = "Thompson-Cox-Hastings profile"
    def __init__(self):
        super().__init__()
        self._add_constant_wavelength_broadening()
        self._add_fcj_asymmetry()
        self._locked = True  # Lock further attribute additions


class TimeOfFlightPseudoVoigt(PeakBase,
                              TimeOfFlightBroadeningMixin):
    _description = "Pseudo-Voigt profile"
    def __init__(self):
        super().__init__()
        self._add_time_of_flight_broadening()
        self._locked = True  # Lock further attribute additions


class TimeOfFlightIkedaCarpenter(PeakBase,
                                 TimeOfFlightBroadeningMixin,
                                 IkedaCarpenterAsymmetryMixin):
    _description = "Ikeda-Carpenter profile"
    def __init__(self):
        super().__init__()
        self._add_time_of_flight_broadening()
        self._add_ikeda_carpenter_asymmetry()
        self._locked = True  # Lock further attribute additions


class TimeOfFlightPseudoVoigtIkedaCarpenter(PeakBase,
                                            TimeOfFlightBroadeningMixin,
                                            IkedaCarpenterAsymmetryMixin):
    _description = "Pseudo-Voigt * Ikeda-Carpenter profile"
    def __init__(self):
        super().__init__()
        self._add_time_of_flight_broadening()
        self._add_ikeda_carpenter_asymmetry()
        self._locked = True  # Lock further attribute additions


class TimeOfFlightPseudoVoigtBackToBackExponential(PeakBase,
                                                   TimeOfFlightBroadeningMixin,
                                                   IkedaCarpenterAsymmetryMixin):
    _description = "Pseudo-Voigt * Back-to-Back Exponential profile"
    def __init__(self):
        super().__init__()
        self._add_time_of_flight_broadening()
        self._add_ikeda_carpenter_asymmetry()
        self._locked = True  # Lock further attribute additions


# --- Peak factory ---
class PeakFactory:
    _supported = {
        "constant wavelength": {
            "pseudo-voigt": ConstantWavelengthPseudoVoigt,
            "split pseudo-voigt": ConstantWavelengthSplitPseudoVoigt,
            "thompson-cox-hastings": ConstantWavelengthThompsonCoxHastings
        },
        "time-of-flight": {
            "pseudo-voigt": TimeOfFlightPseudoVoigt,
            "ikeda-carpenter": TimeOfFlightIkedaCarpenter,
            "pseudo-voigt * ikeda-carpenter": TimeOfFlightPseudoVoigtIkedaCarpenter,
            "pseudo-voigt * back-to-back": TimeOfFlightPseudoVoigtBackToBackExponential
        }
    }

    @classmethod
    def create(cls,
               beam_mode=DEFAULT_BEAM_MODE,
               profile_type=DEFAULT_PEAK_PROFILE_TYPE):
        if beam_mode not in cls._supported:
            supported_beam_modes = list(cls._supported.keys())

            raise ValueError(
                f"Unsupported beam mode: '{beam_mode}'.\n "
                f"Supported beam modes are: {supported_beam_modes}"
            )

        supported_types = cls._supported[beam_mode]

        if profile_type is not None and profile_type not in supported_types:
            raise ValueError(
                f"Unsupported profile type '{profile_type}' for mode '{beam_mode}'.\n"
                f"Supported profiles are: {list(supported_types.keys())}"
            )

        peak_class = cls._supported[beam_mode][profile_type]
        return peak_class()