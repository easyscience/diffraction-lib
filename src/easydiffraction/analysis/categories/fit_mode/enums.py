# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Enumeration for fit-mode values."""

from __future__ import annotations

from enum import Enum


class FitModeEnum(str, Enum):
    """Fitting strategy for the analysis."""

    SINGLE = 'single'
    JOINT = 'joint'

    @classmethod
    def default(cls) -> FitModeEnum:
        return cls.SINGLE

    def description(self) -> str:
        if self is FitModeEnum.SINGLE:
            return 'Independent fitting of each experiment; no shared parameters'
        elif self is FitModeEnum.JOINT:
            return 'Simultaneous fitting of all experiments; some parameters are shared'
