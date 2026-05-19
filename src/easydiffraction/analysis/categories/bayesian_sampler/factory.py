# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Bayesian-sampler factory."""

from __future__ import annotations

from typing import ClassVar

from easydiffraction.core.factory import FactoryBase


class BayesianSamplerFactory(FactoryBase):
    """Create Bayesian-sampler categories by tag."""

    _default_rules: ClassVar[dict] = {
        frozenset(): 'default',
    }
