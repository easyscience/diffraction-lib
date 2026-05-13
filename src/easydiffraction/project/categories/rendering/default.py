# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Project rendering category."""

from __future__ import annotations

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import MembershipValidator
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.display.plotting import Plotter
from easydiffraction.display.plotting import PlotterEngineEnum
from easydiffraction.display.tables import TableEngineEnum
from easydiffraction.display.tables import TableRenderer
from easydiffraction.io.cif.handler import CifHandler
from easydiffraction.io.cif.parse import read_cif_str
from easydiffraction.project.categories.rendering.factory import RenderingFactory
from easydiffraction.utils.logging import console
from easydiffraction.utils.utils import render_table


@RenderingFactory.register
class Rendering(CategoryItem):
    """Chart and table engine selection for a project."""

    type_info = TypeInfo(
        tag='default',
        description='Project rendering category',
    )

    def __init__(self) -> None:
        super().__init__()

        self._plotter = Plotter()
        self._tabler = TableRenderer.get()

        self._chart_engine = StringDescriptor(
            name='chart_engine',
            description='Chart renderer backend type',
            value_spec=AttributeSpec(
                default=self._plotter.engine,
                validator=MembershipValidator(
                    allowed=[member.value for member in PlotterEngineEnum],
                ),
            ),
            cif_handler=CifHandler(names=['_rendering.chart_engine']),
        )
        self._table_engine = StringDescriptor(
            name='table_engine',
            description='Table renderer backend type',
            value_spec=AttributeSpec(
                default=self._tabler.engine,
                validator=MembershipValidator(
                    allowed=[member.value for member in TableEngineEnum],
                ),
            ),
            cif_handler=CifHandler(names=['_rendering.table_engine']),
        )

        self._identity.category_code = 'rendering'

    @property
    def chart_engine(self) -> StringDescriptor:
        """Chart renderer backend type."""
        return self._chart_engine

    @chart_engine.setter
    def chart_engine(self, value: str) -> None:
        self._plotter.engine = value
        self._chart_engine.value = self._plotter.engine

    @property
    def table_engine(self) -> StringDescriptor:
        """Table renderer backend type."""
        return self._table_engine

    @table_engine.setter
    def table_engine(self, value: str) -> None:
        self._tabler.engine = value
        self._table_engine.value = self._tabler.engine

    @property
    def plotter(self) -> Plotter:
        """Live plotting facade bound to the owning project."""
        parent = getattr(self, '_parent', None)
        if parent is not None:
            self._plotter._set_project(parent)
        return self._plotter

    @property
    def tabler(self) -> TableRenderer:
        """Live table-rendering facade."""
        return self._tabler

    def show_chart_engines(self) -> None:
        """Print supported chart renderer backends."""
        self.plotter.show_supported_engines()

    def show_table_engines(self) -> None:
        """Print supported table renderer backends."""
        self.tabler.show_supported_engines()

    def show_config(self) -> None:
        """Print the current rendering configuration."""
        console.paragraph('Current rendering configuration')
        render_table(
            columns_headers=['Setting', 'Value'],
            columns_alignment=['left', 'left'],
            columns_data=[
                ['Chart engine', self.chart_engine.value],
                ['Table engine', self.table_engine.value],
            ],
        )

    def from_cif(self, block: object, idx: int = 0) -> None:
        """Populate this rendering category from a CIF block."""
        del idx
        chart_engine = read_cif_str(block, '_rendering.chart_engine')
        if chart_engine is not None:
            if chart_engine == self._plotter.engine:
                self._chart_engine.value = chart_engine
            else:
                self.chart_engine = chart_engine

        table_engine = read_cif_str(block, '_rendering.table_engine')
        if table_engine is not None:
            if table_engine == self._tabler.engine:
                self._table_engine.value = table_engine
            else:
                self.table_engine = table_engine