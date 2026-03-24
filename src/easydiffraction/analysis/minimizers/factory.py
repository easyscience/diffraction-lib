# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Minimizer factory — delegates to ``FactoryBase``."""

from __future__ import annotations

from easydiffraction.core.factory import FactoryBase


class MinimizerFactory(FactoryBase):
    """Factory for creating minimizer instances."""

    _default_rules = {
        frozenset(): 'lmfit',
    }
