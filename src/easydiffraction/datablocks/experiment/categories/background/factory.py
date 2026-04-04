# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Background factory — delegates entirely to ``FactoryBase``."""

from __future__ import annotations

from typing import ClassVar

from easydiffraction.core.factory import FactoryBase
from easydiffraction.datablocks.experiment.categories.background.enums import BackgroundTypeEnum


class BackgroundFactory(FactoryBase):
    """Create background collections by tag."""

    _default_rules: ClassVar[dict] = {
        frozenset(): BackgroundTypeEnum.LINE_SEGMENT,
    }
