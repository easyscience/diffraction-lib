# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Enumeration types used by analysis components."""

from __future__ import annotations

from enum import Enum
from enum import StrEnum


class FitModeEnum(StrEnum):
    """Fitting mode for the analysis."""

    SINGLE = 'single'
    JOINT = 'joint'
    SEQUENTIAL = 'sequential'

    @classmethod
    def default(cls) -> FitModeEnum:
        """Return the default fit mode (SINGLE)."""
        return cls.SINGLE

    def description(self) -> str:
        """Return a human-readable description of this fit mode."""
        if self is FitModeEnum.SINGLE:
            return 'Fit one experiment at a time.'
        if self is FitModeEnum.JOINT:
            return 'Fit several experiments together with shared parameters.'
        if self is FitModeEnum.SEQUENTIAL:
            return 'Fit one experiment against a series of data files.'
        return ''


class FitResultKindEnum(str, Enum):
    """Persisted kind of the latest fit-result projection."""

    DETERMINISTIC = 'deterministic'
    BAYESIAN = 'bayesian'

    @classmethod
    def default(cls) -> FitResultKindEnum:
        """Return the default persisted fit-result kind."""
        return cls.DETERMINISTIC


class FitCorrelationSourceEnum(str, Enum):
    """Source of a persisted fit-parameter correlation summary."""

    DETERMINISTIC = 'deterministic'
    POSTERIOR = 'posterior'

    @classmethod
    def default(cls) -> FitCorrelationSourceEnum:
        """Return the default persisted correlation source."""
        return cls.DETERMINISTIC
