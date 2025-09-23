# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
from enum import Enum
from typing import Optional

from easydiffraction.core.categories import CategoryItem
from easydiffraction.core.parameters import Parameter
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
            (
                ScatteringTypeEnum.BRAGG,
                BeamModeEnum.CONSTANT_WAVELENGTH,
            ): cls.PSEUDO_VOIGT,
            (
                ScatteringTypeEnum.BRAGG,
                BeamModeEnum.TIME_OF_FLIGHT,
            ): cls.PSEUDO_VOIGT_IKEDA_CARPENTER,
            (
                ScatteringTypeEnum.TOTAL,
                BeamModeEnum.CONSTANT_WAVELENGTH,
            ): cls.GAUSSIAN_DAMPED_SINC,
            (
                ScatteringTypeEnum.TOTAL,
                BeamModeEnum.TIME_OF_FLIGHT,
            ): cls.GAUSSIAN_DAMPED_SINC,
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
    _class_public_attrs = {
        'broad_gauss_u',
        'broad_gauss_v',
        'broad_gauss_w',
        'broad_lorentz_x',
        'broad_lorentz_y',
    }

    def _add_constant_wavelength_broadening(self) -> None:
        self.broad_gauss_u: Parameter = Parameter(
            value=0.01,
            name='broad_gauss_u',
            full_cif_names=['_peak.broad_gauss_u'],
            default_value=0.01,
            units='deg²',
            description='Gaussian broadening coefficient (dependent on '
            'sample size and instrument resolution)',
        )
        self.broad_gauss_v: Parameter = Parameter(
            value=-0.01,
            name='broad_gauss_v',
            full_cif_names=['_peak.broad_gauss_v'],
            default_value=-0.01,
            units='deg²',
            description='Gaussian broadening coefficient (instrumental broadening contribution)',
        )
        self.broad_gauss_w: Parameter = Parameter(
            value=0.02,
            name='broad_gauss_w',
            full_cif_names=['_peak.broad_gauss_w'],
            default_value=0.02,
            units='deg²',
            description='Gaussian broadening coefficient (instrumental broadening contribution)',
        )
        self.broad_lorentz_x: Parameter = Parameter(
            value=0.0,
            name='broad_lorentz_x',
            full_cif_names=['_peak.broad_lorentz_x'],
            default_value=0.0,
            units='deg',
            description='Lorentzian broadening coefficient (dependent on sample strain effects)',
        )
        self.broad_lorentz_y: Parameter = Parameter(
            value=0.0,
            name='broad_lorentz_y',
            full_cif_names=['_peak.broad_lorentz_y'],
            default_value=0.0,
            units='deg',
            description='Lorentzian broadening coefficient (dependent on '
            'microstructural defects and strain)',
        )


class TimeOfFlightBroadeningMixin:
    _class_public_attrs = {
        'broad_gauss_sigma_0',
        'broad_gauss_sigma_1',
        'broad_gauss_sigma_2',
        'broad_lorentz_gamma_0',
        'broad_lorentz_gamma_1',
        'broad_lorentz_gamma_2',
        'broad_mix_beta_0',
        'broad_mix_beta_1',
    }

    def _add_time_of_flight_broadening(self) -> None:
        self.broad_gauss_sigma_0: Parameter = Parameter(
            value=0.0,
            name='gauss_sigma_0',
            full_cif_names=['_peak.gauss_sigma_0'],
            default_value=0.0,
            units='µs²',
            description='Gaussian broadening coefficient (instrumental resolution)',
        )
        self.broad_gauss_sigma_1: Parameter = Parameter(
            value=0.0,
            name='gauss_sigma_1',
            full_cif_names=['_peak.gauss_sigma_1'],
            default_value=0.0,
            units='µs/Å',
            description='Gaussian broadening coefficient (dependent on d-spacing)',
        )
        self.broad_gauss_sigma_2: Parameter = Parameter(
            value=0.0,
            name='gauss_sigma_2',
            full_cif_names=['_peak.gauss_sigma_2'],
            default_value=0.0,
            units='µs²/Å²',
            description='Gaussian broadening coefficient (instrument-dependent term)',
        )
        self.broad_lorentz_gamma_0: Parameter = Parameter(
            value=0.0,
            name='lorentz_gamma_0',
            full_cif_names=['_peak.lorentz_gamma_0'],
            default_value=0.0,
            units='µs',
            description='Lorentzian broadening coefficient (dependent on microstrain effects)',
        )
        self.broad_lorentz_gamma_1: Parameter = Parameter(
            value=0.0,
            name='lorentz_gamma_1',
            full_cif_names=['_peak.lorentz_gamma_1'],
            default_value=0.0,
            units='µs/Å',
            description='Lorentzian broadening coefficient (dependent on d-spacing)',
        )
        self.broad_lorentz_gamma_2: Parameter = Parameter(
            value=0.0,
            name='lorentz_gamma_2',
            full_cif_names=['_peak.lorentz_gamma_2'],
            default_value=0.0,
            units='µs²/Å²',
            description='Lorentzian broadening coefficient (instrumental-dependent term)',
        )
        self.broad_mix_beta_0: Parameter = Parameter(
            value=0.0,
            name='mix_beta_0',
            full_cif_names=['_peak.mix_beta_0'],
            default_value=0.0,
            units='deg',
            description='Mixing parameter. Defines the ratio of Gaussian '
            'to Lorentzian contributions in TOF profiles',
        )
        self.broad_mix_beta_1: Parameter = Parameter(
            value=0.0,
            name='mix_beta_1',
            full_cif_names=['_peak.mix_beta_1'],
            default_value=0.0,
            units='deg',
            description='Mixing parameter. Defines the ratio of Gaussian '
            'to Lorentzian contributions in TOF profiles',
        )


