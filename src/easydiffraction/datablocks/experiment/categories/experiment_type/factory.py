# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Experiment-type factory — delegates entirely to ``FactoryBase``."""

from __future__ import annotations

from easydiffraction.core.factory import FactoryBase


class ExperimentTypeFactory(FactoryBase):
    """Create experiment-type descriptors by tag."""

    _default_rules = {
        frozenset(): 'default',
    }
