# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Instrument category base definitions for CWL/TOF instruments.

This module provides the shared parent used by concrete instrument
implementations under the instrument category.
"""

from __future__ import annotations

from easydiffraction.core.category import CategoryItem


class InstrumentBase(CategoryItem):
    """
    Base class for instrument category items.

    This class sets the common ``category_code`` and is used as a base
    for concrete CWL/TOF instrument definitions.
    """

    _category_code = 'instrument'

    def __init__(self) -> None:
        """Initialize instrument base."""
        super().__init__()