class EmpiricalAsymmetryMixin:
    _class_public_attrs = {
        'asym_empir_1',
        'asym_empir_2',
        'asym_empir_3',
        'asym_empir_4',
    }

    def _add_empirical_asymmetry(self) -> None:
        self.asym_empir_1: Parameter = Parameter(
            value=0.1,
            name='asym_empir_1',
            full_cif_names=['_peak.asym_empir_1'],
            default_value=0.1,
            units='',
            description='Empirical asymmetry coefficient p1',
        )
        self.asym_empir_2: Parameter = Parameter(
            value=0.2,
            name='asym_empir_2',
            full_cif_names=['_peak.asym_empir_2'],
            default_value=0.2,
            units='',
            description='Empirical asymmetry coefficient p2',
        )
        self.asym_empir_3: Parameter = Parameter(
            value=0.3,
            name='asym_empir_3',
            full_cif_names=['_peak.asym_empir_3'],
            default_value=0.3,
            units='',
            description='Empirical asymmetry coefficient p3',
        )
        self.asym_empir_4: Parameter = Parameter(
            value=0.4,
            name='asym_empir_4',
            full_cif_names=['_peak.asym_empir_4'],
            default_value=0.4,
            units='',
            description='Empirical asymmetry coefficient p4',
        )


class FcjAsymmetryMixin:
    _class_public_attrs = {
        'asym_fcj_1',
        'asym_fcj_2',
    }

    def _add_fcj_asymmetry(self) -> None:
        self.asym_fcj_1: Parameter = Parameter(
            value=0.01,
            name='asym_fcj_1',
            full_cif_names=['_peak.asym_fcj_1'],
            default_value=0.01,
            units='',
            description='FCJ asymmetry coefficient 1',
        )
        self.asym_fcj_2: Parameter = Parameter(
            value=0.02,
            name='asym_fcj_2',
            full_cif_names=['_peak.asym_fcj_2'],
            default_value=0.02,
            units='',
            description='FCJ asymmetry coefficient 2',
        )


class IkedaCarpenterAsymmetryMixin:
    _class_public_attrs = {
        'asym_alpha_0',
        'asym_alpha_1',
    }

    def _add_ikeda_carpenter_asymmetry(self) -> None:
        self.asym_alpha_0: Parameter = Parameter(
            value=0.01,
            name='asym_alpha_0',
            full_cif_names=['_peak.asym_alpha_0'],
            default_value=0.01,
            units='',
            description='Ikeda-Carpenter asymmetry parameter α₀',
        )
        self.asym_alpha_1: Parameter = Parameter(
            value=0.02,
            name='asym_alpha_1',
            full_cif_names=['_peak.asym_alpha_1'],
            default_value=0.02,
            units='',
            description='Ikeda-Carpenter asymmetry parameter α₁',
        )


class PairDistributionFunctionBroadeningMixin:
    _class_public_attrs = {
        'damp_q',
        'broad_q',
        'cutoff_q',
        'sharp_delta_1',
        'sharp_delta_2',
        'damp_particle_diameter',
    }

    def _add_pair_distribution_function_broadening(self):
        self.damp_q = Parameter(
            value=0.05,
            name='damp_q',
            full_cif_names=['_peak.damp_q'],
            default_value=0.05,
            units='Å⁻¹',
            description='Instrumental Q-resolution damping factor '
            '(affects high-r PDF peak amplitude)',
        )
        self.broad_q = Parameter(
            value=0.0,
            name='broad_q',
            full_cif_names=['_peak.broad_q'],
            default_value=0.0,
            units='Å⁻²',
            description='Quadratic PDF peak broadening coefficient '
            '(thermal and model uncertainty contribution)',
        )
        self.cutoff_q = Parameter(
            value=25.0,
            name='cutoff_q',
            full_cif_names=['_peak.cutoff_q'],
            default_value=25.0,
            units='Å⁻¹',
            description='Q-value cutoff applied to model PDF for Fourier '
            'transform (controls real-space resolution)',
        )
        self.sharp_delta_1 = Parameter(
            value=0.0,
            name='sharp_delta_1',
            full_cif_names=['_peak.sharp_delta_1'],
            default_value=0.0,
            units='Å',
            description='PDF peak sharpening coefficient (1/r dependence)',
        )
        self.sharp_delta_2 = Parameter(
            value=0.0,
            name='sharp_delta_2',
            full_cif_names=['_peak.sharp_delta_2'],
            default_value=0.0,
            units='Å²',
            description='PDF peak sharpening coefficient (1/r² dependence)',
        )
        self.damp_particle_diameter = Parameter(
            value=0.0,
            name='damp_particle_diameter',
            full_cif_names=['_peak.damp_particle_diameter'],
            default_value=0.0,
            units='Å',
            description='Particle diameter for spherical envelope damping correction in PDF',
        )


