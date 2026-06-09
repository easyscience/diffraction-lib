# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Data-range category base definition.

The data range defines the reciprocal-space region (and, for powder, the
profile step) used to build the calculation grid when no measured scan
exists. Concrete per-type classes live alongside this module.
"""

from __future__ import annotations

from easydiffraction.core.category import CategoryItem


class DataRangeBase(CategoryItem):
    """
    Base class for data-range category items.

    Sets the common ``category_code`` shared by the concrete CWL, TOF,
    and single-crystal data-range definitions.
    """

    _category_code = 'data_range'

    def __init__(self) -> None:
        """Initialize the data-range base."""
        super().__init__()
