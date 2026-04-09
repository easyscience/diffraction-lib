# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Enumeration for fit-mode values."""

from __future__ import annotations

from enum import StrEnum


class FitModeEnum(StrEnum):
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
        if self is FitModeEnum.JOINT:
            return 'Simultaneous fitting of all experiments; some parameters are shared'
        return None
