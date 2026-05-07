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
    BUMPS_DREAM = 'bumps (dream)'
    BUMPS_AMOEBA = 'bumps (amoeba)'
    BUMPS_DE = 'bumps (de)'

    @classmethod
    def default(cls) -> MinimizerTypeEnum:
        """Return the default minimizer type."""
        return cls.LMFIT_LEASTSQ

    def description(self) -> str:
        """
        Return a human-readable description of this minimizer type.
        """
        descriptions = {
            MinimizerTypeEnum.LMFIT: (
                'LMFIT library using the default Levenberg-Marquardt least squares method'
            ),
            MinimizerTypeEnum.LMFIT_LEASTSQ: (
                'LMFIT library with Levenberg-Marquardt least squares method'
            ),
            MinimizerTypeEnum.LMFIT_LEAST_SQUARES: (
                "LMFIT library with SciPy's trust region reflective algorithm"
            ),
            MinimizerTypeEnum.DFOLS: (
                'DFO-LS library for derivative-free least-squares optimization'
            ),
            MinimizerTypeEnum.BUMPS: (
                'BUMPS library using the default Levenberg-Marquardt method'
            ),
            MinimizerTypeEnum.BUMPS_LM: ('BUMPS library with Levenberg-Marquardt method'),
            MinimizerTypeEnum.BUMPS_DREAM: ('BUMPS library with DREAM Bayesian sampling'),
            MinimizerTypeEnum.BUMPS_AMOEBA: ('BUMPS library with Nelder-Mead simplex method'),
            MinimizerTypeEnum.BUMPS_DE: ('BUMPS library with differential evolution method'),
        }
        return descriptions.get(self, '')
