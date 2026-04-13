# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Peak profile factory — delegates to ``FactoryBase``."""

from __future__ import annotations

from typing import ClassVar

from easydiffraction.core.factory import FactoryBase
from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import PeakProfileTypeEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum


class PeakFactory(FactoryBase):
    """Factory for creating peak profile objects."""

    _default_rules: ClassVar[dict] = {
        frozenset({
            ('scattering_type', ScatteringTypeEnum.BRAGG),
            ('beam_mode', BeamModeEnum.CONSTANT_WAVELENGTH),
        }): PeakProfileTypeEnum.PSEUDO_VOIGT,
        frozenset({
            ('scattering_type', ScatteringTypeEnum.BRAGG),
            ('beam_mode', BeamModeEnum.TIME_OF_FLIGHT),
        }): PeakProfileTypeEnum.JORGENSEN,
        frozenset({
            ('scattering_type', ScatteringTypeEnum.TOTAL),
        }): PeakProfileTypeEnum.GAUSSIAN_DAMPED_SINC,
    }
