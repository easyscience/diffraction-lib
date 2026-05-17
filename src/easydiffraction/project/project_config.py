# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Project configuration owner for singleton project categories."""

from __future__ import annotations

from easydiffraction.core.category_owner import CategoryOwner
from easydiffraction.project.categories.info import ProjectInfo
from easydiffraction.project.categories.info import ProjectInfoFactory
from easydiffraction.project.categories.rendering import Rendering
from easydiffraction.project.categories.rendering import RenderingFactory


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
        self._rendering = RenderingFactory.create(RenderingFactory.default_tag())

    @property
    def info(self) -> ProjectInfo:
        """Project metadata category."""
        return self._info

    @property
    def rendering(self) -> Rendering:
        """Rendering configuration category."""
        return self._rendering

    @property
    def as_cif(self) -> str:
        """Serialize singleton project categories to CIF."""
        from easydiffraction.io.cif.serialize import category_owner_to_cif  # noqa: PLC0415

        return category_owner_to_cif(self)