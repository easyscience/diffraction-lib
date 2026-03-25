# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Fit-mode factory — delegates entirely to ``FactoryBase``."""

from __future__ import annotations

from easydiffraction.core.factory import FactoryBase


class FitModeFactory(FactoryBase):
    """Create fit-mode category items by tag."""

    _default_rules = {
        frozenset(): 'default',
    }
