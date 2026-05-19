# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Bayesian convergence diagnostics category."""

from __future__ import annotations

from easydiffraction.analysis.categories.bayesian_convergence.factory import (
    BayesianConvergenceFactory,
)
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.variable import BoolDescriptor
from easydiffraction.core.variable import IntegerDescriptor
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.io.cif.handler import CifHandler


@BayesianConvergenceFactory.register
class BayesianConvergence(CategoryItem):
    """Persisted Bayesian convergence diagnostics."""

    _category_code = 'bayesian_convergence'

    type_info = TypeInfo(
        tag='default',
        description='Persisted Bayesian convergence diagnostics',
    )

    def __init__(self) -> None:
        super().__init__()
        self._converged = BoolDescriptor(
            name='converged',
            description='Whether the Bayesian fit met convergence criteria.',
            value_spec=AttributeSpec(default=False),
            cif_handler=CifHandler(names=['_bayesian_convergence.converged']),
        )
        self._max_r_hat = NumericDescriptor(
            name='max_r_hat',
            description='Maximum rank-normalized split-R-hat across parameters.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_bayesian_convergence.max_r_hat']),
        )
        self._min_ess_bulk = NumericDescriptor(
            name='min_ess_bulk',
            description='Minimum bulk effective sample size across parameters.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_bayesian_convergence.min_ess_bulk']),
        )
        self._n_draws = IntegerDescriptor(
            name='n_draws',
            description='Number of stored posterior draws.',
            value_spec=AttributeSpec(default=0),
            cif_handler=CifHandler(names=['_bayesian_convergence.n_draws']),
        )
        self._n_chains = IntegerDescriptor(
            name='n_chains',
            description='Number of stored posterior chains.',
            value_spec=AttributeSpec(default=0),
            cif_handler=CifHandler(names=['_bayesian_convergence.n_chains']),
        )
        self._n_parameters = IntegerDescriptor(
            name='n_parameters',
            description='Number of sampled parameters.',
            value_spec=AttributeSpec(default=0),
            cif_handler=CifHandler(names=['_bayesian_convergence.n_parameters']),
        )

    @property
    def converged(self) -> BoolDescriptor:
        """Whether the Bayesian fit met convergence criteria."""
        return self._converged

    def _set_converged(self, *, value: bool) -> None:
        """Set the convergence flag for internal callers."""
        self._converged.value = value

    @property
    def max_r_hat(self) -> NumericDescriptor:
        """Maximum rank-normalized split-R-hat across parameters."""
        return self._max_r_hat

    def _set_max_r_hat(self, value: float | None) -> None:
        """Set the maximum R-hat for internal callers."""
        self._max_r_hat.value = value

    @property
    def min_ess_bulk(self) -> NumericDescriptor:
        """Minimum bulk effective sample size across parameters."""
        return self._min_ess_bulk

    def _set_min_ess_bulk(self, value: float | None) -> None:
        """Set the minimum ESS bulk for internal callers."""
        self._min_ess_bulk.value = value

    @property
    def n_draws(self) -> IntegerDescriptor:
        """Number of stored posterior draws."""
        return self._n_draws

    def _set_n_draws(self, value: int) -> None:
        """Set the draw count for internal callers."""
        self._n_draws.value = value

    @property
    def n_chains(self) -> IntegerDescriptor:
        """Number of stored posterior chains."""
        return self._n_chains

    def _set_n_chains(self, value: int) -> None:
        """Set the chain count for internal callers."""
        self._n_chains.value = value

    @property
    def n_parameters(self) -> IntegerDescriptor:
        """Number of sampled parameters."""
        return self._n_parameters

    def _set_n_parameters(self, value: int) -> None:
        """Set the sampled-parameter count for internal callers."""
        self._n_parameters.value = value
