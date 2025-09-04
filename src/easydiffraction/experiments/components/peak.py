# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction Python Library contributors <https://github.com/easyscience/diffraction-lib>
# SPDX-License-Identifier: BSD-3-Clause
from enum import Enum

from easydiffraction.core.objects import Component
from easydiffraction.core.objects import Parameter
from easydiffraction.experiments.components.experiment_type import BeamModeEnum
from easydiffraction.experiments.components.experiment_type import ScatteringTypeEnum


class PeakProfileTypeEnum(str, Enum):
    PSEUDO_VOIGT = 'pseudo-voigt'
    SPLIT_PSEUDO_VOIGT = 'split pseudo-voigt'
    THOMPSON_COX_HASTINGS = 'thompson-cox-hastings'
    PSEUDO_VOIGT_IKEDA_CARPENTER = 'pseudo-voigt * ikeda-carpenter'
    PSEUDO_VOIGT_BACK_TO_BACK = 'pseudo-voigt * back-to-back'
    GAUSSIAN_DAMPED_SINC = 'gaussian-damped-sinc'

    @classmethod
    def default(
        cls,
        scattering_type: ScatteringTypeEnum | None = None,
        beam_mode: BeamModeEnum | None = None,
    ) -> 'PeakProfileTypeEnum':
        if scattering_type is None:
            scattering_type = ScatteringTypeEnum.default()
        if beam_mode is None:
            beam_mode = BeamModeEnum.default()

        return {
            (ScatteringTypeEnum.BRAGG, BeamModeEnum.CONSTANT_WAVELENGTH): cls.PSEUDO_VOIGT,
            (ScatteringTypeEnum.BRAGG, BeamModeEnum.TIME_OF_FLIGHT): cls.PSEUDO_VOIGT_IKEDA_CARPENTER,
            (ScatteringTypeEnum.TOTAL, BeamModeEnum.CONSTANT_WAVELENGTH): cls.GAUSSIAN_DAMPED_SINC,
            (ScatteringTypeEnum.TOTAL, BeamModeEnum.TIME_OF_FLIGHT): cls.GAUSSIAN_DAMPED_SINC,
        }[(scattering_type, beam_mode)]

    def description(self) -> str:
        if self is PeakProfileTypeEnum.PSEUDO_VOIGT:
            return 'Pseudo-Voigt profile'
        elif self is PeakProfileTypeEnum.SPLIT_PSEUDO_VOIGT:
            return 'Split pseudo-Voigt profile with empirical asymmetry correction.'
        elif self is PeakProfileTypeEnum.THOMPSON_COX_HASTINGS:
            return 'Thompson-Cox-Hastings profile with FCJ asymmetry correction.'
        elif self is PeakProfileTypeEnum.PSEUDO_VOIGT_IKEDA_CARPENTER:
            return 'Pseudo-Voigt profile with Ikeda-Carpenter asymmetry correction.'
        elif self is PeakProfileTypeEnum.PSEUDO_VOIGT_BACK_TO_BACK:
            return 'Pseudo-Voigt profile with Back-to-Back Exponential asymmetry correction.'
        elif self is PeakProfileTypeEnum.GAUSSIAN_DAMPED_SINC:
            return 'Gaussian-damped sinc profile for pair distribution function (PDF) analysis.'


# --- Mixins ---
class ConstantWavelengthBroadeningMixin:
    def _add_constant_wavelength_broadening(self) -> None:
        self.broad_gauss_u: Parameter = Parameter(
            value=0.01,
            name='broad_gauss_u',
            cif_name='broad_gauss_u',
            units='deg²',
            description='Gaussian broadening coefficient (dependent on sample size and instrument resolution)',
        )
        self.broad_gauss_v: Parameter = Parameter(
            value=-0.01,
            name='broad_gauss_v',
            cif_name='broad_gauss_v',
            units='deg²',
            description='Gaussian broadening coefficient (instrumental broadening contribution)',
        )
        self.broad_gauss_w: Parameter = Parameter(
            value=0.02,
            name='broad_gauss_w',
            cif_name='broad_gauss_w',
            units='deg²',
            description='Gaussian broadening coefficient (instrumental broadening contribution)',
        )
        self.broad_lorentz_x: Parameter = Parameter(
            value=0.0,
            name='broad_lorentz_x',
            cif_name='broad_lorentz_x',
            units='deg',
            description='Lorentzian broadening coefficient (dependent on sample strain effects)',
        )
        self.broad_lorentz_y: Parameter = Parameter(
            value=0.0,
            name='broad_lorentz_y',
            cif_name='broad_lorentz_y',
            units='deg',
            description='Lorentzian broadening coefficient (dependent on microstructural defects and strain)',
        )


