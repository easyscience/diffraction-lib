# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from easydiffraction.core.category import CategoryItem


class InstrumentBase(CategoryItem):
    """Base class for instrument category items.

    This class sets the common ``category_code`` and is used as a base
    for concrete CWL/TOF instrument definitions.
    """

    def __init__(self) -> None:
        super().__init__()
        self._identity.category_code = 'instrument'
