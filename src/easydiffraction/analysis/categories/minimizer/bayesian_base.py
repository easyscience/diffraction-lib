# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Behavior helpers for Bayesian minimizer categories."""

from __future__ import annotations

from typing import ClassVar

from easydiffraction.analysis.categories.fit_result.bayesian import BayesianFitResult
from easydiffraction.analysis.categories.minimizer.base import MinimizerCategoryBase
from easydiffraction.analysis.minimizers.enums import InitializationMethodEnum
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import MembershipValidator
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.variable import BoolDescriptor
from easydiffraction.core.variable import IntegerDescriptor
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import CifHandler


class BayesianMinimizerBase(MinimizerCategoryBase):
    """Shared behavior for Bayesian minimizer categories."""

    _fit_result_class: ClassVar[type] = BayesianFitResult
    _expected_descriptor_names: ClassVar[tuple[str, ...]] = (
        'sampling_steps',
        'burn_in_steps',
        'thinning_interval',
        'population_size',
        'parallel_workers',
        'initialization_method',
        'random_seed',
        'runtime_seconds',
        'point_estimate_name',
        'sampler_completed',
        'credible_interval_inner',
        'credible_interval_outer',
        'acceptance_rate_mean',
        'gelman_rubin_max',
        'effective_sample_size_min',
        'best_log_posterior',
    )
    _native_key_map: ClassVar[dict[str, str]] = {
        'sampling_steps': 'steps',
        'burn_in_steps': 'burn',
        'thinning_interval': 'thin',
        'population_size': 'pop',
        'parallel_workers': 'parallel',
        'initialization_method': 'init',
        'random_seed': 'random_seed',
    }
    _setting_descriptor_names: ClassVar[tuple[str, ...]] = (
        'sampling_steps',
        'burn_in_steps',
        'thinning_interval',
        'population_size',
        'parallel_workers',
        'initialization_method',
        'random_seed',
    )
    _result_descriptor_names: ClassVar[tuple[str, ...]] = (
        'runtime_seconds',
        'point_estimate_name',
        'sampler_completed',
        'credible_interval_inner',
        'credible_interval_outer',
        'acceptance_rate_mean',
        'gelman_rubin_max',
        'effective_sample_size_min',
        'best_log_posterior',
    )
    _supported_initialization_methods: ClassVar[tuple[InitializationMethodEnum, ...]] = (
        InitializationMethodEnum.LATIN_HYPERCUBE,
    )
    _native_initialization_methods: ClassVar[dict[InitializationMethodEnum, str]] = {
        InitializationMethodEnum.LATIN_HYPERCUBE: 'lhs',
    }

    def _native_kwargs(self) -> dict[str, object]:
        """Return backend keyword arguments keyed by native names."""
        kwargs = super()._native_kwargs()
        if 'init' not in kwargs:
            return kwargs
        method = InitializationMethodEnum(str(kwargs['init']))
        kwargs['init'] = self._native_initialization_methods[method]
        return kwargs

    @staticmethod
    def _sampling_steps_descriptor(default: int) -> IntegerDescriptor:
        """Create a sampling-steps descriptor."""
        return IntegerDescriptor(
            name='sampling_steps',
            description='Total sampler iterations per chain.',
            value_spec=AttributeSpec(default=default, validator=RangeValidator(ge=1)),
            cif_handler=CifHandler(names=['_minimizer.sampling_steps']),
        )

    @staticmethod
    def _burn_in_steps_descriptor(default: int) -> IntegerDescriptor:
        """Create a burn-in descriptor."""
        return IntegerDescriptor(
            name='burn_in_steps',
            description='Sampler iterations discarded as warm-up.',
            value_spec=AttributeSpec(default=default, validator=RangeValidator(ge=0)),
            cif_handler=CifHandler(names=['_minimizer.burn_in_steps']),
        )

    @staticmethod
    def _thinning_interval_descriptor(default: int) -> IntegerDescriptor:
        """Create a thinning-interval descriptor."""
        return IntegerDescriptor(
            name='thinning_interval',
            description='Sampler thinning interval.',
            value_spec=AttributeSpec(default=default, validator=RangeValidator(ge=1)),
            cif_handler=CifHandler(names=['_minimizer.thinning_interval']),
        )

    @staticmethod
    def _population_size_descriptor(default: int) -> IntegerDescriptor:
        """Create a population-size descriptor."""
        return IntegerDescriptor(
            name='population_size',
            description='Number of chains or walkers.',
            value_spec=AttributeSpec(default=default, validator=RangeValidator(ge=1)),
            cif_handler=CifHandler(names=['_minimizer.population_size']),
        )

    @staticmethod
    def _parallel_workers_descriptor(default: int) -> IntegerDescriptor:
        """Create a parallel-workers descriptor."""
        return IntegerDescriptor(
            name='parallel_workers',
            description='Worker count; 0 uses all available CPUs.',
            value_spec=AttributeSpec(default=default, validator=RangeValidator(ge=0)),
            cif_handler=CifHandler(names=['_minimizer.parallel_workers']),
        )

    @classmethod
    def _initialization_method_descriptor(cls) -> StringDescriptor:
        """Create an initialization-method descriptor."""
        allowed = [member.value for member in cls._supported_initialization_methods]
        return StringDescriptor(
            name='initialization_method',
            description='Sampler initialization method.',
            value_spec=AttributeSpec(
                default=InitializationMethodEnum.LATIN_HYPERCUBE.value,
                validator=MembershipValidator(allowed=allowed),
            ),
            cif_handler=CifHandler(names=['_minimizer.initialization_method']),
        )

    @staticmethod
    def _random_seed_descriptor() -> IntegerDescriptor:
        """Create a random-seed descriptor."""
        return IntegerDescriptor(
            name='random_seed',
            description='Random seed; None uses a system-derived seed.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_minimizer.random_seed']),
        )

    @staticmethod
    def _runtime_seconds_descriptor() -> NumericDescriptor:
        """Create a runtime-seconds descriptor."""
        return NumericDescriptor(
            name='runtime_seconds',
            description='Wall time of the fit in seconds.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_minimizer.runtime_seconds']),
        )

    @staticmethod
    def _point_estimate_name_descriptor() -> StringDescriptor:
        """Create a point-estimate-name descriptor."""
        return StringDescriptor(
            name='point_estimate_name',
            description='Committed sampled point estimate name.',
            value_spec=AttributeSpec(default='best_sample'),
            cif_handler=CifHandler(names=['_minimizer.point_estimate_name']),
        )

    @staticmethod
    def _sampler_completed_descriptor() -> BoolDescriptor:
        """Create a sampler-completed descriptor."""
        return BoolDescriptor(
            name='sampler_completed',
            description='Whether the sampler completed and returned posterior data.',
            value_spec=AttributeSpec(default=False),
            cif_handler=CifHandler(names=['_minimizer.sampler_completed']),
        )

    @staticmethod
    def _credible_interval_inner_descriptor() -> NumericDescriptor:
        """Create an inner credible-interval descriptor."""
        return NumericDescriptor(
            name='credible_interval_inner',
            description='Inner credible-interval level used in summaries.',
            value_spec=AttributeSpec(default=0.68),
            cif_handler=CifHandler(names=['_minimizer.credible_interval_inner']),
        )

    @staticmethod
    def _credible_interval_outer_descriptor() -> NumericDescriptor:
        """Create an outer credible-interval descriptor."""
        return NumericDescriptor(
            name='credible_interval_outer',
            description='Outer credible-interval level used in summaries.',
            value_spec=AttributeSpec(default=0.95),
            cif_handler=CifHandler(names=['_minimizer.credible_interval_outer']),
        )

    @staticmethod
    def _acceptance_rate_mean_descriptor() -> NumericDescriptor:
        """Create an acceptance-rate descriptor."""
        return NumericDescriptor(
            name='acceptance_rate_mean',
            description='Mean sampler acceptance rate.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_minimizer.acceptance_rate_mean']),
        )

    @staticmethod
    def _gelman_rubin_max_descriptor() -> NumericDescriptor:
        """Create a Gelman-Rubin descriptor."""
        return NumericDescriptor(
            name='gelman_rubin_max',
            description='Maximum rank-normalized split R-hat.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_minimizer.gelman_rubin_max']),
        )

    @staticmethod
    def _effective_sample_size_min_descriptor() -> NumericDescriptor:
        """Create an effective-sample-size descriptor."""
        return NumericDescriptor(
            name='effective_sample_size_min',
            description='Minimum bulk effective sample size.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_minimizer.effective_sample_size_min']),
        )

    @staticmethod
    def _best_log_posterior_descriptor() -> NumericDescriptor:
        """Create a best-log-posterior descriptor."""
        return NumericDescriptor(
            name='best_log_posterior',
            description='Best log-posterior value found.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_minimizer.best_log_posterior']),
        )

    @property
    def sampling_steps(self) -> IntegerDescriptor:
        """Total sampler iterations per chain."""
        return self._sampling_steps

    @sampling_steps.setter
    def sampling_steps(self, value: int) -> None:
        self._sampling_steps.value = value

    @property
    def burn_in_steps(self) -> IntegerDescriptor:
        """Sampler iterations discarded as warm-up."""
        return self._burn_in_steps

    @burn_in_steps.setter
    def burn_in_steps(self, value: int) -> None:
        self._burn_in_steps.value = value

    @property
    def thinning_interval(self) -> IntegerDescriptor:
        """Sampler thinning interval."""
        return self._thinning_interval

    @thinning_interval.setter
    def thinning_interval(self, value: int) -> None:
        self._thinning_interval.value = value

    @property
    def population_size(self) -> IntegerDescriptor:
        """Number of chains or walkers."""
        return self._population_size

    @population_size.setter
    def population_size(self, value: int) -> None:
        self._population_size.value = value

    @property
    def parallel_workers(self) -> IntegerDescriptor:
        """Worker count; 0 uses all available CPUs."""
        return self._parallel_workers

    @parallel_workers.setter
    def parallel_workers(self, value: int) -> None:
        self._parallel_workers.value = value

    @property
    def initialization_method(self) -> StringDescriptor:
        """Sampler initialization method."""
        return self._initialization_method

    @initialization_method.setter
    def initialization_method(self, value: InitializationMethodEnum | str) -> None:
        method = InitializationMethodEnum(value)
        if method not in self._supported_initialization_methods:
            supported = ', '.join(item.value for item in self._supported_initialization_methods)
            msg = f"Initialization method '{method.value}' is unsupported; use: {supported}."
            raise ValueError(msg)
        self._initialization_method.value = method.value

    @property
    def random_seed(self) -> IntegerDescriptor:
        """Random seed; None uses a system-derived seed."""
        return self._random_seed

    @random_seed.setter
    def random_seed(self, value: int | None) -> None:
        self._random_seed.value = value

    @property
    def runtime_seconds(self) -> NumericDescriptor:
        """Wall time of the fit in seconds."""
        return self._runtime_seconds

    def _set_runtime_seconds(self, value: float | None) -> None:
        """Set the fit runtime for internal callers."""
        self._runtime_seconds.value = value

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
