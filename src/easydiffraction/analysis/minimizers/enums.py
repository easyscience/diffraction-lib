# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Enumerations for minimizer types."""

from __future__ import annotations

from enum import StrEnum


class MinimizerTypeEnum(StrEnum):
    """Supported minimizer types."""

    LMFIT = 'lmfit'
    LMFIT_LEASTSQ = 'lmfit (leastsq)'
    LMFIT_LEAST_SQUARES = 'lmfit (least_squares)'
    DFOLS = 'dfols'
    BUMPS = 'bumps'
    BUMPS_LM = 'bumps (lm)'
    BUMPS_AMOEBA = 'bumps (amoeba)'
    BUMPS_DE = 'bumps (de)'

    @classmethod
    def default(cls) -> MinimizerTypeEnum:
        """Return the default minimizer type."""
        return cls.LMFIT

    def description(self) -> str:
        """
        Return a human-readable description of this minimizer type.
        """
        if self is MinimizerTypeEnum.LMFIT:
            return 'LMFIT library using the default Levenberg-Marquardt least squares method'
        if self is MinimizerTypeEnum.LMFIT_LEASTSQ:
            return 'LMFIT library with Levenberg-Marquardt least squares method'
        if self is MinimizerTypeEnum.LMFIT_LEAST_SQUARES:
            return "LMFIT library with SciPy's trust region reflective algorithm"
        if self is MinimizerTypeEnum.DFOLS:
            return 'DFO-LS library for derivative-free least-squares optimization'
        if self is MinimizerTypeEnum.BUMPS:
            return 'BUMPS library using the default Levenberg-Marquardt method'
        if self is MinimizerTypeEnum.BUMPS_LM:
            return 'BUMPS library with Levenberg-Marquardt method'
        if self is MinimizerTypeEnum.BUMPS_AMOEBA:
            return 'BUMPS library with Nelder-Mead simplex method'
        if self is MinimizerTypeEnum.BUMPS_DE:
            return 'BUMPS library with differential evolution method'
        return ''