class TimeOfFlightBroadeningMixin:
    def _add_time_of_flight_broadening(self) -> None:
        self.broad_gauss_sigma_0: Parameter = Parameter(
            value=0.0,
            name='gauss_sigma_0',
            cif_name='gauss_sigma_0',
            units='µs²',
            description='Gaussian broadening coefficient (instrumental resolution)',
        )
        self.broad_gauss_sigma_1: Parameter = Parameter(
            value=0.0,
            name='gauss_sigma_1',
            cif_name='gauss_sigma_1',
            units='µs/Å',
            description='Gaussian broadening coefficient (dependent on d-spacing)',
        )
        self.broad_gauss_sigma_2: Parameter = Parameter(
            value=0.0,
            name='gauss_sigma_2',
            cif_name='gauss_sigma_2',
            units='µs²/Å²',
            description='Gaussian broadening coefficient (instrument-dependent term)',
        )
        self.broad_lorentz_gamma_0: Parameter = Parameter(
            value=0.0,
            name='lorentz_gamma_0',
            cif_name='lorentz_gamma_0',
            units='µs',
            description='Lorentzian broadening coefficient (dependent on microstrain effects)',
        )
        self.broad_lorentz_gamma_1: Parameter = Parameter(
            value=0.0,
            name='lorentz_gamma_1',
            cif_name='lorentz_gamma_1',
            units='µs/Å',
            description='Lorentzian broadening coefficient (dependent on d-spacing)',
        )
        self.broad_lorentz_gamma_2: Parameter = Parameter(
            value=0.0,
            name='lorentz_gamma_2',
            cif_name='lorentz_gamma_2',
            units='µs²/Å²',
            description='Lorentzian broadening coefficient (instrumental-dependent term)',
        )
        self.broad_mix_beta_0: Parameter = Parameter(
            value=0.0,
            name='mix_beta_0',
            cif_name='mix_beta_0',
            units='deg',
            description='Mixing parameter. Defines the ratio of Gaussian to Lorentzian contributions in TOF profiles',
        )
        self.broad_mix_beta_1: Parameter = Parameter(
            value=0.0,
            name='mix_beta_1',
            cif_name='mix_beta_1',
            units='deg',
            description='Mixing parameter. Defines the ratio of Gaussian to Lorentzian contributions in TOF profiles',
        )


class EmpiricalAsymmetryMixin:
    def _add_empirical_asymmetry(self) -> None:
        self.asym_empir_1: Parameter = Parameter(
            value=0.1,
            name='asym_empir_1',
            cif_name='asym_empir_1',
            units='',
            description='Empirical asymmetry coefficient p1',
        )
        self.asym_empir_2: Parameter = Parameter(
            value=0.2,
            name='asym_empir_2',
            cif_name='asym_empir_2',
            units='',
            description='Empirical asymmetry coefficient p2',
        )
        self.asym_empir_3: Parameter = Parameter(
            value=0.3,
            name='asym_empir_3',
            cif_name='asym_empir_3',
            units='',
            description='Empirical asymmetry coefficient p3',
        )
        self.asym_empir_4: Parameter = Parameter(
            value=0.4,
            name='asym_empir_4',
            cif_name='asym_empir_4',
            units='',
            description='Empirical asymmetry coefficient p4',
        )


