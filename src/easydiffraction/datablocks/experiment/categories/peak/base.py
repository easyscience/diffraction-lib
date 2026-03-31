# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Base class for peak profile categories."""

from easydiffraction.core.category import CategoryItem


class PeakBase(CategoryItem):
    """Base class for peak profile categories."""

    def __init__(self) -> None:
        super().__init__()
        self._identity.category_code = 'peak'
