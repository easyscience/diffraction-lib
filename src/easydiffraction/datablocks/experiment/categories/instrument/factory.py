# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Instrument factory — delegates to ``FactoryBase``."""

from easydiffraction.core.factory import FactoryBase
from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum


class InstrumentFactory(FactoryBase):
    """Create instrument instances for supported modes."""

    _default_rules = {
        frozenset({
            ('beam_mode', BeamModeEnum.CONSTANT_WAVELENGTH),
            ('sample_form', SampleFormEnum.POWDER),
        }): 'cwl-pd',
        frozenset({
            ('beam_mode', BeamModeEnum.CONSTANT_WAVELENGTH),
            ('sample_form', SampleFormEnum.SINGLE_CRYSTAL),
        }): 'cwl-sc',
        frozenset({
            ('beam_mode', BeamModeEnum.TIME_OF_FLIGHT),
            ('sample_form', SampleFormEnum.POWDER),
        }): 'tof-pd',
        frozenset({
            ('beam_mode', BeamModeEnum.TIME_OF_FLIGHT),
            ('sample_form', SampleFormEnum.SINGLE_CRYSTAL),
        }): 'tof-sc',
    }
