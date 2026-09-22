# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Persisted category for the BUMPS amoeba minimizer."""

from __future__ import annotations

from typing import ClassVar

from easydiffraction.analysis.categories.minimizer.factory import MinimizerCategoryFactory
from easydiffraction.analysis.categories.minimizer.lsq_base import (
    ObjectiveParameterToleranceMinimizerBase,
)
from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum
from easydiffraction.core.metadata import TypeInfo


@MinimizerCategoryFactory.register
class BumpsAmoebaMinimizer(ObjectiveParameterToleranceMinimizerBase):
    """Persisted settings for the BUMPS amoeba minimizer."""

    _engine_metadata: ClassVar[dict[str, str]] = {
        'optimizer_name': 'bumps (amoeba)',
        'method_name': 'amoeba',
    }
    _default_chi_square_change_tolerance: ClassVar[float] = 1e-8
    _default_parameter_change_tolerance: ClassVar[float] = 1e-6
    url: str = 'https://bumps.readthedocs.io'

    type_info = TypeInfo(
        tag=MinimizerTypeEnum.BUMPS_AMOEBA,
        description='BUMPS library with Nelder-Mead simplex method',
    )
