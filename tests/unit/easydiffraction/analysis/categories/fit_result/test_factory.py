# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for fit-result factory registration and pairing."""

from __future__ import annotations


def test_fit_result_factory_creates_registered_family_classes():
    import easydiffraction.analysis.categories.fit_result  # noqa: F401
    from easydiffraction.analysis.categories.fit_result.bayesian import BayesianFitResult
    from easydiffraction.analysis.categories.fit_result.factory import FitResultFactory
    from easydiffraction.analysis.categories.fit_result.lsq import LeastSquaresFitResult

    assert isinstance(FitResultFactory.create('least_squares'), LeastSquaresFitResult)
    assert isinstance(FitResultFactory.create('bayesian'), BayesianFitResult)


def test_minimizer_bases_declare_paired_fit_result_classes():
    from easydiffraction.analysis.categories.fit_result.bayesian import BayesianFitResult
    from easydiffraction.analysis.categories.fit_result.lsq import LeastSquaresFitResult
    from easydiffraction.analysis.categories.minimizer.bayesian_base import BayesianMinimizerBase
    from easydiffraction.analysis.categories.minimizer.lsq_base import LeastSquaresMinimizerBase

    assert LeastSquaresMinimizerBase._fit_result_class is LeastSquaresFitResult
    assert BayesianMinimizerBase._fit_result_class is BayesianFitResult
