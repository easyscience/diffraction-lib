# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for common fit-result status metadata."""

from __future__ import annotations


def test_fit_result_base_defaults_unknown_result_values_to_none():
    from easydiffraction.analysis.categories.fit_result.base import FitResultBase
    from easydiffraction.analysis.enums import FitResultKindEnum

    fit_result = FitResultBase()

    assert fit_result.result_kind.value == FitResultKindEnum.DETERMINISTIC.value
    assert fit_result.success.value is None
    assert fit_result.message.value is None
    assert fit_result.iterations.value is None
    assert fit_result.fitting_time.value is None
    assert fit_result.reduced_chi_square.value is None


def test_fit_result_base_reset_restores_declared_defaults():
    from easydiffraction.analysis.categories.fit_result.base import FitResultBase

    fit_result = FitResultBase()
    fit_result._set_result_kind('bayesian')
    fit_result._set_success(value=True)
    fit_result._set_message('Fit converged')
    fit_result._set_iterations(14)
    fit_result._set_fitting_time(0.25)
    fit_result._set_reduced_chi_square(1.2)

    fit_result._reset_result_descriptors()

    assert fit_result.result_kind.value == 'deterministic'
    assert fit_result.success.value is None
    assert fit_result.message.value is None
    assert fit_result.iterations.value is None
    assert fit_result.fitting_time.value is None
    assert fit_result.reduced_chi_square.value is None


def test_fit_result_base_serializes_unknown_values_as_cif_unknowns():
    from easydiffraction.analysis.categories.fit_result.base import FitResultBase

    cif_text = FitResultBase().as_cif

    assert '_fit_result.success ?' in cif_text
    assert '_fit_result.message ?' in cif_text
    assert '_fit_result.iterations ?' in cif_text
