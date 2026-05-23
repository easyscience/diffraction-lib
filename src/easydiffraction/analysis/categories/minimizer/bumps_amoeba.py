# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Persisted category for the BUMPS amoeba minimizer."""

from __future__ import annotations

from easydiffraction.analysis.categories.minimizer.factory import MinimizerCategoryFactory
from easydiffraction.analysis.categories.minimizer.lsq_base import (
    LeastSquaresMinimizerBase,
)
from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum
from easydiffraction.core.metadata import TypeInfo

DEFAULT_MAX_ITERATIONS = 1000

@MinimizerCategoryFactory.register
class BumpsAmoebaMinimizer(LeastSquaresMinimizerBase):
    """Persisted settings for the BUMPS amoeba minimizer."""

    type_info = TypeInfo(
        tag=MinimizerTypeEnum.BUMPS_AMOEBA,
        description='BUMPS library with Nelder-Mead simplex method',
    )

    def __init__(self) -> None:
        super().__init__()
        self._max_iterations = self._max_iterations_descriptor(DEFAULT_MAX_ITERATIONS)
        self._optimizer_name = self._string_result_descriptor(
            'optimizer_name',
            'Name of the persisted deterministic optimizer.',
        )
        self._method_name = self._string_result_descriptor(
            'method_name',
            'Method name of the persisted deterministic optimizer.',
        )
        self._objective_name = self._string_result_descriptor(
            'objective_name',
            'Objective function name for the persisted deterministic fit.',
        )
        self._objective_value = self._numeric_result_descriptor(
            'objective_value',
            'Objective value for the persisted deterministic fit.',
        )
        self._n_data_points = self._integer_result_descriptor(
            'n_data_points',
            'Number of data points used in the persisted deterministic fit.',
        )
        self._n_parameters = self._integer_result_descriptor(
            'n_parameters',
            'Number of parameters considered in the persisted deterministic fit.',
        )
        self._n_free_parameters = self._integer_result_descriptor(
            'n_free_parameters',
            'Number of free parameters in the persisted deterministic fit.',
        )
        self._degrees_of_freedom = self._integer_result_descriptor(
            'degrees_of_freedom',
            'Degrees of freedom for the persisted deterministic fit.',
        )
        self._covariance_available = self._bool_result_descriptor(
            'covariance_available',
            'Whether covariance was available for the persisted deterministic fit.',
        )
        self._correlation_available = self._bool_result_descriptor(
            'correlation_available',
            'Whether correlations were available for the persisted deterministic fit.',
        )
        self._runtime_seconds = self._numeric_result_descriptor(
            'runtime_seconds',
            'Runtime in seconds for the persisted deterministic fit.',
        )
        self._iterations_performed = self._integer_result_descriptor(
            'iterations_performed',
            'Number of iterations performed by the persisted deterministic fit.',
        )
        self._exit_reason = self._string_result_descriptor(
            'exit_reason',
            'Backend exit reason for the persisted deterministic fit.',
        )
