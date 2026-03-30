# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Enumerations for fit-mode and fit-verbosity values."""

from __future__ import annotations

from enum import Enum


class FitModeEnum(str, Enum):
    """Fitting strategy for the analysis."""

    SINGLE = 'single'
    JOINT = 'joint'

    @classmethod
    def default(cls) -> FitModeEnum:
        """Return the default fit mode (SINGLE)."""
        return cls.SINGLE

    def description(self) -> str:
        """Return a human-readable description of this fit mode."""
        if self is FitModeEnum.SINGLE:
            return 'Independent fitting of each experiment; no shared parameters'
        elif self is FitModeEnum.JOINT:
            return 'Simultaneous fitting of all experiments; some parameters are shared'


class FitVerbosityEnum(str, Enum):
    """Console output verbosity during fitting."""

    FULL = 'full'
    SHORT = 'short'
    SILENT = 'silent'

    @classmethod
    def default(cls) -> FitVerbosityEnum:
        """Return the default verbosity (FULL)."""
        return cls.FULL
