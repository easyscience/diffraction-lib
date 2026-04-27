# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Project display category."""

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
from easydiffraction.project.categories.display.factory import DisplayFactory


@DisplayFactory.register
class Display(CategoryItem):
    """Display engine selection and access for a project."""

    type_info = TypeInfo(
        tag='default',
        description='Project display category',
    )

    def __init__(self) -> None:
        super().__init__()

        self._plotter = Plotter()
        self._tabler = TableRenderer.get()

        self._plotter_type = StringDescriptor(
            name='plotter_type',
            description='Plot renderer backend type',
            value_spec=AttributeSpec(
                default=self._plotter.engine,
                validator=MembershipValidator(
                    allowed=[member.value for member in PlotterEngineEnum],
                ),
            ),
            cif_handler=CifHandler(names=['_display.plotter_type']),
        )
        self._tabler_type = StringDescriptor(
            name='tabler_type',
            description='Table renderer backend type',
            value_spec=AttributeSpec(
                default=self._tabler.engine,
                validator=MembershipValidator(
                    allowed=[member.value for member in TableEngineEnum],
                ),
            ),
            cif_handler=CifHandler(names=['_display.tabler_type']),
        )

        self._identity.category_code = 'display'

    @property
    def plotter_type(self) -> StringDescriptor:
        """Plot renderer backend type."""
        return self._plotter_type

    @plotter_type.setter
    def plotter_type(self, value: str) -> None:
        self._plotter.engine = value
        self._plotter_type.value = self._plotter.engine

    @property
    def tabler_type(self) -> StringDescriptor:
        """Table renderer backend type."""
        return self._tabler_type

    @tabler_type.setter
    def tabler_type(self, value: str) -> None:
        self._tabler.engine = value
        self._tabler_type.value = self._tabler.engine

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

    def show_plotter_types(self) -> None:
        """Print supported plot renderer backends."""
        self.plotter.show_supported_engines()

    def show_tabler_types(self) -> None:
        """Print supported table renderer backends."""
        self.tabler.show_supported_engines()

    def from_cif(self, block: object, idx: int = 0) -> None:
        """Populate this display category from a CIF block."""
        del idx
        plotter_type = read_cif_str(block, '_display.plotter_type')
        if plotter_type is not None:
            if plotter_type == self._plotter.engine:
                self._plotter_type.value = plotter_type
            else:
                self.plotter_type = plotter_type

        tabler_type = read_cif_str(block, '_display.tabler_type')
        if tabler_type is not None:
            if tabler_type == self._tabler.engine:
                self._tabler_type.value = tabler_type
            else:
                self.tabler_type = tabler_type
