# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Resolved Bayesian sampler settings category."""

from __future__ import annotations

from easydiffraction.analysis.categories.bayesian_sampler.factory import BayesianSamplerFactory
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.variable import BoolDescriptor
from easydiffraction.core.variable import NumericDescriptor
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
        self._steps = NumericDescriptor(
            name='steps',
            description='Resolved number of sampler steps.',
            value_spec=AttributeSpec(default=0),
            cif_handler=CifHandler(names=['_bayesian_sampler.steps']),
        )
        self._burn = NumericDescriptor(
            name='burn',
            description='Resolved burn-in count.',
            value_spec=AttributeSpec(default=0),
            cif_handler=CifHandler(names=['_bayesian_sampler.burn']),
        )
        self._thin = NumericDescriptor(
            name='thin',
            description='Resolved thinning interval.',
            value_spec=AttributeSpec(default=0),
            cif_handler=CifHandler(names=['_bayesian_sampler.thin']),
        )
        self._pop = NumericDescriptor(
            name='pop',
            description='Resolved population size.',
            value_spec=AttributeSpec(default=0),
            cif_handler=CifHandler(names=['_bayesian_sampler.pop']),
        )
        self._parallel = BoolDescriptor(
            name='parallel',
            description='Whether sampling ran in parallel.',
            value_spec=AttributeSpec(default=False),
            cif_handler=CifHandler(names=['_bayesian_sampler.parallel']),
        )
        self._init = StringDescriptor(
            name='init',
            description='Resolved DREAM initialization mode.',
            value_spec=AttributeSpec(default=''),
            cif_handler=CifHandler(names=['_bayesian_sampler.init']),
        )
        self._random_seed = NumericDescriptor(
            name='random_seed',
            description='Resolved random seed used by the sampler.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_bayesian_sampler.random_seed']),
        )

    @property
    def steps(self) -> NumericDescriptor:
        """Resolved number of sampler steps."""
        return self._steps

    def _set_steps(self, value: int | float) -> None:
        """Set the step count for internal callers."""
        self._steps.value = value

    @property
    def burn(self) -> NumericDescriptor:
        """Resolved burn-in count."""
        return self._burn

    def _set_burn(self, value: int | float) -> None:
        """Set the burn-in count for internal callers."""
        self._burn.value = value

    @property
    def thin(self) -> NumericDescriptor:
        """Resolved thinning interval."""
        return self._thin

    def _set_thin(self, value: int | float) -> None:
        """Set the thinning interval for internal callers."""
        self._thin.value = value

    @property
    def pop(self) -> NumericDescriptor:
        """Resolved population size."""
        return self._pop

    def _set_pop(self, value: int | float) -> None:
        """Set the population size for internal callers."""
        self._pop.value = value

    @property
    def parallel(self) -> BoolDescriptor:
        """Whether sampling ran in parallel."""
        return self._parallel

    def _set_parallel(self, value: bool) -> None:
        """Set the parallel flag for internal callers."""
        self._parallel.value = value

    @property
    def init(self) -> StringDescriptor:
        """Resolved DREAM initialization mode."""
        return self._init

    def _set_init(self, value: str) -> None:
        """Set the initialization mode for internal callers."""
        self._init.value = value

    @property
    def random_seed(self) -> NumericDescriptor:
        """Resolved random seed used by the sampler."""
        return self._random_seed

    def _set_random_seed(self, value: int | float | None) -> None:
        """Set the random seed for internal callers."""
        self._random_seed.value = value