class FcjAsymmetryMixin:
    def _add_fcj_asymmetry(self) -> None:
        self.asym_fcj_1: Parameter = Parameter(
            value=0.01,
            name='asym_fcj_1',
            cif_name='asym_fcj_1',
            units='',
            description='FCJ asymmetry coefficient 1',
        )
        self.asym_fcj_2: Parameter = Parameter(
            value=0.02,
            name='asym_fcj_2',
            cif_name='asym_fcj_2',
            units='',
            description='FCJ asymmetry coefficient 2',
        )


class IkedaCarpenterAsymmetryMixin:
    def _add_ikeda_carpenter_asymmetry(self) -> None:
        self.asym_alpha_0: Parameter = Parameter(
            value=0.01,
            name='asym_alpha_0',
            cif_name='asym_alpha_0',
            units='',
            description='Ikeda-Carpenter asymmetry parameter α₀',
        )
        self.asym_alpha_1: Parameter = Parameter(
            value=0.02,
            name='asym_alpha_1',
            cif_name='asym_alpha_1',
            units='',
            description='Ikeda-Carpenter asymmetry parameter α₁',
        )


class PairDistributionFunctionBroadeningMixin:
    def _add_pair_distribution_function_broadening(self):
        self.damp_q = Parameter(
            value=0.05,
            name='damp_q',
            cif_name='damp_q',
            units='Å⁻¹',
            description='Instrumental Q-resolution damping factor (affects high-r PDF peak amplitude)',
        )
        self.broad_q = Parameter(
            value=0.0,
            name='broad_q',
            cif_name='broad_q',
            units='Å⁻²',
            description='Quadratic PDF peak broadening coefficient (thermal and model uncertainty contribution)',
        )
        self.cutoff_q = Parameter(
            value=25.0,
            name='cutoff_q',
            cif_name='cutoff_q',
            units='Å⁻¹',
            description='Q-value cutoff applied to model PDF for Fourier transform (controls real-space resolution)',
        )
        self.sharp_delta_1 = Parameter(
            value=0.0,
            name='sharp_delta_1',
            cif_name='sharp_delta_1',
            units='Å',
            description='PDF peak sharpening coefficient (1/r dependence)',
        )
        self.sharp_delta_2 = Parameter(
            value=0.0,
            name='sharp_delta_2',
            cif_name='sharp_delta_2',
            units='Å²',
            description='PDF peak sharpening coefficient (1/r² dependence)',
        )
        self.damp_particle_diameter = Parameter(
            value=0.0,
            name='damp_particle_diameter',
            cif_name='damp_particle_diameter',
            units='Å',
            description='Particle diameter for spherical envelope damping correction in PDF',
        )


# --- Base peak class ---
class PeakBase(Component):
    @property
    def category_key(self) -> str:
        return 'peak'

    @property
    def cif_category_key(self) -> str:
        return 'peak'


# --- Derived peak classes ---
class ConstantWavelengthPseudoVoigt(
    PeakBase,
    ConstantWavelengthBroadeningMixin,
):
    def __init__(self) -> None:
        super().__init__()

        self._add_constant_wavelength_broadening()

        # Lock further attribute additions to prevent
        # accidental modifications by users
        self._locked: bool = True


class ConstantWavelengthSplitPseudoVoigt(
    PeakBase,
    ConstantWavelengthBroadeningMixin,
    EmpiricalAsymmetryMixin,
):
    def __init__(self) -> None:
        super().__init__()

        self._add_constant_wavelength_broadening()
        self._add_empirical_asymmetry()

        # Lock further attribute additions to prevent
        # accidental modifications by users
        self._locked: bool = True


class ConstantWavelengthThompsonCoxHastings(
    PeakBase,
    ConstantWavelengthBroadeningMixin,
    FcjAsymmetryMixin,
):
    def __init__(self) -> None:
        super().__init__()

        self._add_constant_wavelength_broadening()
        self._add_fcj_asymmetry()

        # Lock further attribute additions to prevent
        # accidental modifications by users
        self._locked: bool = True


class TimeOfFlightPseudoVoigt(
    PeakBase,
    TimeOfFlightBroadeningMixin,
):
    def __init__(self) -> None:
        super().__init__()

        self._add_time_of_flight_broadening()

        # Lock further attribute additions to prevent
        # accidental modifications by users
        self._locked: bool = True


