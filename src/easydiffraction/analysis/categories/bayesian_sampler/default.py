# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Resolved Bayesian sampler settings category."""

from __future__ import annotations

from easydiffraction.analysis.categories.bayesian_sampler.factory import BayesianSamplerFactory
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.variable import IntegerDescriptor
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import CifHandler


@BayesianSamplerFactory.register
class BayesianSampler(CategoryItem):
    """Persisted resolved Bayesian sampler settings."""

    _category_code = 'bayesian_sampler'

    type_info = TypeInfo(
        tag='default',
        description='Persisted resolved Bayesian sampler settings',
    )

    def __init__(self) -> None:
        super().__init__()
        self._steps = IntegerDescriptor(
            name='steps',
            description='Resolved number of sampler steps.',
            value_spec=AttributeSpec(default=0),
            cif_handler=CifHandler(names=['_bayesian_sampler.steps']),
        )
        self._burn = IntegerDescriptor(
            name='burn',
            description='Resolved burn-in count.',
            value_spec=AttributeSpec(default=0),
            cif_handler=CifHandler(names=['_bayesian_sampler.burn']),
        )
        self._thin = IntegerDescriptor(
            name='thin',
            description='Resolved thinning interval.',
            value_spec=AttributeSpec(default=0),
            cif_handler=CifHandler(names=['_bayesian_sampler.thin']),
        )
        self._pop = IntegerDescriptor(
            name='pop',
            description='Resolved population size.',
            value_spec=AttributeSpec(default=0),
            cif_handler=CifHandler(names=['_bayesian_sampler.pop']),
        )
        self._parallel = IntegerDescriptor(
            name='parallel',
            description='Resolved DREAM worker count; 0 uses all CPUs.',
            value_spec=AttributeSpec(default=0),
            cif_handler=CifHandler(names=['_bayesian_sampler.parallel']),
        )
        self._init = StringDescriptor(
            name='init',
            description='Resolved DREAM initialization mode.',
            value_spec=AttributeSpec(default=''),
            cif_handler=CifHandler(names=['_bayesian_sampler.init']),
        )
        self._random_seed = IntegerDescriptor(
            name='random_seed',
            description='Resolved random seed used by the sampler.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_bayesian_sampler.random_seed']),
        )

    @property
    def steps(self) -> IntegerDescriptor:
        """Resolved number of sampler steps."""
        return self._steps

    def _set_steps(self, value: int) -> None:
        """Set the step count for internal callers."""
        self._steps.value = value

    @property
    def burn(self) -> IntegerDescriptor:
        """Resolved burn-in count."""
        return self._burn

    def _set_burn(self, value: int) -> None:
        """Set the burn-in count for internal callers."""
        self._burn.value = value

    @property
    def thin(self) -> IntegerDescriptor:
        """Resolved thinning interval."""
        return self._thin

    def _set_thin(self, value: int) -> None:
        """Set the thinning interval for internal callers."""
        self._thin.value = value

    @property
    def pop(self) -> IntegerDescriptor:
        """Resolved population size."""
        return self._pop

    def _set_pop(self, value: int) -> None:
        """Set the population size for internal callers."""
        self._pop.value = value

    @property
    def parallel(self) -> IntegerDescriptor:
        """Resolved DREAM worker count; 0 uses all CPUs."""
        return self._parallel

    def _set_parallel(self, value: int) -> None:
        """Set the DREAM worker count for internal callers."""
        self._parallel.value = value

    @property
    def init(self) -> StringDescriptor:
        """Resolved DREAM initialization mode."""
        return self._init

    def _set_init(self, value: str) -> None:
        """Set the initialization mode for internal callers."""
        self._init.value = value

    @property
    def random_seed(self) -> IntegerDescriptor:
        """Resolved random seed used by the sampler."""
        return self._random_seed

    def _set_random_seed(self, value: int | None) -> None:
        """Set the random seed for internal callers."""
        self._random_seed.value = value
