# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Internal implementation package for the Instrument category.

Split by beam mode/domain. Public consumers should import from the
category entry point
`easydiffraction.experiments.category_items.instrument`.

Re-exports are provided for contributor discoverability and focused
tests.
"""

from easydiffraction.experiments.category_items.instrument import InstrumentFactory
from easydiffraction.experiments.category_items.instrument_setups.base import InstrumentBase
from easydiffraction.experiments.category_items.instrument_setups.cw import (
    ConstantWavelengthInstrument,
)
from easydiffraction.experiments.category_items.instrument_setups.tof import TimeOfFlightInstrument

__all__ = [
    'ConstantWavelengthInstrument',
    'TimeOfFlightInstrument',
    'InstrumentBase',
    'InstrumentFactory',
]
