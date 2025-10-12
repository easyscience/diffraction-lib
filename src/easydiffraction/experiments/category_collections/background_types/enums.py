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
