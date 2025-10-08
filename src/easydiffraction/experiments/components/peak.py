# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
from enum import Enum
from typing import Optional

from easydiffraction.core.categories import CategoryItem
from easydiffraction.core.guards import RangeValidator
from easydiffraction.core.parameters import Parameter
from easydiffraction.crystallography.cif import CifHandler
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
    def _add_constant_wavelength_broadening(self) -> None:
        self._broad_gauss_u: Parameter = Parameter(
            name='broad_gauss_u',
            description='Gaussian broadening coefficient (dependent on '
            'sample size and instrument resolution)',
            validator=RangeValidator(
                default=0.01,
            ),
            value=0.01,
            units='deg²',
            cif_handler=CifHandler(
                names=[
                    '_peak.broad_gauss_u',
                ]
            ),
        )
        self._broad_gauss_v: Parameter = Parameter(
            name='broad_gauss_v',
            description='Gaussian broadening coefficient (instrumental broadening contribution)',
            validator=RangeValidator(
                default=-0.01,
            ),
            value=-0.01,
            units='deg²',
            cif_handler=CifHandler(
                names=[
                    '_peak.broad_gauss_v',
                ]
            ),
        )
        self._broad_gauss_w: Parameter = Parameter(
            name='broad_gauss_w',
            description='Gaussian broadening coefficient (instrumental broadening contribution)',
            validator=RangeValidator(
                default=0.02,
            ),
            value=0.02,
            units='deg²',
            cif_handler=CifHandler(
                names=[
                    '_peak.broad_gauss_w',
                ]
            ),
        )
        self._broad_lorentz_x: Parameter = Parameter(
            name='broad_lorentz_x',
            description='Lorentzian broadening coefficient (dependent on sample strain effects)',
            validator=RangeValidator(
                default=0.0,
            ),
            value=0.0,
            units='deg',
            cif_handler=CifHandler(
                names=[
                    '_peak.broad_lorentz_x',
                ]
            ),
        )
        self._broad_lorentz_y: Parameter = Parameter(
            name='broad_lorentz_y',
            description='Lorentzian broadening coefficient (dependent on '
            'microstructural defects and strain)',
            validator=RangeValidator(
                default=0.0,
            ),
            value=0.0,
            units='deg',
            cif_handler=CifHandler(
                names=[
                    '_peak.broad_lorentz_y',
                ]
            ),
        )

    @property
    def broad_gauss_u(self) -> Parameter:
        return self._broad_gauss_u

    @broad_gauss_u.setter
    def broad_gauss_u(self, value: float) -> None:
        self._broad_gauss_u.value = value

    @property
    def broad_gauss_v(self) -> Parameter:
        return self._broad_gauss_v

    @broad_gauss_v.setter
    def broad_gauss_v(self, value: float) -> None:
        self._broad_gauss_v.value = value

    @property
    def broad_gauss_w(self) -> Parameter:
        return self._broad_gauss_w

    @broad_gauss_w.setter
    def broad_gauss_w(self, value: float) -> None:
        self._broad_gauss_w.value = value

    @property
    def broad_lorentz_x(self) -> Parameter:
        return self._broad_lorentz_x

    @broad_lorentz_x.setter
    def broad_lorentz_x(self, value: float) -> None:
        self._broad_lorentz_x.value = value

    @property
    def broad_lorentz_y(self) -> Parameter:
        return self._broad_lorentz_y

    @broad_lorentz_y.setter
    def broad_lorentz_y(self, value: float) -> None:
        self._broad_lorentz_y.value = value


