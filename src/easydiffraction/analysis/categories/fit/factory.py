# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Fit factory — delegates entirely to ``FactoryBase``."""

from __future__ import annotations

from typing import ClassVar

from easydiffraction.core.factory import FactoryBase


class FitFactory(FactoryBase):
    """Create fit category items by tag."""

    _default_rules: ClassVar[dict] = {
        frozenset(): 'default',
    }
