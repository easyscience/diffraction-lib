# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Instrument category entry point (public facade).

End users should import Instrument classes from this module. Internals
live under the package
`easydiffraction.experiments.category_items.instrument_setups` and are
re-exported here for a stable and readable API.
"""

from easydiffraction.experiments.category_items.instrument_setups.base import InstrumentBase
from easydiffraction.experiments.category_items.instrument_setups.base import InstrumentFactory
from easydiffraction.experiments.category_items.instrument_setups.cw import (
    ConstantWavelengthInstrument,
)
from easydiffraction.experiments.category_items.instrument_setups.tof import TimeOfFlightInstrument

__all__ = [
    'InstrumentBase',
    'InstrumentFactory',
    'ConstantWavelengthInstrument',
    'TimeOfFlightInstrument',
]