class TimeOfFlightBroadeningMixin:
    def _add_time_of_flight_broadening(self) -> None:
        self._broad_gauss_sigma_0: Parameter = Parameter(
            name='gauss_sigma_0',
            description='Gaussian broadening coefficient (instrumental resolution)',
            validator=RangeValidator(
                default=0.0,
            ),
            value=0.0,
            units='µs²',
            cif_handler=CifHandler(
                names=[
                    '_peak.gauss_sigma_0',
                ]
            ),
        )
        self._broad_gauss_sigma_1: Parameter = Parameter(
            name='gauss_sigma_1',
            description='Gaussian broadening coefficient (dependent on d-spacing)',
            validator=RangeValidator(
                default=0.0,
            ),
            value=0.0,
            units='µs/Å',
            cif_handler=CifHandler(
                names=[
                    '_peak.gauss_sigma_1',
                ]
            ),
        )
        self._broad_gauss_sigma_2: Parameter = Parameter(
            name='gauss_sigma_2',
            description='Gaussian broadening coefficient (instrument-dependent term)',
            validator=RangeValidator(
                default=0.0,
            ),
            value=0.0,
            units='µs²/Å²',
            cif_handler=CifHandler(
                names=[
                    '_peak.gauss_sigma_2',
                ]
            ),
        )
        self._broad_lorentz_gamma_0: Parameter = Parameter(
            name='lorentz_gamma_0',
            description='Lorentzian broadening coefficient (dependent on microstrain effects)',
            validator=RangeValidator(
                default=0.0,
            ),
            value=0.0,
            units='µs',
            cif_handler=CifHandler(
                names=[
                    '_peak.lorentz_gamma_0',
                ]
            ),
        )
        self._broad_lorentz_gamma_1: Parameter = Parameter(
            name='lorentz_gamma_1',
            description='Lorentzian broadening coefficient (dependent on d-spacing)',
            validator=RangeValidator(
                default=0.0,
            ),
            value=0.0,
            units='µs/Å',
            cif_handler=CifHandler(
                names=[
                    '_peak.lorentz_gamma_1',
                ]
            ),
        )
        self._broad_lorentz_gamma_2: Parameter = Parameter(
            name='lorentz_gamma_2',
            description='Lorentzian broadening coefficient (instrument-dependent term)',
            validator=RangeValidator(
                default=0.0,
            ),
            value=0.0,
            units='µs²/Å²',
            cif_handler=CifHandler(
                names=[
                    '_peak.lorentz_gamma_2',
                ]
            ),
        )
        self._broad_mix_beta_0: Parameter = Parameter(
            name='mix_beta_0',
            description='Mixing parameter. Defines the ratio of Gaussian '
            'to Lorentzian contributions in TOF profiles',
            validator=RangeValidator(
                default=0.0,
            ),
            value=0.0,
            units='deg',
            cif_handler=CifHandler(
                names=[
                    '_peak.mix_beta_0',
                ]
            ),
        )
        self._broad_mix_beta_1: Parameter = Parameter(
            name='mix_beta_1',
            description='Mixing parameter. Defines the ratio of Gaussian '
            'to Lorentzian contributions in TOF profiles',
            validator=RangeValidator(
                default=0.0,
            ),
            value=0.0,
            units='deg',
            cif_handler=CifHandler(
                names=[
                    '_peak.mix_beta_1',
                ]
            ),
        )

    @property
    def broad_gauss_sigma_0(self) -> Parameter:
        return self._broad_gauss_sigma_0

    @broad_gauss_sigma_0.setter
    def broad_gauss_sigma_0(self, value: float) -> None:
        self._broad_gauss_sigma_0.value = value

    @property
    def broad_gauss_sigma_1(self) -> Parameter:
        return self._broad_gauss_sigma_1

    @broad_gauss_sigma_1.setter
    def broad_gauss_sigma_1(self, value: float) -> None:
        self._broad_gauss_sigma_1.value = value

    @property
    def broad_gauss_sigma_2(self) -> Parameter:
        return self._broad_gauss_sigma_2

    @broad_gauss_sigma_2.setter
    def broad_gauss_sigma_2(self, value: float) -> None:
        self._broad_gauss_sigma_2.value = value

    @property
    def broad_lorentz_gamma_0(self) -> Parameter:
        return self._broad_lorentz_gamma_0

    @broad_lorentz_gamma_0.setter
    def broad_lorentz_gamma_0(self, value: float) -> None:
        self._broad_lorentz_gamma_0.value = value

    @property
    def broad_lorentz_gamma_1(self) -> Parameter:
        return self._broad_lorentz_gamma_1

    @broad_lorentz_gamma_1.setter
    def broad_lorentz_gamma_1(self, value: float) -> None:
        self._broad_lorentz_gamma_1.value = value

    @property
    def broad_lorentz_gamma_2(self) -> Parameter:
        return self._broad_lorentz_gamma_2

    @broad_lorentz_gamma_2.setter
    def broad_lorentz_gamma_2(self, value: float) -> None:
        self._broad_lorentz_gamma_2.value = value

    @property
    def broad_mix_beta_0(self) -> Parameter:
        return self._broad_mix_beta_0

    @broad_mix_beta_0.setter
    def broad_mix_beta_0(self, value: float) -> None:
        self._broad_mix_beta_0.value = value

    @property
    def broad_mix_beta_1(self) -> Parameter:
        return self._broad_mix_beta_1

    @broad_mix_beta_1.setter
    def broad_mix_beta_1(self, value: float) -> None:
        self._broad_mix_beta_1.value = value


