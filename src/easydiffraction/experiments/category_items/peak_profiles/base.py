# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from typing import Optional

from easydiffraction.core.categories import CategoryItem
from easydiffraction.experiments.enums import BeamModeEnum
from easydiffraction.experiments.enums import PeakProfileTypeEnum
from easydiffraction.experiments.enums import ScatteringTypeEnum


class PeakBase(CategoryItem):
    def __init__(self) -> None:
        super().__init__()
        # Ensure category identity is set for all peak subclasses
        self._identity.category_code = 'peak'


class PeakFactory:
    ST = ScatteringTypeEnum
    BM = BeamModeEnum
    PPT = PeakProfileTypeEnum
    _supported = None  # type: ignore[var-annotated]

    @classmethod
    def _supported_map(cls):
        # Lazy import to avoid circular imports between
        # base and cw/tof/pdf modules
        if cls._supported is None:
            from easydiffraction.experiments.category_items.peak_profiles.cw import (
                ConstantWavelengthPseudoVoigt as CwPv,
            )
            from easydiffraction.experiments.category_items.peak_profiles.cw import (
                ConstantWavelengthSplitPseudoVoigt as CwSpv,
            )
            from easydiffraction.experiments.category_items.peak_profiles.cw import (
                ConstantWavelengthThompsonCoxHastings as CwTch,
            )
            from easydiffraction.experiments.category_items.peak_profiles.pdf import (
                PairDistributionFunctionGaussianDampedSinc as PdfGds,
            )
            from easydiffraction.experiments.category_items.peak_profiles.tof import (
                TimeOfFlightPseudoVoigt as TofPv,
            )
            from easydiffraction.experiments.category_items.peak_profiles.tof import (
                TimeOfFlightPseudoVoigtBackToBack as TofBtb,
            )
            from easydiffraction.experiments.category_items.peak_profiles.tof import (
                TimeOfFlightPseudoVoigtIkedaCarpenter as TofIc,
            )

            cls._supported = {
                cls.ST.BRAGG: {
                    cls.BM.CONSTANT_WAVELENGTH: {
                        cls.PPT.PSEUDO_VOIGT: CwPv,
                        cls.PPT.SPLIT_PSEUDO_VOIGT: CwSpv,
                        cls.PPT.THOMPSON_COX_HASTINGS: CwTch,
                    },
                    cls.BM.TIME_OF_FLIGHT: {
                        cls.PPT.PSEUDO_VOIGT: TofPv,
                        cls.PPT.PSEUDO_VOIGT_IKEDA_CARPENTER: TofIc,
                        cls.PPT.PSEUDO_VOIGT_BACK_TO_BACK: TofBtb,
                    },
                },
                cls.ST.TOTAL: {
                    cls.BM.CONSTANT_WAVELENGTH: {
                        cls.PPT.GAUSSIAN_DAMPED_SINC: PdfGds,
                    },
                    cls.BM.TIME_OF_FLIGHT: {
                        cls.PPT.GAUSSIAN_DAMPED_SINC: PdfGds,
                    },
                },
            }
        return cls._supported

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
        supported = cls._supported_map()
        supported_scattering_types = list(supported.keys())
        if scattering_type not in supported_scattering_types:
            raise ValueError(
                f"Unsupported scattering type: '{scattering_type}'.\n"
                f'Supported scattering types: {supported_scattering_types}'
            )

        supported_beam_modes = list(supported[scattering_type].keys())
        if beam_mode not in supported_beam_modes:
            raise ValueError(
                f"Unsupported beam mode: '{beam_mode}' for scattering type: "
                f"'{scattering_type}'.\n Supported beam modes: '{supported_beam_modes}'"
            )

        supported_profile_types = list(supported[scattering_type][beam_mode].keys())
        if profile_type not in supported_profile_types:
            raise ValueError(
                f"Unsupported profile type '{profile_type}' for beam mode '{beam_mode}'.\n"
                f'Supported profile types: {supported_profile_types}'
            )

        peak_class = supported[scattering_type][beam_mode][profile_type]
        peak_obj = peak_class()

        return peak_obj
