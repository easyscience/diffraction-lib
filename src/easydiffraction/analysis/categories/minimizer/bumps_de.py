# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Persisted category for the BUMPS de minimizer."""

from __future__ import annotations

from typing import ClassVar

from easydiffraction.analysis.categories.minimizer.factory import MinimizerCategoryFactory
from easydiffraction.analysis.categories.minimizer.lsq_base import LeastSquaresMinimizerBase
from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum
from easydiffraction.core.metadata import TypeInfo


@MinimizerCategoryFactory.register
class BumpsDeMinimizer(LeastSquaresMinimizerBase):
    """Persisted settings for the BUMPS de minimizer."""

    _engine_metadata: ClassVar[dict[str, str]] = {
        'optimizer_name': 'bumps (de)',
        'method_name': 'de',
    }
    url: str = 'https://bumps.readthedocs.io'

    type_info = TypeInfo(
        tag=MinimizerTypeEnum.BUMPS_DE,
        description='BUMPS library with differential evolution method',
    )