class EmpiricalAsymmetryMixin:
    def _add_empirical_asymmetry(self) -> None:
        self._asym_empir_1: Parameter = Parameter(
            name='asym_empir_1',
            description='Empirical asymmetry coefficient p1',
            validator=RangeValidator(
                default=0.1,
            ),
            value=0.1,
            units='',
            cif_handler=CifHandler(
                names=[
                    '_peak.asym_empir_1',
                ]
            ),
        )
        self._asym_empir_2: Parameter = Parameter(
            name='asym_empir_2',
            description='Empirical asymmetry coefficient p2',
            validator=RangeValidator(
                default=0.2,
            ),
            value=0.2,
            units='',
            cif_handler=CifHandler(
                names=[
                    '_peak.asym_empir_2',
                ]
            ),
        )
        self._asym_empir_3: Parameter = Parameter(
            name='asym_empir_3',
            description='Empirical asymmetry coefficient p3',
            validator=RangeValidator(
                default=0.3,
            ),
            value=0.3,
            units='',
            cif_handler=CifHandler(
                names=[
                    '_peak.asym_empir_3',
                ]
            ),
        )
        self._asym_empir_4: Parameter = Parameter(
            name='asym_empir_4',
            description='Empirical asymmetry coefficient p4',
            validator=RangeValidator(
                default=0.4,
            ),
            value=0.4,
            units='',
            cif_handler=CifHandler(
                names=[
                    '_peak.asym_empir_4',
                ]
            ),
        )

    @property
    def asym_empir_1(self) -> Parameter:
        return self._asym_empir_1

    @asym_empir_1.setter
    def asym_empir_1(self, value: float) -> None:
        self._asym_empir_1.value = value

    @property
    def asym_empir_2(self) -> Parameter:
        return self._asym_empir_2

    @asym_empir_2.setter
    def asym_empir_2(self, value: float) -> None:
        self._asym_empir_2.value = value

    @property
    def asym_empir_3(self) -> Parameter:
        return self._asym_empir_3

    @asym_empir_3.setter
    def asym_empir_3(self, value: float) -> None:
        self._asym_empir_3.value = value

    @property
    def asym_empir_4(self) -> Parameter:
        return self._asym_empir_4

    @asym_empir_4.setter
    def asym_empir_4(self, value: float) -> None:
        self._asym_empir_4.value = value


class FcjAsymmetryMixin:
    def _add_fcj_asymmetry(self) -> None:
        self._asym_fcj_1: Parameter = Parameter(
            name='asym_fcj_1',
            description='FCJ asymmetry coefficient 1',
            validator=RangeValidator(
                default=0.01,
            ),
            value=0.01,
            units='',
            cif_handler=CifHandler(
                names=[
                    '_peak.asym_fcj_1',
                ]
            ),
        )
        self._asym_fcj_2: Parameter = Parameter(
            name='asym_fcj_2',
            description='FCJ asymmetry coefficient 2',
            validator=RangeValidator(
                default=0.02,
            ),
            value=0.02,
            units='',
            cif_handler=CifHandler(
                names=[
                    '_peak.asym_fcj_2',
                ]
            ),
        )

    @property
    def asym_fcj_1(self) -> Parameter:
        return self._asym_fcj_1

    @asym_fcj_1.setter
    def asym_fcj_1(self, value: float) -> None:
        self._asym_fcj_1.value = value

    @property
    def asym_fcj_2(self) -> Parameter:
        return self._asym_fcj_2

    @asym_fcj_2.setter
    def asym_fcj_2(self, value: float) -> None:
        self._asym_fcj_2.value = value


class IkedaCarpenterAsymmetryMixin:
    def _add_ikeda_carpenter_asymmetry(self) -> None:
        self._asym_alpha_0: Parameter = Parameter(
            name='asym_alpha_0',
            description='Ikeda-Carpenter asymmetry parameter α₀',
            validator=RangeValidator(
                default=0.01,
            ),
            value=0.01,
            units='',
            cif_handler=CifHandler(
                names=[
                    '_peak.asym_alpha_0',
                ]
            ),
        )
        self._asym_alpha_1: Parameter = Parameter(
            name='asym_alpha_1',
            description='Ikeda-Carpenter asymmetry parameter α₁',
            validator=RangeValidator(
                default=0.02,
            ),
            value=0.02,
            units='',
            cif_handler=CifHandler(
                names=[
                    '_peak.asym_alpha_1',
                ]
            ),
        )

    @property
    def asym_alpha_0(self) -> Parameter:
        return self._asym_alpha_0

    @asym_alpha_0.setter
    def asym_alpha_0(self, value: float) -> None:
        self._asym_alpha_0.value = value

    @property
    def asym_alpha_1(self) -> Parameter:
        return self._asym_alpha_1


