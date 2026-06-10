# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Data-range factory — delegates to ``FactoryBase``."""

from __future__ import annotations

from typing import ClassVar

from easydiffraction.core.factory import FactoryBase
from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum


class DataRangeFactory(FactoryBase):
    """Create data-range instances for supported experiment types."""

    _default_rules: ClassVar[dict] = {
        frozenset({
            ('beam_mode', BeamModeEnum.CONSTANT_WAVELENGTH),
            ('sample_form', SampleFormEnum.POWDER),
        }): 'cwl-pd',
        frozenset({
            ('beam_mode', BeamModeEnum.TIME_OF_FLIGHT),
            ('sample_form', SampleFormEnum.POWDER),
        }): 'tof-pd',
        # Both single-crystal beam modes share one sinθ/λ data range.
        frozenset({
            ('beam_mode', BeamModeEnum.CONSTANT_WAVELENGTH),
            ('sample_form', SampleFormEnum.SINGLE_CRYSTAL),
        }): 'sc',
        frozenset({
            ('beam_mode', BeamModeEnum.TIME_OF_FLIGHT),
            ('sample_form', SampleFormEnum.SINGLE_CRYSTAL),
        }): 'sc',
    }
