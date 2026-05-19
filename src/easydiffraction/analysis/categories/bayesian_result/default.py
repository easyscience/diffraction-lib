# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Bayesian fit-result metadata category."""

from __future__ import annotations

from easydiffraction.analysis.categories.bayesian_result.factory import BayesianResultFactory
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.variable import BoolDescriptor
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import CifHandler


@BayesianResultFactory.register
class BayesianResult(CategoryItem):
    """Persisted Bayesian fit-result metadata."""

    _category_code = 'bayesian_result'

    type_info = TypeInfo(
        tag='default',
        description='Persisted Bayesian fit-result metadata',
    )

    def __init__(self) -> None:
        super().__init__()
        self._sampler_name = StringDescriptor(
            name='sampler_name',
            description='Name of the persisted Bayesian sampler.',
            value_spec=AttributeSpec(default='dream'),
            cif_handler=CifHandler(names=['_bayesian_result.sampler_name']),
        )
        self._point_estimate_name = StringDescriptor(
            name='point_estimate_name',
            description='Committed sampled point estimate name.',
            value_spec=AttributeSpec(default='best_sample'),
            cif_handler=CifHandler(names=['_bayesian_result.point_estimate_name']),
        )
        self._success = BoolDescriptor(
            name='success',
            description='Whether the persisted Bayesian fit produced usable results.',
            value_spec=AttributeSpec(default=False),
            cif_handler=CifHandler(names=['_bayesian_result.success']),
        )
        self._sampler_completed = BoolDescriptor(
            name='sampler_completed',
            description='Whether the sampler completed and returned posterior data.',
            value_spec=AttributeSpec(default=False),
            cif_handler=CifHandler(names=['_bayesian_result.sampler_completed']),
        )
        self._best_log_posterior = NumericDescriptor(
            name='best_log_posterior',
            description='Best log-posterior value reported by the sampler.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_bayesian_result.best_log_posterior']),
        )
        self._credible_interval_inner = NumericDescriptor(
            name='credible_interval_inner',
            description='Inner credible-interval level used in summaries.',
            value_spec=AttributeSpec(default=0.68),
            cif_handler=CifHandler(names=['_bayesian_result.credible_interval_inner']),
        )
        self._credible_interval_outer = NumericDescriptor(
            name='credible_interval_outer',
            description='Outer credible-interval level used in summaries.',
            value_spec=AttributeSpec(default=0.95),
            cif_handler=CifHandler(names=['_bayesian_result.credible_interval_outer']),
        )
        self._has_posterior_samples = BoolDescriptor(
            name='has_posterior_samples',
            description='Whether posterior samples were persisted.',
            value_spec=AttributeSpec(default=False),
            cif_handler=CifHandler(names=['_bayesian_result.has_posterior_samples']),
        )
        self._has_distribution_cache = BoolDescriptor(
            name='has_distribution_cache',
            description='Whether distribution-cache manifests were persisted.',
            value_spec=AttributeSpec(default=False),
            cif_handler=CifHandler(names=['_bayesian_result.has_distribution_cache']),
        )
        self._has_pair_cache = BoolDescriptor(
            name='has_pair_cache',
            description='Whether pair-cache manifests were persisted.',
            value_spec=AttributeSpec(default=False),
            cif_handler=CifHandler(names=['_bayesian_result.has_pair_cache']),
        )
        self._has_posterior_predictive = BoolDescriptor(
            name='has_posterior_predictive',
            description='Whether posterior predictive manifests were persisted.',
            value_spec=AttributeSpec(default=False),
            cif_handler=CifHandler(names=['_bayesian_result.has_posterior_predictive']),
        )
        self._sidecar_file = StringDescriptor(
            name='sidecar_file',
            description='Relative path to the persisted Bayesian HDF5 sidecar.',
            value_spec=AttributeSpec(default='results.h5'),
            cif_handler=CifHandler(names=['_bayesian_result.sidecar_file']),
        )

    @property
    def sampler_name(self) -> StringDescriptor:
        """Name of the persisted Bayesian sampler."""
        return self._sampler_name

    def _set_sampler_name(self, value: str) -> None:
        """Set the sampler name for internal callers."""
        self._sampler_name.value = value

    @property
    def point_estimate_name(self) -> StringDescriptor:
        """Committed sampled point estimate name."""
        return self._point_estimate_name

    def _set_point_estimate_name(self, value: str) -> None:
        """Set the point-estimate name for internal callers."""
        self._point_estimate_name.value = value

    @property
    def success(self) -> BoolDescriptor:
        """
        Whether the persisted Bayesian fit produced usable results.
        """
        return self._success

    def _set_success(self, *, value: bool) -> None:
        """Set the success flag for internal callers."""
        self._success.value = value

    @property
    def sampler_completed(self) -> BoolDescriptor:
        """Whether the sampler completed and returned posterior data."""
        return self._sampler_completed

    def _set_sampler_completed(self, *, value: bool) -> None:
        """Set the sampler-completed flag for internal callers."""
        self._sampler_completed.value = value

    @property
    def best_log_posterior(self) -> NumericDescriptor:
        """Best log-posterior value reported by the sampler."""
        return self._best_log_posterior

    def _set_best_log_posterior(self, value: float | None) -> None:
        """Set the best log-posterior for internal callers."""
        self._best_log_posterior.value = value

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
    def has_posterior_samples(self) -> BoolDescriptor:
        """Whether posterior samples were persisted."""
        return self._has_posterior_samples

    def _set_has_posterior_samples(self, *, value: bool) -> None:
        """Set the posterior-samples flag for internal callers."""
        self._has_posterior_samples.value = value

    @property
    def has_distribution_cache(self) -> BoolDescriptor:
        """Whether distribution-cache manifests were persisted."""
        return self._has_distribution_cache

    def _set_has_distribution_cache(self, *, value: bool) -> None:
        """Set the distribution-cache flag for internal callers."""
        self._has_distribution_cache.value = value

    @property
    def has_pair_cache(self) -> BoolDescriptor:
        """Whether pair-cache manifests were persisted."""
        return self._has_pair_cache

    def _set_has_pair_cache(self, *, value: bool) -> None:
        """Set the pair-cache flag for internal callers."""
        self._has_pair_cache.value = value

    @property
    def has_posterior_predictive(self) -> BoolDescriptor:
        """Whether posterior predictive manifests were persisted."""
        return self._has_posterior_predictive

    def _set_has_posterior_predictive(self, *, value: bool) -> None:
        """Set the posterior-predictive flag for internal callers."""
        self._has_posterior_predictive.value = value

    @property
    def sidecar_file(self) -> StringDescriptor:
        """Relative path to the persisted Bayesian HDF5 sidecar."""
        return self._sidecar_file

    def _set_sidecar_file(self, value: str) -> None:
        """Set the sidecar-file path for internal callers."""
        self._sidecar_file.value = value
