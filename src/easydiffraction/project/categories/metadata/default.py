# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Project metadata category."""

from __future__ import annotations

import datetime
import pathlib

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import CifHandler
from easydiffraction.io.cif.serialize import project_metadata_to_cif
from easydiffraction.project.categories.metadata.factory import ProjectMetadataFactory
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log
from easydiffraction.utils.utils import render_cif

_PROJECT_TIMESTAMP_FORMAT = '%d %b %Y %H:%M:%S'


@ProjectMetadataFactory.register
class ProjectMetadata(CategoryItem):
    """Project metadata category."""

    _category_code = 'metadata'

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

        self._validate_name(name)

        created = datetime.datetime.now(tz=datetime.UTC)
        last_modified = datetime.datetime.now(tz=datetime.UTC)

        self._project_id = StringDescriptor(
            name='name',
            description='Project identifier',
            value_spec=AttributeSpec(default=name),
            cif_handler=CifHandler(
                names=['_metadata.name'],
                import_names=['_project.id'],
                iucr_name='_project.id',
            ),
        )
        self._title_descriptor = StringDescriptor(
            name='title',
            description='Project title',
            value_spec=AttributeSpec(default=title),
            cif_handler=CifHandler(
                names=['_metadata.title'],
                import_names=['_project.title'],
                iucr_name='_project.title',
            ),
        )
        self._description_descriptor = StringDescriptor(
            name='description',
            description='Project description',
            value_spec=AttributeSpec(default=' '.join(description.split())),
            cif_handler=CifHandler(
                names=['_metadata.description'],
                import_names=['_project.description'],
                iucr_name='_project.description',
            ),
        )
        self._created_descriptor = StringDescriptor(
            name='created',
            description='Project creation timestamp',
            value_spec=AttributeSpec(default=created.strftime(_PROJECT_TIMESTAMP_FORMAT)),
            cif_handler=CifHandler(
                names=['_metadata.created'],
                import_names=['_project.created'],
                iucr_name='_project.created',
            ),
        )
        self._last_modified_descriptor = StringDescriptor(
            name='last_modified',
            description='Project last-modified timestamp',
            value_spec=AttributeSpec(default=last_modified.strftime(_PROJECT_TIMESTAMP_FORMAT)),
            cif_handler=CifHandler(
                names=['_metadata.last_modified'],
                import_names=['_project.last_modified'],
                iucr_name='_project.last_modified',
            ),
        )
        self._timestamp_descriptor = StringDescriptor(
            name='timestamp',
            description='Project fit timestamp',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(
                names=['_metadata.timestamp'],
                import_names=['_software.timestamp'],
                iucr_name='_easydiffraction_project.timestamp',
            ),
        )
        self._path: pathlib.Path | None = None

    @staticmethod
    def _validate_name(value: str) -> None:
        """Reject project names containing a path separator."""
        if '/' in value or '\\' in value:
            log.error(
                f"Project name {value!r} must not contain a path separator ('/' or '\\').",
                exc_type=ValueError,
            )

    @staticmethod
    def _parse_timestamp(value: str) -> datetime.datetime:
        """Parse project timestamp text from STAR storage format."""
        return datetime.datetime.strptime(value, _PROJECT_TIMESTAMP_FORMAT).replace(
            tzinfo=datetime.UTC,
        )

    @staticmethod
    def _normalize_timestamp(value: datetime.datetime) -> datetime.datetime:
        """Return timestamps as UTC-aware datetimes."""
        if value.tzinfo is None:
            return value.replace(tzinfo=datetime.UTC)
        return value.astimezone(datetime.UTC)

    @staticmethod
    def _format_timestamp(value: datetime.datetime) -> str:
        """Format a project timestamp for STAR storage."""
        return ProjectMetadata._normalize_timestamp(value).strftime(_PROJECT_TIMESTAMP_FORMAT)

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
        self._validate_name(value)
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

    @property
    def last_modified(self) -> datetime.datetime:
        """Return the last modified timestamp."""
        return self._parse_timestamp(self._last_modified_descriptor.value)

    @property
    def timestamp(self) -> str | None:
        """Return the latest fit timestamp."""
        return self._timestamp_descriptor.value

    @timestamp.setter
    def timestamp(self, value: str | None) -> None:
        self._timestamp_descriptor.value = value

    def _set_last_modified(self, value: datetime.datetime | str) -> None:
        """
        Set the last-modified timestamp from runtime or STAR input.
        """
        if isinstance(value, datetime.datetime):
            self._last_modified_descriptor.value = self._format_timestamp(value)
            return
        self._last_modified_descriptor.value = value

    def update_last_modified(self) -> None:
        """Update the last modified timestamp."""
        self._set_last_modified(datetime.datetime.now(tz=datetime.UTC))

    @property
    def as_cif(self) -> str:
        """Export project metadata to Edifa."""
        return project_metadata_to_cif(self)

    def show_as_text(self) -> None:
        """Pretty-print the project metadata as text."""
        paragraph_title = f"Project 📦 '{self.name}' metadata as text"
        console.paragraph(paragraph_title)
        render_cif(self.as_cif)
