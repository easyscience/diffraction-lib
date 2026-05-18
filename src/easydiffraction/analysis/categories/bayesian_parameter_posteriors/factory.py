# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Bayesian-parameter-posteriors factory."""

from __future__ import annotations

from typing import ClassVar

from easydiffraction.core.factory import FactoryBase


class BayesianParameterPosteriorsFactory(FactoryBase):
    """Create Bayesian-parameter-posterior collections by tag."""

    _default_rules: ClassVar[dict] = {
        frozenset(): 'default',
    }