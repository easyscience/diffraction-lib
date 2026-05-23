# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Project chart category."""

from __future__ import annotations

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.switchable import SwitchableCategoryBase
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import MembershipValidator
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.display.plotting import Plotter
from easydiffraction.display.plotting import PlotterEngineEnum
from easydiffraction.display.plotting import PlotterFactory
from easydiffraction.io.cif.handler import CifHandler
from easydiffraction.io.cif.parse import read_cif_str
from easydiffraction.project.categories.chart.factory import ChartFactory

AUTO_ENGINE = 'auto'
AUTO_DESCRIPTION = 'Environment default chart engine'
CHART_ENGINE_OPTIONS = [AUTO_ENGINE, *[member.value for member in PlotterEngineEnum]]


@ChartFactory.register
class Chart(CategoryItem, SwitchableCategoryBase):
    """Chart engine selection for a project."""

    _category_code = 'chart'
    _owner_attr_name = 'chart'
    _swap_method_name = '_swap_chart'

    type_info = TypeInfo(
        tag='default',
        description='Project chart category',
    )

    def __init__(self) -> None:
        super().__init__()

        self._plotter = Plotter()
        self._type = StringDescriptor(
            name='type',
            description='Chart renderer backend type',
            value_spec=AttributeSpec(
                default=AUTO_ENGINE,
                validator=MembershipValidator(
                    allowed=CHART_ENGINE_OPTIONS,
                ),
            ),
            cif_handler=CifHandler(names=['_chart.type']),
        )

    @staticmethod
    def _resolved_engine(value: str) -> str:
        if value == AUTO_ENGINE:
            return PlotterEngineEnum.default().value
        return value

    def _set_type(self, value: str) -> None:
        if value not in CHART_ENGINE_OPTIONS:
            self._plotter.engine = value
            return

        resolved_engine = self._resolved_engine(value)
        if self._plotter.engine != resolved_engine:
            self._plotter.engine = resolved_engine
        self._type.value = value

    @property
    def plotter(self) -> Plotter:
        """Live plotting facade bound to the owning project."""
        owner = getattr(self, '_parent', None)
        if owner is not None:
            self._plotter._set_project(owner)
        return self._plotter

    def _supported_types(
        self,
        filters: dict[str, object],
    ) -> list[tuple[str, str]]:
        """Return supported chart renderer backends."""
        del filters
        return [(AUTO_ENGINE, AUTO_DESCRIPTION), *PlotterFactory.descriptions()]

    def from_cif(self, block: object, idx: int = 0) -> None:
        """Populate this chart category from a CIF block."""
        del idx
        chart_type = read_cif_str(block, '_chart.type')
        if chart_type is None:
            return
        parent = getattr(self, '_parent', None)
        if parent is None:
            self._set_type(chart_type)
            return
        parent._swap_chart(chart_type)
