# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Enumeration types used by analysis components."""

from __future__ import annotations

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


class FitResultKindEnum(StrEnum):
    """Persisted kind of the latest fit-result projection."""

    DETERMINISTIC = 'deterministic'
    BAYESIAN = 'bayesian'

    @classmethod
    def default(cls) -> FitResultKindEnum:
        """Return the default persisted fit-result kind."""
        return cls.DETERMINISTIC

    def description(self) -> str:
        """
        Return a human-readable description of this fit-result kind.
        """
        if self is FitResultKindEnum.DETERMINISTIC:
            return 'Least-squares (point-estimate) fit result.'
        if self is FitResultKindEnum.BAYESIAN:
            return 'Bayesian (posterior-sampling) fit result.'
        return ''


class FitCorrelationSourceEnum(StrEnum):
    """Source of a persisted fit-parameter correlation summary."""

    DETERMINISTIC = 'deterministic'
    POSTERIOR = 'posterior'

    @classmethod
    def default(cls) -> FitCorrelationSourceEnum:
        """Return the default persisted correlation source."""
        return cls.DETERMINISTIC

    def description(self) -> str:
        """
        Return a human-readable description of this correlation source.
        """
        if self is FitCorrelationSourceEnum.DETERMINISTIC:
            return 'Correlations from the least-squares covariance matrix.'
        if self is FitCorrelationSourceEnum.POSTERIOR:
            return 'Correlations from posterior samples.'
        return ''


class SoftwareRoleEnum(StrEnum):
    """Role of a software package in the latest fit."""

    FRAMEWORK = 'framework'
    CALCULATOR = 'calculator'
    MINIMIZER = 'minimizer'

    @classmethod
    def default(cls) -> SoftwareRoleEnum:
        """Return the default software role."""
        return cls.FRAMEWORK

    def description(self) -> str:
        """Return a human-readable description of this role."""
        if self is SoftwareRoleEnum.FRAMEWORK:
            return 'EasyDiffraction framework.'
        if self is SoftwareRoleEnum.CALCULATOR:
            return 'Calculation engine.'
        if self is SoftwareRoleEnum.MINIMIZER:
            return 'Minimization engine.'
        return ''
