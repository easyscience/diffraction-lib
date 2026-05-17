# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Project info category."""

from __future__ import annotations

import datetime
import pathlib

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import CifHandler
from easydiffraction.io.cif.serialize import project_info_to_cif
from easydiffraction.project.categories.info.factory import ProjectInfoFactory
from easydiffraction.utils.logging import console
from easydiffraction.utils.utils import render_cif

_PROJECT_TIMESTAMP_FORMAT = '%d %b %Y %H:%M:%S'


@ProjectInfoFactory.register
class ProjectInfo(CategoryItem):
    """Project metadata category."""

    type_info = TypeInfo(
        tag='default',
        description='Project metadata category',
    )

    def __init__(
        self,
        name: str = 'untitled_project',
        title: str = 'Untitled Project',
        description: str = '',
    ) -> None:
        super().__init__()

        created = datetime.datetime.now()
        last_modified = datetime.datetime.now()

        self._project_id = StringDescriptor(
            name='id',
            description='Project identifier',
            value_spec=AttributeSpec(default=name),
            cif_handler=CifHandler(names=['_project.id']),
        )
        self._title_descriptor = StringDescriptor(
            name='title',
            description='Project title',
            value_spec=AttributeSpec(default=title),
            cif_handler=CifHandler(names=['_project.title']),
        )
        self._description_descriptor = StringDescriptor(
            name='description',
            description='Project description',
            value_spec=AttributeSpec(default=' '.join(description.split())),
            cif_handler=CifHandler(names=['_project.description']),
        )
        self._created_descriptor = StringDescriptor(
            name='created',
            description='Project creation timestamp',
            value_spec=AttributeSpec(default=created.strftime(_PROJECT_TIMESTAMP_FORMAT)),
            cif_handler=CifHandler(names=['_project.created']),
        )
        self._last_modified_descriptor = StringDescriptor(
            name='last_modified',
            description='Project last-modified timestamp',
            value_spec=AttributeSpec(default=last_modified.strftime(_PROJECT_TIMESTAMP_FORMAT)),
            cif_handler=CifHandler(names=['_project.last_modified']),
        )
        self._path: pathlib.Path | None = None

        self._identity.category_code = 'project'

    @staticmethod
    def _parse_timestamp(value: str) -> datetime.datetime:
        """Parse project timestamp text from CIF storage format."""
        return datetime.datetime.strptime(value, _PROJECT_TIMESTAMP_FORMAT)

    @staticmethod
    def _format_timestamp(value: datetime.datetime) -> str:
        """Format a project timestamp for CIF storage."""
        return value.strftime(_PROJECT_TIMESTAMP_FORMAT)

    @property
    def unique_name(self) -> str:
        """Unique name for GuardedBase diagnostics."""
        return self.name

    @property
    def name(self) -> str:
        """Return the project name."""
        return self._project_id.value

    @name.setter
    def name(self, value: str) -> None:
        self._project_id.value = value

    @property
    def title(self) -> str:
        """Return the project title."""
        return self._title_descriptor.value

    @title.setter
    def title(self, value: str) -> None:
        self._title_descriptor.value = value

    @property
    def description(self) -> str:
        """Return sanitized description with single spaces."""
        return ' '.join(self._description_descriptor.value.split())

    @description.setter
    def description(self, value: str) -> None:
        self._description_descriptor.value = ' '.join(value.split())

    @property
    def path(self) -> pathlib.Path | None:
        """Return the project path as a Path object."""
        return self._path

    @path.setter
    def path(self, value: object) -> None:
        """Set the project directory path."""
        self._path = pathlib.Path(value)

    @property
    def created(self) -> datetime.datetime:
        """Return the creation timestamp."""
        return self._parse_timestamp(self._created_descriptor.value)

    def _set_created(self, value: datetime.datetime | str) -> None:
        """Set the creation timestamp from runtime or CIF input."""
        if isinstance(value, datetime.datetime):
            self._created_descriptor.value = self._format_timestamp(value)
            return
        self._created_descriptor.value = value

    @property
    def last_modified(self) -> datetime.datetime:
        """Return the last modified timestamp."""
        return self._parse_timestamp(self._last_modified_descriptor.value)

    def _set_last_modified(self, value: datetime.datetime | str) -> None:
        """Set the last-modified timestamp from runtime or CIF input."""
        if isinstance(value, datetime.datetime):
            self._last_modified_descriptor.value = self._format_timestamp(value)
            return
        self._last_modified_descriptor.value = value

    def update_last_modified(self) -> None:
        """Update the last modified timestamp."""
        self._set_last_modified(datetime.datetime.now())

    @property
    def as_cif(self) -> str:
        """Export project metadata to CIF."""
        return project_info_to_cif(self)

    def show_as_cif(self) -> None:
        """Pretty-print CIF via shared utilities."""
        paragraph_title = f"Project 📦 '{self.name}' info as CIF"
        console.paragraph(paragraph_title)
        render_cif(self.as_cif)