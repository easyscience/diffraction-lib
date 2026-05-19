# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Fit-parameter control snapshots."""

from __future__ import annotations

import numpy as np

from easydiffraction.analysis.categories.fit_parameters.factory import FitParametersFactory
from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RegexValidator
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import CifHandler


class FitParameterItem(CategoryItem):
    """Single persisted fit-parameter control row."""

    _category_code = 'fit_parameter'
    _category_entry_name = 'param_unique_name'

    def __init__(self) -> None:
        super().__init__()
        self._param_unique_name = StringDescriptor(
            name='param_unique_name',
            description='Unique name of the referenced live parameter.',
            value_spec=AttributeSpec(
                default='_',
                validator=RegexValidator(pattern=r'^[A-Za-z_][A-Za-z0-9_.]*$'),
            ),
            cif_handler=CifHandler(names=['_fit_parameter.param_unique_name']),
        )
        self._fit_min = NumericDescriptor(
            name='fit_min',
            description='Persisted lower fit bound.',
            value_spec=AttributeSpec(default=-np.inf),
            cif_handler=CifHandler(names=['_fit_parameter.fit_min']),
        )
        self._fit_max = NumericDescriptor(
            name='fit_max',
            description='Persisted upper fit bound.',
            value_spec=AttributeSpec(default=np.inf),
            cif_handler=CifHandler(names=['_fit_parameter.fit_max']),
        )
        self._fit_bounds_uncertainty_multiplier = NumericDescriptor(
            name='fit_bounds_uncertainty_multiplier',
            description='Multiplier used to derive fit bounds from uncertainty.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_fit_parameter.fit_bounds_uncertainty_multiplier']),
        )
        self._start_value = NumericDescriptor(
            name='start_value',
            description='Persisted pre-fit value snapshot.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_fit_parameter.start_value']),
        )
        self._start_uncertainty = NumericDescriptor(
            name='start_uncertainty',
            description='Persisted pre-fit uncertainty snapshot.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_fit_parameter.start_uncertainty']),
        )

    @property
    def param_unique_name(self) -> StringDescriptor:
        """Unique name of the referenced live parameter."""
        return self._param_unique_name

    def _set_param_unique_name(self, value: str) -> None:
        """
        Set the referenced parameter unique name for internal callers.
        """
        self._param_unique_name.value = value

    @property
    def fit_min(self) -> NumericDescriptor:
        """Persisted lower fit bound."""
        return self._fit_min

    def _set_fit_min(self, value: float) -> None:
        """Set the persisted lower fit bound for internal callers."""
        self._fit_min.value = value

    @property
    def fit_max(self) -> NumericDescriptor:
        """Persisted upper fit bound."""
        return self._fit_max

    def _set_fit_max(self, value: float) -> None:
        """Set the persisted upper fit bound for internal callers."""
        self._fit_max.value = value

    @property
    def fit_bounds_uncertainty_multiplier(self) -> NumericDescriptor:
        """Multiplier used to derive fit bounds from uncertainty."""
        return self._fit_bounds_uncertainty_multiplier

    def _set_fit_bounds_uncertainty_multiplier(
        self,
        value: float | None,
    ) -> None:
        """
        Set the fit-bounds uncertainty multiplier for internal callers.
        """
        self._fit_bounds_uncertainty_multiplier.value = value

    @property
    def start_value(self) -> NumericDescriptor:
        """Persisted pre-fit value snapshot."""
        return self._start_value

    def _set_start_value(self, value: float | None) -> None:
        """Set the pre-fit value snapshot for internal callers."""
        self._start_value.value = value

    @property
    def start_uncertainty(self) -> NumericDescriptor:
        """Persisted pre-fit uncertainty snapshot."""
        return self._start_uncertainty

    def _set_start_uncertainty(self, value: float | None) -> None:
        """Set the pre-fit uncertainty snapshot for internal callers."""
        self._start_uncertainty.value = value


@FitParametersFactory.register
class FitParameters(CategoryCollection):
    """Collection of persisted fit-parameter control snapshots."""

    type_info = TypeInfo(
        tag='default',
        description='Persisted fit-parameter control snapshots',
    )

    def __init__(self) -> None:
        super().__init__(item_type=FitParameterItem)

    def create(
        self,
        *,
        param_unique_name: str,
        fit_min: float,
        fit_max: float,
        fit_bounds_uncertainty_multiplier: float | None = None,
        start_value: float | None = None,
        start_uncertainty: float | None = None,
    ) -> None:
        """
        Create a persisted fit-parameter control snapshot row.

        Parameters
        ----------
        param_unique_name : str
            Unique name of the referenced live parameter.
        fit_min : float
            Persisted lower fit bound.
        fit_max : float
            Persisted upper fit bound.
        fit_bounds_uncertainty_multiplier : float | None, default=None
            Multiplier used to derive fit bounds from uncertainty.
        start_value : float | None, default=None
            Persisted pre-fit value snapshot.
        start_uncertainty : float | None, default=None
            Persisted pre-fit uncertainty snapshot.
        """
        item = FitParameterItem()
        item._set_param_unique_name(param_unique_name)
        item._set_fit_min(fit_min)
        item._set_fit_max(fit_max)
        item._set_fit_bounds_uncertainty_multiplier(fit_bounds_uncertainty_multiplier)
        item._set_start_value(start_value)
        item._set_start_uncertainty(start_uncertainty)
        self.add(item)
