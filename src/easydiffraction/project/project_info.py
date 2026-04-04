# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Project metadata container used by Project."""

import datetime
import pathlib

from easydiffraction.core.guard import GuardedBase
from easydiffraction.io.cif.serialize import project_info_to_cif
from easydiffraction.utils.logging import console
from easydiffraction.utils.utils import render_cif


class ProjectInfo(GuardedBase):
    """Store project metadata: name, title, description, paths."""

    def __init__(
        self,
        name: str = 'untitled_project',
        title: str = 'Untitled Project',
        description: str = '',
    ) -> None:
        super().__init__()

        self._name = name
        self._title = title
        self._description = description
        self._path: pathlib.Path | None = None  # pathlib.Path.cwd()
        self._created: datetime.datetime = datetime.datetime.now()
        self._last_modified: datetime.datetime = datetime.datetime.now()

    @property
    def name(self) -> str:
        """Return the project name."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """
        Set the project name.

        Parameters
        ----------
        value : str
            New project name.
        """
        self._name = value

    @property
    def unique_name(self) -> str:
        """Unique name for GuardedBase diagnostics."""
        return self.name

    @property
    def title(self) -> str:
        """Return the project title."""
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        """
        Set the project title.

        Parameters
        ----------
        value : str
            New project title.
        """
        self._title = value

    @property
    def description(self) -> str:
        """Return sanitized description with single spaces."""
        return ' '.join(self._description.split())

    @description.setter
    def description(self, value: str) -> None:
        """
        Set the project description (whitespace normalized).

        Parameters
        ----------
        value : str
            New description text.
        """
        self._description = ' '.join(value.split())

    @property
    def path(self) -> pathlib.Path | None:
        """Return the project path as a Path object."""
        return self._path

    @path.setter
    def path(self, value: object) -> None:
        """
        Set the project directory path.

        Parameters
        ----------
        value : object
            New path as a :class:`str` or :class:`pathlib.Path`.
        """
        # Accept str or Path; normalize to Path
        self._path = pathlib.Path(value)

    @property
    def created(self) -> datetime.datetime:
        """Return the creation timestamp."""
        return self._created

    @property
    def last_modified(self) -> datetime.datetime:
        """Return the last modified timestamp."""
        return self._last_modified

    def update_last_modified(self) -> None:
        """Update the last modified timestamp."""
        self._last_modified = datetime.datetime.now()

    def parameters(self) -> None:
        """List parameters (not implemented)."""

    # TODO: Consider moving to io.cif.serialize
    def as_cif(self) -> str:
        """Export project metadata to CIF."""
        return project_info_to_cif(self)

    # TODO: Consider moving to io.cif.serialize
    def show_as_cif(self) -> None:
        """Pretty-print CIF via shared utilities."""
        paragraph_title: str = f"Project 📦 '{self.name}' info as CIF"
        cif_text: str = self.as_cif()
        console.paragraph(paragraph_title)
        render_cif(cif_text)
