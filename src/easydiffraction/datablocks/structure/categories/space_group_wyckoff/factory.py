# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Space-group Wyckoff factory — delegates entirely to ``FactoryBase``.
"""

from __future__ import annotations

from typing import ClassVar

from easydiffraction.core.factory import FactoryBase


class SpaceGroupWyckoffFactory(FactoryBase):
    """Create space-group Wyckoff collections by tag."""

    _default_rules: ClassVar[dict] = {
        frozenset(): 'default',
    }
