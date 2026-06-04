# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Factory for persisted minimizer category items."""

from __future__ import annotations

from typing import ClassVar

from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum
from easydiffraction.core.factory import FactoryBase


class MinimizerCategoryFactory(FactoryBase):
    """Create minimizer category items by tag."""

    _default_rules: ClassVar[dict] = {
        frozenset(): MinimizerTypeEnum.default().value,
    }
