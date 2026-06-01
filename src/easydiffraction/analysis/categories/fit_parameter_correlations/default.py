# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Persisted fit-parameter correlation summaries."""

from __future__ import annotations

from easydiffraction.analysis.categories.fit_parameter_correlations.factory import (
    FitParameterCorrelationsFactory,
)
from easydiffraction.analysis.enums import FitCorrelationSourceEnum
from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.validation import RegexValidator
from easydiffraction.core.variable import EnumDescriptor
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import CifHandler


def _normalized_parameter_pair(
    param_unique_name_i: str,
    param_unique_name_j: str,
) -> tuple[str, str]:
    """Return a stable ordering for a parameter pair."""
    if param_unique_name_i <= param_unique_name_j:
        return param_unique_name_i, param_unique_name_j
    return param_unique_name_j, param_unique_name_i


class FitParameterCorrelationItem(CategoryItem):
    """Single persisted fit-parameter correlation row."""

    _category_code = 'fit_parameter_correlation'
    _category_entry_name = 'id'

    def __init__(self) -> None:
        super().__init__()
        self._id = StringDescriptor(
            name='id',
            description='Stable identifier for the persisted correlation row.',
            value_spec=AttributeSpec(
                default='_',
                validator=RegexValidator(pattern=r'^[A-Za-z0-9_.:-]+$'),
            ),
            cif_handler=CifHandler(names=['_fit_parameter_correlation.id']),
        )
        self._source_kind = EnumDescriptor(
            name='source_kind',
            enum=FitCorrelationSourceEnum,
            description='Origin of the persisted correlation summary.',
            cif_handler=CifHandler(names=['_fit_parameter_correlation.source_kind']),
        )
        self._param_unique_name_i = StringDescriptor(
            name='param_unique_name_i',
            description='First unique parameter name in the persisted pair.',
            value_spec=AttributeSpec(
                default='_',
                validator=RegexValidator(pattern=r'^[A-Za-z_][A-Za-z0-9_.]*$'),
            ),
            cif_handler=CifHandler(names=['_fit_parameter_correlation.param_unique_name_i']),
        )
        self._param_unique_name_j = StringDescriptor(
            name='param_unique_name_j',
            description='Second unique parameter name in the persisted pair.',
            value_spec=AttributeSpec(
                default='_',
                validator=RegexValidator(pattern=r'^[A-Za-z_][A-Za-z0-9_.]*$'),
            ),
            cif_handler=CifHandler(names=['_fit_parameter_correlation.param_unique_name_j']),
        )
        self._correlation = NumericDescriptor(
            name='correlation',
            description='Persisted correlation coefficient for the parameter pair.',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=-1.0, le=1.0),
            ),
            cif_handler=CifHandler(names=['_fit_parameter_correlation.correlation']),
        )

    @property
    def id(self) -> StringDescriptor:
        """Stable identifier for the persisted correlation row."""
        return self._id

    def _set_id(self, value: str) -> None:
        """Set the persisted correlation-row id for internal callers."""
        self._id.value = value

    @property
    def source_kind(self) -> EnumDescriptor:
        """Origin of the persisted correlation summary."""
        return self._source_kind

    def _set_source_kind(self, value: str) -> None:
        """Set the correlation source kind for internal callers."""
        self._source_kind.value = value

    @property
    def param_unique_name_i(self) -> StringDescriptor:
        """First unique parameter name in the persisted pair."""
        return self._param_unique_name_i

    def _set_param_unique_name_i(self, value: str) -> None:
        """Set the first parameter name for internal callers."""
        self._param_unique_name_i.value = value

    @property
    def param_unique_name_j(self) -> StringDescriptor:
        """Second unique parameter name in the persisted pair."""
        return self._param_unique_name_j

    def _set_param_unique_name_j(self, value: str) -> None:
        """Set the second parameter name for internal callers."""
        self._param_unique_name_j.value = value

    @property
    def correlation(self) -> NumericDescriptor:
        """Persisted correlation coefficient for the parameter pair."""
        return self._correlation

    def _set_correlation(self, value: float) -> None:
        """Set the correlation coefficient for internal callers."""
        self._correlation.value = value


@FitParameterCorrelationsFactory.register
class FitParameterCorrelations(CategoryCollection):
    """Collection of persisted fit-parameter correlation summaries."""

    type_info = TypeInfo(
        tag='default',
        description='Persisted fit-parameter correlation summaries',
    )

    def __init__(self) -> None:
        super().__init__(item_type=FitParameterCorrelationItem)

    def create(
        self,
        *,
        source_kind: str,
        param_unique_name_i: str,
        param_unique_name_j: str,
        correlation: float,
        id: str | None = None,
    ) -> None:
        """
        Create a persisted fit-parameter correlation row.

        Parameters
        ----------
        source_kind : str
            Origin of the persisted correlation summary.
        param_unique_name_i : str
            First unique parameter name in the pair.
        param_unique_name_j : str
            Second unique parameter name in the pair.
        correlation : float
            Correlation coefficient for the parameter pair.
        id : str | None, default=None
            Explicit persisted row identifier. When omitted, a simple
            sequential identifier is generated.
        """
        normalized_i, normalized_j = _normalized_parameter_pair(
            param_unique_name_i,
            param_unique_name_j,
        )
        item = FitParameterCorrelationItem()
        item._set_source_kind(source_kind)
        item._set_param_unique_name_i(normalized_i)
        item._set_param_unique_name_j(normalized_j)
        item._set_correlation(correlation)
        resolved_id = id or str(len(self) + 1)
        item._set_id(resolved_id)
        self.add(item)
