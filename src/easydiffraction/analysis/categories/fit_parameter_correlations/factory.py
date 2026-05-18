# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Fit-parameter-correlation factory."""

from __future__ import annotations

from typing import ClassVar

from easydiffraction.core.factory import FactoryBase


class FitParameterCorrelationsFactory(FactoryBase):
    """Create fit-parameter correlation collections by tag."""

    _default_rules: ClassVar[dict] = {
        frozenset(): 'default',
    }
