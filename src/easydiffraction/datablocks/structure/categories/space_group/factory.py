# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Space-group factory — delegates entirely to ``FactoryBase``."""

from __future__ import annotations

from easydiffraction.core.factory import FactoryBase


class SpaceGroupFactory(FactoryBase):
    """Create space-group categories by tag."""

    _default_rules = {
        frozenset(): 'default',
    }
