# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Enumerations for background model types."""

from __future__ import annotations

from enum import StrEnum


# TODO: Consider making EnumBase class with: default, description, ...
class BackgroundTypeEnum(StrEnum):
    """Supported background model types."""

    LINE_SEGMENT = 'line-segment'
    CHEBYSHEV = 'chebyshev'

    @classmethod
    def default(cls) -> BackgroundTypeEnum:
        """Return a default background type."""
        return cls.LINE_SEGMENT

    def description(self) -> str:
        """Human-friendly description for the enum value."""
        if self is BackgroundTypeEnum.LINE_SEGMENT:
            return 'Linear interpolation between points'
        if self is BackgroundTypeEnum.CHEBYSHEV:
            return 'Chebyshev polynomial background'
        return None
