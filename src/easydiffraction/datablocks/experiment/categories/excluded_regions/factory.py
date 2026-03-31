# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Excluded-regions factory — delegates entirely to ``FactoryBase``.
"""

from __future__ import annotations

from easydiffraction.core.factory import FactoryBase


class ExcludedRegionsFactory(FactoryBase):
    """Create excluded-regions collections by tag."""

    _default_rules = {
        frozenset(): 'default',
    }