class PairDistributionFunctionBroadeningMixin:
    def _add_pair_distribution_function_broadening(self):
        self._damp_q: Parameter = Parameter(
            name='damp_q',
            description='Instrumental Q-resolution damping factor '
            '(affects high-r PDF peak amplitude)',
            validator=RangeValidator(
                default=0.05,
            ),
            value=0.05,
            units='Å⁻¹',
            cif_handler=CifHandler(
                names=[
                    '_peak.damp_q',
                ]
            ),
        )
        self._broad_q: Parameter = Parameter(
            name='broad_q',
            description='Quadratic PDF peak broadening coefficient '
            '(thermal and model uncertainty contribution)',
            validator=RangeValidator(
                default=0.0,
            ),
            value=0.0,
            units='Å⁻²',
            cif_handler=CifHandler(
                names=[
                    '_peak.broad_q',
                ]
            ),
        )
        self._cutoff_q: Parameter = Parameter(
            name='cutoff_q',
            description='Q-value cutoff applied to model PDF for Fourier '
            'transform (controls real-space resolution)',
            validator=RangeValidator(
                default=25.0,
            ),
            value=25.0,
            units='Å⁻¹',
            cif_handler=CifHandler(
                names=[
                    '_peak.cutoff_q',
                ]
            ),
        )
        self._sharp_delta_1: Parameter = Parameter(
            name='sharp_delta_1',
            description='PDF peak sharpening coefficient (1/r dependence)',
            validator=RangeValidator(
                default=0.0,
            ),
            value=0.0,
            units='Å',
            cif_handler=CifHandler(
                names=[
                    '_peak.sharp_delta_1',
                ]
            ),
        )
        self._sharp_delta_2: Parameter = Parameter(
            name='sharp_delta_2',
            description='PDF peak sharpening coefficient (1/r² dependence)',
            validator=RangeValidator(
                default=0.0,
            ),
            value=0.0,
            units='Å²',
            cif_handler=CifHandler(
                names=[
                    '_peak.sharp_delta_2',
                ]
            ),
        )
        self._damp_particle_diameter: Parameter = Parameter(
            name='damp_particle_diameter',
            description='Particle diameter for spherical envelope damping correction in PDF',
            validator=RangeValidator(
                default=0.0,
            ),
            value=0.0,
            units='Å',
            cif_handler=CifHandler(
                names=[
                    '_peak.damp_particle_diameter',
                ]
            ),
        )

    @property
    def damp_q(self) -> Parameter:
        return self._damp_q

    @damp_q.setter
    def damp_q(self, value: float) -> None:
        self._damp_q.value = value

    @property
    def broad_q(self) -> Parameter:
        return self._broad_q

    @broad_q.setter
    def broad_q(self, value: float) -> None:
        self._broad_q.value = value

    @property
    def cutoff_q(self) -> Parameter:
        return self._cutoff_q

    @cutoff_q.setter
    def cutoff_q(self, value: float) -> None:
        self._cutoff_q.value = value

    @property
    def sharp_delta_1(self) -> Parameter:
        return self._sharp_delta_1

    @sharp_delta_1.setter
    def sharp_delta_1(self, value: float) -> None:
        self._sharp_delta_1.value = value

    @property
    def sharp_delta_2(self) -> Parameter:
        return self._sharp_delta_2

    @sharp_delta_2.setter
    def sharp_delta_2(self, value: float) -> None:
        self._sharp_delta_2.value = value

    @property
    def damp_particle_diameter(self) -> Parameter:
        return self._damp_particle_diameter

    @damp_particle_diameter.setter
    def damp_particle_diameter(self, value: float) -> None:
        self._damp_particle_diameter.value = value


# --- Base peak class ---
class PeakBase(CategoryItem):
    def __init__(
        self,
    ) -> None:
        super().__init__()
        self._identity.category_code = 'peak'


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
