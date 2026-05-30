# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Project configuration owner for singleton project categories."""

from __future__ import annotations

from easydiffraction.core.category_owner import CategoryOwner
from easydiffraction.project.categories.chart import Chart
from easydiffraction.project.categories.chart import ChartFactory
from easydiffraction.project.categories.info import ProjectInfo
from easydiffraction.project.categories.info import ProjectInfoFactory
from easydiffraction.project.categories.report import Report
from easydiffraction.project.categories.report import ReportFactory
from easydiffraction.project.categories.table import Table
from easydiffraction.project.categories.table import TableFactory
from easydiffraction.project.categories.style import Style
from easydiffraction.project.categories.style import StyleFactory
from easydiffraction.project.categories.verbosity import Verbosity
from easydiffraction.project.categories.verbosity import VerbosityFactory
from easydiffraction.project.categories.view import View
from easydiffraction.project.categories.view import ViewFactory


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
        self._chart = ChartFactory.create(ChartFactory.default_tag())
        self._report = ReportFactory.create(ReportFactory.default_tag())
        self._table = TableFactory.create(TableFactory.default_tag())
        self._verbosity = VerbosityFactory.create(VerbosityFactory.default_tag())
        self._view = ViewFactory.create(ViewFactory.default_tag())
        self._style = StyleFactory.create(StyleFactory.default_tag())

    @property
    def info(self) -> ProjectInfo:
        """Project metadata category."""
        return self._info

    @property
    def chart(self) -> Chart:
        """Chart configuration category."""
        return self._chart

    @property
    def report(self) -> Report:
        """Report configuration category."""
        return self._report

    @property
    def table(self) -> Table:
        """Table configuration category."""
        return self._table

    @property
    def verbosity(self) -> Verbosity:
        """Verbosity configuration category."""
        return self._verbosity

    @property
    def view(self) -> View:
        """Structure-view configuration category."""
        return self._view

    @property
    def style(self) -> Style:
        """Structure-view styling category."""
        return self._style

    @property
    def as_cif(self) -> str:
        """Serialize singleton project categories to CIF."""
        from easydiffraction.io.cif.serialize import category_owner_to_cif  # noqa: PLC0415

        return category_owner_to_cif(self)
