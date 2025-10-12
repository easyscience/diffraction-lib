# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Background collection entry point (public facade).

End users should import Background classes from this module. Internals
live under the package
`easydiffraction.experiments.category_collections.background_types`
and are re-exported here for a stable and readable API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Optional

from easydiffraction.experiments.category_collections.background_types.enums import (
    BackgroundTypeEnum,
)

if TYPE_CHECKING:
    from easydiffraction.experiments.category_collections.background_types import BackgroundBase


class BackgroundFactory:
    BT = BackgroundTypeEnum

    @classmethod
    def _supported_map(cls) -> dict:
        # Lazy import to avoid circulars
        from easydiffraction.experiments.category_collections.background_types.chebyshev import (
            ChebyshevPolynomialBackground,
        )
        from easydiffraction.experiments.category_collections.background_types.line_segment import (
            LineSegmentBackground,
        )

        return {
            cls.BT.LINE_SEGMENT: LineSegmentBackground,
            cls.BT.CHEBYSHEV: ChebyshevPolynomialBackground,
        }

    @classmethod
    def create(
        cls,
        background_type: Optional[BackgroundTypeEnum] = None,
    ) -> BackgroundBase:
        if background_type is None:
            background_type = BackgroundTypeEnum.default()

        supported = cls._supported_map()
        if background_type not in supported:
            supported_types = list(supported.keys())

            raise ValueError(
                f"Unsupported background type: '{background_type}'.\n"
                f' Supported background types: {[bt.value for bt in supported_types]}'
            )

        background_class = supported[background_type]
        return background_class()
