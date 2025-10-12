# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Background collection entry point (public facade).

End users should import Background classes from this module. Internals
live under the package
`easydiffraction.experiments.category_collections.background_types`
and are re-exported here for a stable and readable API.
"""

from easydiffraction.experiments.collections.background_types.base import BackgroundBase
from easydiffraction.experiments.collections.background_types.base import BackgroundFactory
from easydiffraction.experiments.collections.background_types.base import BackgroundTypeEnum
from easydiffraction.experiments.collections.background_types.base import Point
from easydiffraction.experiments.collections.background_types.base import PolynomialTerm
from easydiffraction.experiments.collections.background_types.chebyshev import (
    ChebyshevPolynomialBackground,
)
from easydiffraction.experiments.collections.background_types.line_segment import (
    LineSegmentBackground,
)

__all__ = [
    'BackgroundBase',
    'BackgroundFactory',
    'BackgroundTypeEnum',
    'Point',
    'PolynomialTerm',
    'LineSegmentBackground',
    'ChebyshevPolynomialBackground',
]
