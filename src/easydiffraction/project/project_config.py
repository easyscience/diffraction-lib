# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Project configuration owner for singleton project categories."""

from __future__ import annotations

from easydiffraction.core.category_owner import CategoryOwner
from easydiffraction.project.categories.rendering_plot import RenderingPlot
from easydiffraction.project.categories.rendering_plot import RenderingPlotFactory
from easydiffraction.project.categories.info import ProjectInfo
from easydiffraction.project.categories.info import ProjectInfoFactory
from easydiffraction.project.categories.report import Report
from easydiffraction.project.categories.report import ReportFactory
from easydiffraction.project.categories.rendering_table import RenderingTable
from easydiffraction.project.categories.rendering_table import RenderingTableFactory
from easydiffraction.project.categories.style import Style
from easydiffraction.project.categories.style import StyleFactory
from easydiffraction.project.categories.verbosity import Verbosity
from easydiffraction.project.categories.verbosity import VerbosityFactory
from easydiffraction.project.categories.rendering_structure import RenderingStructure
from easydiffraction.project.categories.rendering_structure import RenderingStructureFactory
from easydiffraction.project.categories.structure_view import StructureView
from easydiffraction.project.categories.structure_view import StructureViewFactory
from easydiffraction.project.categories.structure_style import StructureStyle
from easydiffraction.project.categories.structure_style import StructureStyleFactory


class ProjectConfig(CategoryOwner):
    """Own singleton project configuration categories."""

    def __init__(
        self,
        name: str = 'untitled_project',
        title: str = 'Untitled Project',
        description: str = '',
    ) -> None:
        super().__init__()
        self._info = ProjectInfoFactory.create(
            ProjectInfoFactory.default_tag(),
            name=name,
            title=title,
            description=description,
        )
        self._rendering_plot = RenderingPlotFactory.create(RenderingPlotFactory.default_tag())
        self._report = ReportFactory.create(ReportFactory.default_tag())
        self._rendering_table = RenderingTableFactory.create(RenderingTableFactory.default_tag())
        self._verbosity = VerbosityFactory.create(VerbosityFactory.default_tag())
        self._rendering_structure = RenderingStructureFactory.create(RenderingStructureFactory.default_tag())
        self._structure_view = StructureViewFactory.create(StructureViewFactory.default_tag())
        self._structure_style = StructureStyleFactory.create(StructureStyleFactory.default_tag())
        self._style = StyleFactory.create(StyleFactory.default_tag())

    @property
    def info(self) -> ProjectInfo:
        """Project metadata category."""
        return self._info

    @property
    def rendering_plot(self) -> RenderingPlot:
        """Chart configuration category."""
        return self._rendering_plot

    @property
    def report(self) -> Report:
        """Report configuration category."""
        return self._report

    @property
    def rendering_table(self) -> RenderingTable:
        """Table configuration category."""
        return self._rendering_table

    @property
    def verbosity(self) -> Verbosity:
        """Verbosity configuration category."""
        return self._verbosity

    @property
    def rendering_structure(self) -> RenderingStructure:
        """Structure-view configuration category."""
        return self._rendering_structure

    @property
    def structure_view(self) -> StructureView:
        """Structure-view content and region category."""
        return self._structure_view

    @property
    def structure_style(self) -> StructureStyle:
        """Structure-view appearance category."""
        return self._structure_style

    @property
    def style(self) -> Style:
        """Structure-view styling category."""
        return self._style

    @property
    def as_cif(self) -> str:
        """Serialize singleton project categories to CIF."""
        from easydiffraction.io.cif.serialize import category_owner_to_cif  # noqa: PLC0415

        return category_owner_to_cif(self)
