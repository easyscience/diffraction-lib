# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Linked-crystal factory — delegates entirely to ``FactoryBase``."""

from __future__ import annotations

from easydiffraction.core.factory import FactoryBase


class ConditionsFactory(FactoryBase):
    """Create experimental conditions."""

    _default_rules = {
        frozenset(): 'default',
    }
