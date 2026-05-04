# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Reflection collection factory — delegates to ``FactoryBase``."""

from __future__ import annotations

from typing import ClassVar

from easydiffraction.core.factory import FactoryBase
from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum


class ReflnFactory(FactoryBase):
    """Factory for creating reflection collections."""

    _default_rules: ClassVar[dict] = {
        frozenset({
            ('sample_form', SampleFormEnum.SINGLE_CRYSTAL),
            ('scattering_type', ScatteringTypeEnum.BRAGG),
            ('beam_mode', BeamModeEnum.CONSTANT_WAVELENGTH),
        }): 'bragg-sc',
        frozenset({
            ('sample_form', SampleFormEnum.SINGLE_CRYSTAL),
            ('scattering_type', ScatteringTypeEnum.BRAGG),
            ('beam_mode', BeamModeEnum.TIME_OF_FLIGHT),
        }): 'bragg-sc',
        frozenset({
            ('sample_form', SampleFormEnum.POWDER),
            ('scattering_type', ScatteringTypeEnum.BRAGG),
            ('beam_mode', BeamModeEnum.CONSTANT_WAVELENGTH),
        }): 'bragg-pd-refln',
        frozenset({
            ('sample_form', SampleFormEnum.POWDER),
            ('scattering_type', ScatteringTypeEnum.BRAGG),
            ('beam_mode', BeamModeEnum.TIME_OF_FLIGHT),
        }): 'bragg-pd-tof-refln',
    }
