# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Behavior helpers for deterministic minimizer categories."""

from __future__ import annotations

from typing import ClassVar

from easydiffraction.analysis.categories.minimizer.base import MinimizerCategoryBase
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.variable import IntegerDescriptor
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.io.cif.handler import CifHandler


class LeastSquaresMinimizerBase(MinimizerCategoryBase):
    """Shared behavior for least-squares minimizer categories."""

    _expected_descriptor_names: ClassVar[tuple[str, ...]] = (
        'max_iterations',
        'convergence_tolerance',
        'random_seed',
    )
    _native_key_map: ClassVar[dict[str, str]] = {
        'max_iterations': 'max_iterations',
        'convergence_tolerance': 'convergence_tolerance',
        'random_seed': 'random_seed',
    }

    @staticmethod
    def _max_iterations_descriptor(default: int) -> IntegerDescriptor:
        """Create a max-iterations descriptor."""
        return IntegerDescriptor(
            name='max_iterations',
            description='Maximum solver iterations.',
            value_spec=AttributeSpec(default=default, validator=RangeValidator(ge=1)),
            cif_handler=CifHandler(names=['_minimizer.max_iterations']),
        )

    @staticmethod
    def _convergence_tolerance_descriptor(default: float) -> NumericDescriptor:
        """Create a convergence-tolerance descriptor."""
        return NumericDescriptor(
            name='convergence_tolerance',
            description='Convergence tolerance for the solver.',
            value_spec=AttributeSpec(default=default, validator=RangeValidator(ge=0)),
            cif_handler=CifHandler(names=['_minimizer.convergence_tolerance']),
        )

    @staticmethod
    def _random_seed_descriptor() -> IntegerDescriptor:
        """Create a random-seed descriptor."""
        return IntegerDescriptor(
            name='random_seed',
            description='Random seed used by stochastic solvers.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_minimizer.random_seed']),
        )

    @property
    def max_iterations(self) -> IntegerDescriptor:
        """Maximum solver iterations."""
        return self._max_iterations

    @max_iterations.setter
    def max_iterations(self, value: int) -> None:
        self._max_iterations.value = value

    @property
    def convergence_tolerance(self) -> NumericDescriptor:
        """Convergence tolerance for the solver."""
        return self._convergence_tolerance

    @convergence_tolerance.setter
    def convergence_tolerance(self, value: float) -> None:
        self._convergence_tolerance.value = value

    @property
    def random_seed(self) -> IntegerDescriptor:
        """Random seed used by stochastic solvers."""
        return self._random_seed

    @random_seed.setter
    def random_seed(self, value: int | None) -> None:
        self._random_seed.value = value
