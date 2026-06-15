# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Project rendering_plot category."""

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
from easydiffraction.io.cif.handler import TagSpec
from easydiffraction.io.cif.parse import read_cif_str
from easydiffraction.project.categories.rendering_plot.factory import RenderingPlotFactory
from easydiffraction.utils.logging import log

AUTO_ENGINE = 'auto'
AUTO_DESCRIPTION = 'Environment default rendering_plot engine'
CHART_ENGINE_OPTIONS = [AUTO_ENGINE, *[member.value for member in PlotterEngineEnum]]


@RenderingPlotFactory.register
class RenderingPlot(CategoryItem, SwitchableCategoryBase):
    """RenderingPlot engine selection for a project."""

    _category_code = 'rendering_plot'
    _owner_attr_name = 'rendering_plot'
    _swap_method_name = '_swap_rendering_plot'

    type_info = TypeInfo(
        tag='default',
        description='Project rendering_plot category',
    )

    def __init__(self) -> None:
        super().__init__()

        self._plotter = Plotter()
        self._type = StringDescriptor(
            name='type',
            description='RenderingPlot renderer backend type',
            value_spec=AttributeSpec(
                default=AUTO_ENGINE,
                validator=MembershipValidator(
                    allowed=CHART_ENGINE_OPTIONS,
                ),
            ),
            tags=TagSpec(edi_names=['_rendering_plot.type']),
        )

    @staticmethod
    def _resolved_engine(value: str) -> str:
        if value == AUTO_ENGINE:
            return PlotterEngineEnum.default().value
        return value

    def _set_type(self, value: str, *, strict: bool = True) -> None:
        if value not in CHART_ENGINE_OPTIONS:
            msg = (
                f"Unsupported rendering_plot type '{value}'. "
                f'Supported: {CHART_ENGINE_OPTIONS}. '
                f"For more information, use 'rendering_plot.show_supported()'"
            )
            if strict:
                raise ValueError(msg)
            log.warning(msg)
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

    @staticmethod
    def _supported_types(
        filters: dict[str, object],
    ) -> list[tuple[str, str]]:
        """Return supported rendering_plot renderer backends."""
        del filters
        return [(AUTO_ENGINE, AUTO_DESCRIPTION), *PlotterFactory.descriptions()]

    def from_cif(self, block: object, idx: int = 0) -> None:
        """Populate this rendering_plot category from a CIF block."""
        del idx
        rendering_plot_type = read_cif_str(block, '_rendering_plot.type')
        if rendering_plot_type is None:
            return
        self._parent._swap_rendering_plot(rendering_plot_type, strict=False)
