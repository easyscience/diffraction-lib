# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Bayesian fit-result category."""

from __future__ import annotations

from typing import ClassVar

from easydiffraction.analysis.categories.fit_result.base import FitResultBase
from easydiffraction.analysis.categories.fit_result.factory import FitResultFactory
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.variable import BoolDescriptor
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import CifHandler


@FitResultFactory.register
class BayesianFitResult(FitResultBase):
    """Persisted Bayesian fit-result metadata."""

    type_info = TypeInfo(
        tag='bayesian',
        description='Persisted Bayesian fit-result metadata',
    )
    _result_descriptor_names: ClassVar[tuple[str, ...]] = (
        *FitResultBase._result_descriptor_names,
        'point_estimate_name',
        'sampler_completed',
        'credible_interval_inner',
        'credible_interval_outer',
        'acceptance_rate_mean',
        'gelman_rubin_max',
        'effective_sample_size_min',
        'best_log_posterior',
    )
    _expected_descriptor_names: ClassVar[tuple[str, ...]] = _result_descriptor_names

    def __init__(self) -> None:
        super().__init__()
        self._point_estimate_name = self._point_estimate_name_descriptor()
        self._sampler_completed = self._sampler_completed_descriptor()
        self._credible_interval_inner = self._credible_interval_inner_descriptor()
        self._credible_interval_outer = self._credible_interval_outer_descriptor()
        self._acceptance_rate_mean = self._acceptance_rate_mean_descriptor()
        self._gelman_rubin_max = self._gelman_rubin_max_descriptor()
        self._effective_sample_size_min = self._effective_sample_size_min_descriptor()
        self._best_log_posterior = self._best_log_posterior_descriptor()

    @staticmethod
    def _point_estimate_name_descriptor() -> StringDescriptor:
        """Create a point-estimate-name descriptor."""
        return StringDescriptor(
            name='point_estimate_name',
            description='Committed sampled point estimate name.',
            value_spec=AttributeSpec(default='best_sample'),
            cif_handler=CifHandler(names=['_fit_result.point_estimate_name']),
        )

    @staticmethod
    def _sampler_completed_descriptor() -> BoolDescriptor:
        """Create a sampler-completed descriptor."""
        return BoolDescriptor(
            name='sampler_completed',
            description='Whether the sampler completed and returned posterior data.',
            value_spec=AttributeSpec(default=False),
            cif_handler=CifHandler(names=['_fit_result.sampler_completed']),
        )

    @staticmethod
    def _credible_interval_inner_descriptor() -> NumericDescriptor:
        """Create an inner credible-interval descriptor."""
        return NumericDescriptor(
            name='credible_interval_inner',
            description='Inner credible-interval level used in summaries.',
            value_spec=AttributeSpec(default=0.68),
            cif_handler=CifHandler(names=['_fit_result.credible_interval_inner']),
        )

    @staticmethod
    def _credible_interval_outer_descriptor() -> NumericDescriptor:
        """Create an outer credible-interval descriptor."""
        return NumericDescriptor(
            name='credible_interval_outer',
            description='Outer credible-interval level used in summaries.',
            value_spec=AttributeSpec(default=0.95),
            cif_handler=CifHandler(names=['_fit_result.credible_interval_outer']),
        )

    @staticmethod
    def _acceptance_rate_mean_descriptor() -> NumericDescriptor:
        """Create an acceptance-rate descriptor."""
        return NumericDescriptor(
            name='acceptance_rate_mean',
            description='Mean sampler acceptance rate.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_fit_result.acceptance_rate_mean']),
        )

    @staticmethod
    def _gelman_rubin_max_descriptor() -> NumericDescriptor:
        """Create a Gelman-Rubin descriptor."""
        return NumericDescriptor(
            name='gelman_rubin_max',
            description='Maximum rank-normalized split R-hat.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_fit_result.gelman_rubin_max']),
        )

    @staticmethod
    def _effective_sample_size_min_descriptor() -> NumericDescriptor:
        """Create an effective-sample-size descriptor."""
        return NumericDescriptor(
            name='effective_sample_size_min',
            description='Minimum bulk effective sample size.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_fit_result.effective_sample_size_min']),
        )

    @staticmethod
    def _best_log_posterior_descriptor() -> NumericDescriptor:
        """Create a best-log-posterior descriptor."""
        return NumericDescriptor(
            name='best_log_posterior',
            description='Best log-posterior value found.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_fit_result.best_log_posterior']),
        )

    @property
    def point_estimate_name(self) -> StringDescriptor:
        """Committed sampled point estimate name."""
        return self._point_estimate_name

    def _set_point_estimate_name(self, value: str) -> None:
        """Set the point-estimate name for internal callers."""
        self._point_estimate_name.value = value

    @property
    def sampler_completed(self) -> BoolDescriptor:
        """Whether the sampler completed and returned posterior data."""
        return self._sampler_completed

    def _set_sampler_completed(self, *, value: bool) -> None:
        """Set the sampler-completed flag for internal callers."""
        self._sampler_completed.value = value

    @property
    def credible_interval_inner(self) -> NumericDescriptor:
        """Inner credible-interval level used in summaries."""
        return self._credible_interval_inner

    def _set_credible_interval_inner(self, value: float) -> None:
        """
        Set the inner credible-interval level for internal callers.
        """
        self._credible_interval_inner.value = value

    @property
    def credible_interval_outer(self) -> NumericDescriptor:
        """Outer credible-interval level used in summaries."""
        return self._credible_interval_outer

    def _set_credible_interval_outer(self, value: float) -> None:
        """
        Set the outer credible-interval level for internal callers.
        """
        self._credible_interval_outer.value = value

    @property
    def acceptance_rate_mean(self) -> NumericDescriptor:
        """Mean sampler acceptance rate."""
        return self._acceptance_rate_mean

    def _set_acceptance_rate_mean(self, value: float | None) -> None:
        """Set the acceptance-rate mean for internal callers."""
        self._acceptance_rate_mean.value = value

    @property
    def gelman_rubin_max(self) -> NumericDescriptor:
        """Maximum rank-normalized split R-hat."""
        return self._gelman_rubin_max

    def _set_gelman_rubin_max(self, value: float | None) -> None:
        """Set the maximum R-hat for internal callers."""
        self._gelman_rubin_max.value = value

    @property
    def effective_sample_size_min(self) -> NumericDescriptor:
        """Minimum bulk effective sample size."""
        return self._effective_sample_size_min

    def _set_effective_sample_size_min(self, value: float | None) -> None:
        """
        Set the minimum effective sample size for internal callers.
        """
        self._effective_sample_size_min.value = value

    @property
    def best_log_posterior(self) -> NumericDescriptor:
        """Best log-posterior value found."""
        return self._best_log_posterior

    def _set_best_log_posterior(self, value: float | None) -> None:
        """Set the best log-posterior for internal callers."""
        self._best_log_posterior.value = value
