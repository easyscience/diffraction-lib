# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Registry of supported background implementations.

This file exists to avoid circular imports between `base.py`
and specific background type implementations.
"""

from easydiffraction.experiments.category_collections.background_types.base import (
    BackgroundTypeEnum,
)
from easydiffraction.experiments.category_collections.background_types.chebyshev import (
    ChebyshevPolynomialBackground,
)
from easydiffraction.experiments.category_collections.background_types.line_segment import (
    LineSegmentBackground,
)

SUPPORTED_BACKGROUNDS = {
    BackgroundTypeEnum.LINE_SEGMENT: LineSegmentBackground,
    BackgroundTypeEnum.CHEBYSHEV: ChebyshevPolynomialBackground,
}
