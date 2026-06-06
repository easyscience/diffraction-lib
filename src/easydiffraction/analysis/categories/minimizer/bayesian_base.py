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
from easydiffraction.core.variable import IntegerDescriptor
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
    _result_descriptor_names: ClassVar[tuple[str, ...]] = ()
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
            cif_handler=CifHandler(
                names=['_minimizer.sampling_steps'],
                iucr_name='_easydiffraction_minimizer.sampling_steps',
            ),
        )

    @staticmethod
    def _burn_in_steps_descriptor(default: int) -> IntegerDescriptor:
        """Create a burn-in descriptor."""
        return IntegerDescriptor(
            name='burn_in_steps',
            description='Sampler iterations discarded as warm-up.',
            value_spec=AttributeSpec(default=default, validator=RangeValidator(ge=0)),
            cif_handler=CifHandler(
                names=['_minimizer.burn_in_steps'],
                iucr_name='_easydiffraction_minimizer.burn_in_steps',
            ),
        )

    @staticmethod
    def _thinning_interval_descriptor(default: int) -> IntegerDescriptor:
        """Create a thinning-interval descriptor."""
        return IntegerDescriptor(
            name='thinning_interval',
            description='Sampler thinning interval.',
            value_spec=AttributeSpec(default=default, validator=RangeValidator(ge=1)),
            cif_handler=CifHandler(
                names=['_minimizer.thinning_interval'],
                iucr_name='_easydiffraction_minimizer.thinning_interval',
            ),
        )

    @staticmethod
    def _population_size_descriptor(default: int) -> IntegerDescriptor:
        """Create a population-size descriptor."""
        return IntegerDescriptor(
            name='population_size',
            description='Number of chains or walkers.',
            value_spec=AttributeSpec(default=default, validator=RangeValidator(ge=1)),
            cif_handler=CifHandler(
                names=['_minimizer.population_size'],
                iucr_name='_easydiffraction_minimizer.population_size',
            ),
        )

    @staticmethod
    def _parallel_workers_descriptor(default: int) -> IntegerDescriptor:
        """Create a parallel-workers descriptor."""
        return IntegerDescriptor(
            name='parallel_workers',
            description='Worker count; 0 uses all available CPUs.',
            value_spec=AttributeSpec(default=default, validator=RangeValidator(ge=0)),
            cif_handler=CifHandler(
                names=['_minimizer.parallel_workers'],
                iucr_name='_easydiffraction_minimizer.parallel_workers',
            ),
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
            cif_handler=CifHandler(
                names=['_minimizer.initialization_method'],
                iucr_name='_easydiffraction_minimizer.initialization_method',
            ),
        )

    @staticmethod
    def _random_seed_descriptor() -> IntegerDescriptor:
        """Create a random-seed descriptor."""
        return IntegerDescriptor(
            name='random_seed',
            description='Random seed; None uses a system-derived seed.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(
                names=['_minimizer.random_seed'],
                iucr_name='_easydiffraction_minimizer.random_seed',
            ),
        )

    @property
    def sampling_steps(self) -> IntegerDescriptor:
        """Total sampler iterations per chain."""
        return self._sampling_steps

    @sampling_steps.setter
    def sampling_steps(self, value: int) -> None:
        """Set the total sampler iterations per chain."""
        self._sampling_steps.value = value

    @property
    def burn_in_steps(self) -> IntegerDescriptor:
        """Sampler iterations discarded as warm-up."""
        return self._burn_in_steps

    @burn_in_steps.setter
    def burn_in_steps(self, value: int) -> None:
        """Set the sampler iterations discarded as warm-up."""
        self._burn_in_steps.value = value

    @property
    def thinning_interval(self) -> IntegerDescriptor:
        """Sampler thinning interval."""
        return self._thinning_interval

    @thinning_interval.setter
    def thinning_interval(self, value: int) -> None:
        """Set the sampler thinning interval."""
        self._thinning_interval.value = value

    @property
    def population_size(self) -> IntegerDescriptor:
        """Number of chains or walkers."""
        return self._population_size

    @population_size.setter
    def population_size(self, value: int) -> None:
        """Set the number of chains or walkers."""
        self._population_size.value = value

    @property
    def parallel_workers(self) -> IntegerDescriptor:
        """Worker count; 0 uses all available CPUs."""
        return self._parallel_workers

    @parallel_workers.setter
    def parallel_workers(self, value: int) -> None:
        """Set the worker count; 0 uses all available CPUs."""
        self._parallel_workers.value = value

    @property
    def initialization_method(self) -> StringDescriptor:
        """Sampler initialization method."""
        return self._initialization_method

    @initialization_method.setter
    def initialization_method(self, value: InitializationMethodEnum | str) -> None:
        """Set the sampler initialization method if supported."""
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
        """Set the random seed; None uses a system-derived seed."""
        self._random_seed.value = value