# --- Base peak class ---
class PeakBase(CategoryItem):
    @property
    def category_key(self) -> str:
        return 'peak'


# --- Derived peak classes ---
class ConstantWavelengthPseudoVoigt(
    PeakBase,
    ConstantWavelengthBroadeningMixin,
):
    def __init__(self) -> None:
        super().__init__()

        self._add_constant_wavelength_broadening()


class ConstantWavelengthSplitPseudoVoigt(
    PeakBase,
    ConstantWavelengthBroadeningMixin,
    EmpiricalAsymmetryMixin,
):
    def __init__(self) -> None:
        super().__init__()

        self._add_constant_wavelength_broadening()
        self._add_empirical_asymmetry()


class ConstantWavelengthThompsonCoxHastings(
    PeakBase,
    ConstantWavelengthBroadeningMixin,
    FcjAsymmetryMixin,
):
    def __init__(self) -> None:
        super().__init__()

        self._add_constant_wavelength_broadening()
        self._add_fcj_asymmetry()


class TimeOfFlightPseudoVoigt(
    PeakBase,
    TimeOfFlightBroadeningMixin,
):
    def __init__(self) -> None:
        super().__init__()

        self._add_time_of_flight_broadening()


class TimeOfFlightPseudoVoigtIkedaCarpenter(
    PeakBase,
    TimeOfFlightBroadeningMixin,
    IkedaCarpenterAsymmetryMixin,
):
    def __init__(self) -> None:
        super().__init__()

        self._add_time_of_flight_broadening()
        self._add_ikeda_carpenter_asymmetry()


class TimeOfFlightPseudoVoigtBackToBack(
    PeakBase,
    TimeOfFlightBroadeningMixin,
    IkedaCarpenterAsymmetryMixin,
):
    def __init__(self) -> None:
        super().__init__()

        self._add_time_of_flight_broadening()
        self._add_ikeda_carpenter_asymmetry()


class PairDistributionFunctionGaussianDampedSinc(
    PeakBase,
    PairDistributionFunctionBroadeningMixin,
):
    def __init__(self):
        super().__init__()
        self._add_pair_distribution_function_broadening()


# --- Peak factory ---
class PeakFactory:
    ST = ScatteringTypeEnum
    BM = BeamModeEnum
    PPT = PeakProfileTypeEnum
    _supported = {
        ST.BRAGG: {
            BM.CONSTANT_WAVELENGTH: {
                PPT.PSEUDO_VOIGT: ConstantWavelengthPseudoVoigt,
                PPT.SPLIT_PSEUDO_VOIGT: ConstantWavelengthSplitPseudoVoigt,
                PPT.THOMPSON_COX_HASTINGS: ConstantWavelengthThompsonCoxHastings,
            },
            BM.TIME_OF_FLIGHT: {
                PPT.PSEUDO_VOIGT: TimeOfFlightPseudoVoigt,
                PPT.PSEUDO_VOIGT_IKEDA_CARPENTER: TimeOfFlightPseudoVoigtIkedaCarpenter,
                PPT.PSEUDO_VOIGT_BACK_TO_BACK: TimeOfFlightPseudoVoigtBackToBack,
            },
        },
        ST.TOTAL: {
            BM.CONSTANT_WAVELENGTH: {
                PPT.GAUSSIAN_DAMPED_SINC: PairDistributionFunctionGaussianDampedSinc,
            },
            BM.TIME_OF_FLIGHT: {
                PPT.GAUSSIAN_DAMPED_SINC: PairDistributionFunctionGaussianDampedSinc,
            },
        },
    }

    @classmethod
    def create(
        cls,
        scattering_type: Optional[ScatteringTypeEnum] = None,
        beam_mode: Optional[BeamModeEnum] = None,
        profile_type: Optional[PeakProfileTypeEnum] = None,
    ):
        if beam_mode is None:
            beam_mode = BeamModeEnum.default()
        if scattering_type is None:
            scattering_type = ScatteringTypeEnum.default()
        if profile_type is None:
            profile_type = PeakProfileTypeEnum.default(scattering_type, beam_mode)

        supported_scattering_types = list(cls._supported.keys())
        if scattering_type not in supported_scattering_types:
            raise ValueError(
                f"Unsupported scattering type: '{scattering_type}'.\n"
                f'Supported scattering types: {supported_scattering_types}'
            )

        supported_beam_modes = list(cls._supported[scattering_type].keys())
        if beam_mode not in supported_beam_modes:
            raise ValueError(
                f"Unsupported beam mode: '{beam_mode}' for scattering type: "
                f"'{scattering_type}'.\n Supported beam modes: '{supported_beam_modes}'"
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
