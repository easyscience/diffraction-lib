# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Behavior helpers for deterministic minimizer categories."""

from __future__ import annotations

from typing import ClassVar

from easydiffraction.analysis.categories.minimizer.base import MinimizerCategoryBase
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.variable import BoolDescriptor
from easydiffraction.core.variable import IntegerDescriptor
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import CifHandler


class LeastSquaresMinimizerBase(MinimizerCategoryBase):
    """Shared behavior for least-squares minimizer categories."""

    _default_max_iterations: ClassVar[int] = 1000
    _expected_descriptor_names: ClassVar[tuple[str, ...]] = (
        'max_iterations',
        'optimizer_name',
        'method_name',
        'objective_name',
        'objective_value',
        'n_data_points',
        'n_parameters',
        'n_free_parameters',
        'degrees_of_freedom',
        'covariance_available',
        'correlation_available',
        'runtime_seconds',
        'iterations_performed',
        'exit_reason',
    )
    _native_key_map: ClassVar[dict[str, str]] = {
        'max_iterations': 'max_iterations',
    }
    _setting_descriptor_names: ClassVar[tuple[str, ...]] = ('max_iterations',)
    _result_descriptor_names: ClassVar[tuple[str, ...]] = (
        'optimizer_name',
        'method_name',
        'objective_name',
        'objective_value',
        'n_data_points',
        'n_parameters',
        'n_free_parameters',
        'degrees_of_freedom',
        'covariance_available',
        'correlation_available',
        'runtime_seconds',
        'iterations_performed',
        'exit_reason',
    )

    def __init__(self) -> None:
        super().__init__()
        self._max_iterations = self._max_iterations_descriptor(self._default_max_iterations)
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
    def _string_result_descriptor(name: str, description: str) -> StringDescriptor:
        """Create a string-valued result descriptor.

        Defaults to ``None`` so a CIF written before any fit emits ``?``
        rather than an empty string, matching the "no fit happened yet"
        semantics shared with the numeric/integer/bool variants.
        """
        return StringDescriptor(
            name=name,
            description=description,
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=[f'_minimizer.{name}']),
        )

    @staticmethod
    def _numeric_result_descriptor(
        name: str,
        description: str,
        *,
        default: float | None = None,
        allow_none: bool = True,
    ) -> NumericDescriptor:
        """Create a numeric result descriptor."""
        return NumericDescriptor(
            name=name,
            description=description,
            value_spec=AttributeSpec(default=default, allow_none=allow_none),
            cif_handler=CifHandler(names=[f'_minimizer.{name}']),
        )

    @staticmethod
    def _integer_result_descriptor(name: str, description: str) -> NumericDescriptor:
        """Create an integer-like numeric result descriptor.

        Defaults to ``None`` so a CIF written before any fit emits ``?``
        rather than ``0``; the scientist audience reads ``0`` as a
        degenerate result, not as "no fit yet".
        """
        return NumericDescriptor(
            name=name,
            description=description,
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=[f'_minimizer.{name}']),
        )

    @staticmethod
    def _bool_result_descriptor(name: str, description: str) -> BoolDescriptor:
        """Create a boolean result descriptor.

        Defaults to ``None`` so a CIF written before any fit emits ``?``
        rather than ``false``; ``false`` would otherwise read as
        "covariance/correlation was actively unavailable" instead of
        "no fit happened yet".
        """
        return BoolDescriptor(
            name=name,
            description=description,
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=[f'_minimizer.{name}']),
        )

    @property
    def max_iterations(self) -> IntegerDescriptor:
        """Maximum solver iterations."""
        return self._max_iterations

    @max_iterations.setter
    def max_iterations(self, value: int) -> None:
        self._max_iterations.value = value

    @property
    def optimizer_name(self) -> StringDescriptor:
        """
        Name of the optimizer used by the persisted deterministic fit.
        """
        return self._optimizer_name

    def _set_optimizer_name(self, value: str | None) -> None:
        self._optimizer_name.value = value

    @property
    def method_name(self) -> StringDescriptor:
        """Method name used by the persisted deterministic fit."""
        return self._method_name

    def _set_method_name(self, value: str | None) -> None:
        self._method_name.value = value

    @property
    def objective_name(self) -> StringDescriptor:
        """
        Objective function name for the persisted deterministic fit.
        """
        return self._objective_name

    def _set_objective_name(self, value: str | None) -> None:
        self._objective_name.value = value

    @property
    def objective_value(self) -> NumericDescriptor:
        """Objective value for the persisted deterministic fit."""
        return self._objective_value

    def _set_objective_value(self, value: float | None) -> None:
        self._objective_value.value = value

    @property
    def n_data_points(self) -> NumericDescriptor:
        """
        Number of data points used in the persisted deterministic fit.
        """
        return self._n_data_points

    def _set_n_data_points(self, value: float | None) -> None:
        self._n_data_points.value = value

    @property
    def n_parameters(self) -> NumericDescriptor:
        """Number of parameters in the persisted deterministic fit."""
        return self._n_parameters

    def _set_n_parameters(self, value: float | None) -> None:
        self._n_parameters.value = value

    @property
    def n_free_parameters(self) -> NumericDescriptor:
        """
        Number of free parameters in the persisted deterministic fit.
        """
        return self._n_free_parameters

    def _set_n_free_parameters(self, value: float | None) -> None:
        self._n_free_parameters.value = value

    @property
    def degrees_of_freedom(self) -> NumericDescriptor:
        """Degrees of freedom for the persisted deterministic fit."""
        return self._degrees_of_freedom

    def _set_degrees_of_freedom(self, value: float | None) -> None:
        self._degrees_of_freedom.value = value

    @property
    def covariance_available(self) -> BoolDescriptor:
        """Whether deterministic covariance was available."""
        return self._covariance_available

    def _set_covariance_available(self, *, value: bool | None) -> None:
        self._covariance_available.value = value

    @property
    def correlation_available(self) -> BoolDescriptor:
        """Whether deterministic correlations were available."""
        return self._correlation_available

    def _set_correlation_available(self, *, value: bool | None) -> None:
        self._correlation_available.value = value

    @property
    def runtime_seconds(self) -> NumericDescriptor:
        """Runtime in seconds for the persisted deterministic fit."""
        return self._runtime_seconds

    def _set_runtime_seconds(self, value: float | None) -> None:
        self._runtime_seconds.value = value

    @property
    def iterations_performed(self) -> NumericDescriptor:
        """Number of iterations performed by the deterministic fit."""
        return self._iterations_performed

    def _set_iterations_performed(self, value: float | None) -> None:
        self._iterations_performed.value = value

    @property
    def exit_reason(self) -> StringDescriptor:
        """Backend exit reason for the persisted deterministic fit."""
        return self._exit_reason

    def _set_exit_reason(self, value: str | None) -> None:
        self._exit_reason.value = value
