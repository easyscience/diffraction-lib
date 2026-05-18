# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Deterministic fit-result metadata category."""

from __future__ import annotations

from easydiffraction.analysis.categories.deterministic_result.factory import (
    DeterministicResultFactory,
)
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.variable import BoolDescriptor
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import CifHandler


@DeterministicResultFactory.register
class DeterministicResult(CategoryItem):
    """Persisted deterministic fit-result metadata."""

    _category_code = 'deterministic_result'

    type_info = TypeInfo(
        tag='default',
        description='Persisted deterministic fit-result metadata',
    )

    def __init__(self) -> None:
        super().__init__()
        self._optimizer_name = StringDescriptor(
            name='optimizer_name',
            description='Name of the persisted deterministic optimizer.',
            value_spec=AttributeSpec(default=''),
            cif_handler=CifHandler(names=['_deterministic_result.optimizer_name']),
        )
        self._method_name = StringDescriptor(
            name='method_name',
            description='Method name of the persisted deterministic optimizer.',
            value_spec=AttributeSpec(default=''),
            cif_handler=CifHandler(names=['_deterministic_result.method_name']),
        )
        self._objective_name = StringDescriptor(
            name='objective_name',
            description='Objective function name for the persisted deterministic fit.',
            value_spec=AttributeSpec(default=''),
            cif_handler=CifHandler(names=['_deterministic_result.objective_name']),
        )
        self._objective_value = NumericDescriptor(
            name='objective_value',
            description='Objective value for the persisted deterministic fit.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_deterministic_result.objective_value']),
        )
        self._n_data_points = NumericDescriptor(
            name='n_data_points',
            description='Number of data points used in the persisted deterministic fit.',
            value_spec=AttributeSpec(default=0),
            cif_handler=CifHandler(names=['_deterministic_result.n_data_points']),
        )
        self._n_parameters = NumericDescriptor(
            name='n_parameters',
            description='Number of parameters considered in the persisted deterministic fit.',
            value_spec=AttributeSpec(default=0),
            cif_handler=CifHandler(names=['_deterministic_result.n_parameters']),
        )
        self._n_free_parameters = NumericDescriptor(
            name='n_free_parameters',
            description='Number of free parameters in the persisted deterministic fit.',
            value_spec=AttributeSpec(default=0),
            cif_handler=CifHandler(names=['_deterministic_result.n_free_parameters']),
        )
        self._degrees_of_freedom = NumericDescriptor(
            name='degrees_of_freedom',
            description='Degrees of freedom for the persisted deterministic fit.',
            value_spec=AttributeSpec(default=0),
            cif_handler=CifHandler(names=['_deterministic_result.degrees_of_freedom']),
        )
        self._covariance_available = BoolDescriptor(
            name='covariance_available',
            description='Whether covariance was available for the persisted deterministic fit.',
            value_spec=AttributeSpec(default=False),
            cif_handler=CifHandler(names=['_deterministic_result.covariance_available']),
        )
        self._correlation_available = BoolDescriptor(
            name='correlation_available',
            description='Whether correlations were available for the persisted deterministic fit.',
            value_spec=AttributeSpec(default=False),
            cif_handler=CifHandler(names=['_deterministic_result.correlation_available']),
        )

    @property
    def optimizer_name(self) -> StringDescriptor:
        """Name of the persisted deterministic optimizer."""
        return self._optimizer_name

    def _set_optimizer_name(self, value: str) -> None:
        """Set the optimizer name for internal callers."""
        self._optimizer_name.value = value

    @property
    def method_name(self) -> StringDescriptor:
        """Method name of the persisted deterministic optimizer."""
        return self._method_name

    def _set_method_name(self, value: str) -> None:
        """Set the method name for internal callers."""
        self._method_name.value = value

    @property
    def objective_name(self) -> StringDescriptor:
        """
        Objective function name for the persisted deterministic fit.
        """
        return self._objective_name

    def _set_objective_name(self, value: str) -> None:
        """Set the objective name for internal callers."""
        self._objective_name.value = value

    @property
    def objective_value(self) -> NumericDescriptor:
        """Objective value for the persisted deterministic fit."""
        return self._objective_value

    def _set_objective_value(self, value: float | None) -> None:
        """Set the objective value for internal callers."""
        self._objective_value.value = value

    @property
    def n_data_points(self) -> NumericDescriptor:
        """
        Number of data points used in the persisted deterministic fit.
        """
        return self._n_data_points

    def _set_n_data_points(self, value: float) -> None:
        """Set the data-point count for internal callers."""
        self._n_data_points.value = value

    @property
    def n_parameters(self) -> NumericDescriptor:
        """
        Number of parameters considered in the persisted deterministic
        fit.
        """
        return self._n_parameters

    def _set_n_parameters(self, value: float) -> None:
        """Set the parameter count for internal callers."""
        self._n_parameters.value = value

    @property
    def n_free_parameters(self) -> NumericDescriptor:
        """
        Number of free parameters in the persisted deterministic fit.
        """
        return self._n_free_parameters

    def _set_n_free_parameters(self, value: float) -> None:
        """Set the free-parameter count for internal callers."""
        self._n_free_parameters.value = value

    @property
    def degrees_of_freedom(self) -> NumericDescriptor:
        """Degrees of freedom for the persisted deterministic fit."""
        return self._degrees_of_freedom

    def _set_degrees_of_freedom(self, value: float) -> None:
        """Set the degrees of freedom for internal callers."""
        self._degrees_of_freedom.value = value

    @property
    def covariance_available(self) -> BoolDescriptor:
        """
        Whether covariance was available for the persisted deterministic
        fit.
        """
        return self._covariance_available

    def _set_covariance_available(self, value: bool) -> None:
        """Set the covariance-available flag for internal callers."""
        self._covariance_available.value = value

    @property
    def correlation_available(self) -> BoolDescriptor:
        """
        Whether correlations were available for the persisted
        deterministic fit.
        """
        return self._correlation_available

    def _set_correlation_available(self, value: bool) -> None:
        """Set the correlation-available flag for internal callers."""
        self._correlation_available.value = value
