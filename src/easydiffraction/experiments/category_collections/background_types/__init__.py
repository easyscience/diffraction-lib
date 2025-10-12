# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Internal implementation package for the Background category.

Public consumers should import from the entry point
`easydiffraction.experiments.category_collections.background`.

Re-exports are provided for contributor discoverability and focused
tests.
"""

from easydiffraction.experiments.category_collections.background import BackgroundFactory
from easydiffraction.experiments.category_collections.background_types.base import BackgroundBase
from easydiffraction.experiments.category_collections.background_types.chebyshev import (
    ChebyshevPolynomialBackground,
)
from easydiffraction.experiments.category_collections.background_types.chebyshev import (
    PolynomialTerm,
)
from easydiffraction.experiments.category_collections.background_types.enums import (
    BackgroundTypeEnum,
)
from easydiffraction.experiments.category_collections.background_types.line_segment import (
    LineSegmentBackground,
)
from easydiffraction.experiments.category_collections.background_types.line_segment import Point

__all__ = [
    'BackgroundBase',
    'BackgroundTypeEnum',
    'Point',
    'PolynomialTerm',
    'LineSegmentBackground',
    'ChebyshevPolynomialBackground',
    'BackgroundFactory',
]
