# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from enum import Enum


class BackgroundTypeEnum(str, Enum):
    LINE_SEGMENT = 'line-segment'
    CHEBYSHEV = 'chebyshev polynomial'

    @classmethod
    def default(cls) -> 'BackgroundTypeEnum':
        return cls.LINE_SEGMENT

    def description(self) -> str:
        if self is BackgroundTypeEnum.LINE_SEGMENT:
            return 'Linear interpolation between points'
        elif self is BackgroundTypeEnum.CHEBYSHEV:
            return 'Chebyshev polynomial background'
