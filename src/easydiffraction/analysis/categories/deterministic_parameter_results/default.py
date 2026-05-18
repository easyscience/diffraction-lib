# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Deterministic fit parameter-result rows."""

from __future__ import annotations

from easydiffraction.analysis.categories.deterministic_parameter_results.factory import (
    DeterministicParameterResultsFactory,
)
from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RegexValidator
from easydiffraction.core.variable import BoolDescriptor
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import CifHandler


class DeterministicParameterResultItem(CategoryItem):
    """Single persisted deterministic parameter-result row."""

    _category_code = 'deterministic_parameter_result'
    _category_entry_name = 'param_unique_name'

    def __init__(self) -> None:
        super().__init__()
        self._param_unique_name = StringDescriptor(
            name='param_unique_name',
            description='Unique name of the persisted parameter result row.',
            value_spec=AttributeSpec(
                default='_',
                validator=RegexValidator(pattern=r'^[A-Za-z_][A-Za-z0-9_.]*$'),
            ),
            cif_handler=CifHandler(names=['_deterministic_parameter_result.param_unique_name']),
        )
        self._final_value = NumericDescriptor(
            name='final_value',
            description='Final fitted value for the persisted parameter result.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_deterministic_parameter_result.final_value']),
        )
        self._final_uncertainty = NumericDescriptor(
            name='final_uncertainty',
            description='Final uncertainty for the persisted parameter result.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_deterministic_parameter_result.final_uncertainty']),
        )
        self._at_lower_bound = BoolDescriptor(
            name='at_lower_bound',
            description='Whether the parameter finished at the lower fit bound.',
            value_spec=AttributeSpec(default=False),
            cif_handler=CifHandler(names=['_deterministic_parameter_result.at_lower_bound']),
        )
        self._at_upper_bound = BoolDescriptor(
            name='at_upper_bound',
            description='Whether the parameter finished at the upper fit bound.',
            value_spec=AttributeSpec(default=False),
            cif_handler=CifHandler(names=['_deterministic_parameter_result.at_upper_bound']),
        )

    @property
    def param_unique_name(self) -> StringDescriptor:
        """Unique name of the persisted parameter result row."""
        return self._param_unique_name

    def _set_param_unique_name(self, value: str) -> None:
        """Set the parameter unique name for internal callers."""
        self._param_unique_name.value = value

    @property
    def final_value(self) -> NumericDescriptor:
        """Final fitted value for the persisted parameter result."""
        return self._final_value

    def _set_final_value(self, value: float | None) -> None:
        """Set the final fitted value for internal callers."""
        self._final_value.value = value

    @property
    def final_uncertainty(self) -> NumericDescriptor:
        """Final uncertainty for the persisted parameter result."""
        return self._final_uncertainty

    def _set_final_uncertainty(self, value: float | None) -> None:
        """Set the final uncertainty for internal callers."""
        self._final_uncertainty.value = value

    @property
    def at_lower_bound(self) -> BoolDescriptor:
        """Whether the parameter finished at the lower fit bound."""
        return self._at_lower_bound

    def _set_at_lower_bound(self, *, value: bool) -> None:
        """Set the lower-bound flag for internal callers."""
        self._at_lower_bound.value = value

    @property
    def at_upper_bound(self) -> BoolDescriptor:
        """Whether the parameter finished at the upper fit bound."""
        return self._at_upper_bound

    def _set_at_upper_bound(self, *, value: bool) -> None:
        """Set the upper-bound flag for internal callers."""
        self._at_upper_bound.value = value


@DeterministicParameterResultsFactory.register
class DeterministicParameterResults(CategoryCollection):
    """Collection of persisted deterministic parameter-result rows."""

    type_info = TypeInfo(
        tag='default',
        description='Persisted deterministic parameter-result rows',
    )

    def __init__(self) -> None:
        super().__init__(item_type=DeterministicParameterResultItem)

    def create(
        self,
        *,
        param_unique_name: str,
        final_value: float | None = None,
        final_uncertainty: float | None = None,
        at_lower_bound: bool = False,
        at_upper_bound: bool = False,
    ) -> None:
        """
        Create a persisted deterministic parameter-result row.

        Parameters
        ----------
        param_unique_name : str
            Unique name of the persisted parameter result row.
        final_value : float | None, default=None
            Final fitted value for the persisted parameter result.
        final_uncertainty : float | None, default=None
            Final uncertainty for the persisted parameter result.
        at_lower_bound : bool, default=False
            Whether the parameter finished at the lower fit bound.
        at_upper_bound : bool, default=False
            Whether the parameter finished at the upper fit bound.
        """
        item = DeterministicParameterResultItem()
        item._set_param_unique_name(param_unique_name)
        item._set_final_value(final_value)
        item._set_final_uncertainty(final_uncertainty)
        item._set_at_lower_bound(value=at_lower_bound)
        item._set_at_upper_bound(value=at_upper_bound)
        self.add(item)