class TimeOfFlightPseudoVoigtIkedaCarpenter(
    PeakBase,
    TimeOfFlightBroadeningMixin,
    IkedaCarpenterAsymmetryMixin,
):
    def __init__(self) -> None:
        super().__init__()

        self._add_time_of_flight_broadening()
        self._add_ikeda_carpenter_asymmetry()

        # Lock further attribute additions to prevent
        # accidental modifications by users
        self._locked: bool = True


class TimeOfFlightPseudoVoigtBackToBackExponential(
    PeakBase,
    TimeOfFlightBroadeningMixin,
    IkedaCarpenterAsymmetryMixin,
):
    def __init__(self) -> None:
        super().__init__()

        self._add_time_of_flight_broadening()
        self._add_ikeda_carpenter_asymmetry()

        # Lock further attribute additions to prevent
        # accidental modifications by users
        self._locked: bool = True


class PairDistributionFunctionGaussianDampedSinc(
    PeakBase,
    PairDistributionFunctionBroadeningMixin,
):
    def __init__(self):
        super().__init__()
        self._add_pair_distribution_function_broadening()
        self._locked = True  # Lock further attribute additions


# --- Peak factory ---
class PeakFactory:
    _supported = {
        ScatteringTypeEnum.BRAGG: {
            BeamModeEnum.CONSTANT_WAVELENGTH: {
                PeakProfileTypeEnum.PSEUDO_VOIGT: ConstantWavelengthPseudoVoigt,
                PeakProfileTypeEnum.SPLIT_PSEUDO_VOIGT: ConstantWavelengthSplitPseudoVoigt,
                PeakProfileTypeEnum.THOMPSON_COX_HASTINGS: ConstantWavelengthThompsonCoxHastings,
            },
            BeamModeEnum.TIME_OF_FLIGHT: {
                PeakProfileTypeEnum.PSEUDO_VOIGT: TimeOfFlightPseudoVoigt,
                PeakProfileTypeEnum.PSEUDO_VOIGT_IKEDA_CARPENTER: TimeOfFlightPseudoVoigtIkedaCarpenter,
                PeakProfileTypeEnum.PSEUDO_VOIGT_BACK_TO_BACK: TimeOfFlightPseudoVoigtBackToBackExponential,
            },
        },
        ScatteringTypeEnum.TOTAL: {
            BeamModeEnum.CONSTANT_WAVELENGTH: {
                PeakProfileTypeEnum.GAUSSIAN_DAMPED_SINC: PairDistributionFunctionGaussianDampedSinc,
            },
            BeamModeEnum.TIME_OF_FLIGHT: {
                PeakProfileTypeEnum.GAUSSIAN_DAMPED_SINC: PairDistributionFunctionGaussianDampedSinc,
            },
        },
    }

    @classmethod
    def create(
        cls,
        scattering_type=ScatteringTypeEnum.default(),
        beam_mode=BeamModeEnum.default(),
        profile_type=PeakProfileTypeEnum.default(ScatteringTypeEnum.default(), BeamModeEnum.default()),
    ):
        supported_scattering_types = list(cls._supported.keys())
        if scattering_type not in supported_scattering_types:
            raise ValueError(
                f"Unsupported scattering type: '{scattering_type}'.\nSupported scattering types: {supported_scattering_types}"
            )

        supported_beam_modes = list(cls._supported[scattering_type].keys())
        if beam_mode not in supported_beam_modes:
            raise ValueError(
                f"Unsupported beam mode: '{beam_mode}' for scattering type: '{scattering_type}'.\n "
                f'Supported beam modes: {supported_beam_modes}'
            )

        supported_profile_types = list(cls._supported[scattering_type][beam_mode].keys())
        if profile_type not in supported_profile_types:
            raise ValueError(
                f"Unsupported profile type '{profile_type}' for beam mode '{beam_mode}'.\n"
                f'Supported profile types: {supported_profile_types}'
            )

        peak_class = cls._supported[scattering_type][beam_mode][profile_type]
        peak_obj = peak_class()

        return peak_obj
