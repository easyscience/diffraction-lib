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
        return ''
