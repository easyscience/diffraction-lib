# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Enumerations for background model types and estimation methods."""

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


class BackgroundEstimatorMethodEnum(StrEnum):
    """Supported automatic background-estimation methods."""

    AUTO = 'auto'
    SNIP = 'snip'
    ARPLS = 'arpls'
    FABC = 'fabc'

    @classmethod
    def default(cls) -> BackgroundEstimatorMethodEnum:
        """Return the default estimation method."""
        return cls.AUTO

    def description(self) -> str:
        """Human-friendly description for the enum value."""
        if self is BackgroundEstimatorMethodEnum.AUTO:
            return 'Let the library choose (currently arPLS)'
        if self is BackgroundEstimatorMethodEnum.SNIP:
            return 'SNIP iterative peak-clipping baseline'
        if self is BackgroundEstimatorMethodEnum.ARPLS:
            return 'Asymmetrically reweighted penalized least squares'
        if self is BackgroundEstimatorMethodEnum.FABC:
            return 'Fully automatic baseline correction (classification)'
        return None
