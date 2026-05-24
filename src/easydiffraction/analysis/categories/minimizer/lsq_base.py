# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Behavior helpers for deterministic minimizer categories."""

from __future__ import annotations

from typing import ClassVar

from easydiffraction.analysis.categories.fit_result.lsq import LeastSquaresFitResult
from easydiffraction.analysis.categories.minimizer.base import MinimizerCategoryBase
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.variable import IntegerDescriptor
from easydiffraction.io.cif.handler import CifHandler


class LeastSquaresMinimizerBase(MinimizerCategoryBase):
    """Shared behavior for least-squares minimizer categories."""

    _default_max_iterations: ClassVar[int] = 1000
    _fit_result_class: ClassVar[type] = LeastSquaresFitResult
    _expected_descriptor_names: ClassVar[tuple[str, ...]] = (
        'max_iterations',
    )
    _native_key_map: ClassVar[dict[str, str]] = {
        'max_iterations': 'max_iterations',
    }
    _setting_descriptor_names: ClassVar[tuple[str, ...]] = ('max_iterations',)
    _result_descriptor_names: ClassVar[tuple[str, ...]] = ()

    def __init__(self) -> None:
        super().__init__()
        self._max_iterations = self._max_iterations_descriptor(self._default_max_iterations)

    @staticmethod
    def _max_iterations_descriptor(default: int) -> IntegerDescriptor:
        """Create a max-iterations descriptor."""
        return IntegerDescriptor(
            name='max_iterations',
            description='Maximum solver iterations.',
            value_spec=AttributeSpec(default=default, validator=RangeValidator(ge=1)),
            cif_handler=CifHandler(names=['_minimizer.max_iterations']),
        )

    @property
    def max_iterations(self) -> IntegerDescriptor:
        """Maximum solver iterations."""
        return self._max_iterations

    @max_iterations.setter
    def max_iterations(self, value: int) -> None:
        self._max_iterations.value = value
