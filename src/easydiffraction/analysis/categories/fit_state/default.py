# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Fit-state schema metadata category."""

from __future__ import annotations

from easydiffraction.analysis.categories.fit_state.factory import FitStateFactory
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.io.cif.handler import CifHandler


@FitStateFactory.register
class FitState(CategoryItem):
    """Persisted fit-state schema metadata."""

    _category_code = 'fit_state'

    type_info = TypeInfo(
        tag='default',
        description='Persisted fit-state schema metadata',
    )

    def __init__(self) -> None:
        super().__init__()
        self._schema_version = NumericDescriptor(
            name='schema_version',
            description='Persisted fit-state schema version.',
            value_spec=AttributeSpec(default=1),
            cif_handler=CifHandler(names=['_fit_state.schema_version']),
        )

    @property
    def schema_version(self) -> NumericDescriptor:
        """Persisted fit-state schema version."""
        return self._schema_version

    def _set_schema_version(self, value: float) -> None:
        """Set the fit-state schema version for internal callers."""
        self._schema_version.value = value
