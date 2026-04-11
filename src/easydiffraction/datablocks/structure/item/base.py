# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Structure datablock item."""

from typeguard import typechecked

from easydiffraction.core.datablock import DatablockItem
from easydiffraction.datablocks.structure.categories.atom_sites import AtomSites
from easydiffraction.datablocks.structure.categories.atom_sites.factory import AtomSitesFactory
from easydiffraction.datablocks.structure.categories.cell import Cell
from easydiffraction.datablocks.structure.categories.cell.factory import CellFactory
from easydiffraction.datablocks.structure.categories.space_group import SpaceGroup
from easydiffraction.datablocks.structure.categories.space_group.factory import SpaceGroupFactory
from easydiffraction.utils.logging import console
from easydiffraction.utils.utils import render_cif


class Structure(DatablockItem):
    """Structure datablock item."""

    def __init__(
        self,
        *,
        name: str,
    ) -> None:
        super().__init__()
        self._name = name
        self._cell_type: str = CellFactory.default_tag()
        self._cell = CellFactory.create(self._cell_type)
        self._space_group_type: str = SpaceGroupFactory.default_tag()
        self._space_group = SpaceGroupFactory.create(self._space_group_type)
        self._atom_sites_type: str = AtomSitesFactory.default_tag()
        self._atom_sites = AtomSitesFactory.create(self._atom_sites_type)
        self._identity.datablock_entry_name = lambda: self.name

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        """
        Name identifier for this structure.

        Returns
        -------
        str
            The structure's name.
        """
        return self._name

    @name.setter
    @typechecked
    def name(self, new: str) -> None:
        """
        Set the name identifier for this structure.

        Parameters
        ----------
        new : str
            New name string.
        """
        self._name = new

    # ------------------------------------------------------------------
    #  Cell (read-only, single type)
    # ------------------------------------------------------------------

    @property
    def cell(self) -> Cell:
        """Unit-cell category for this structure."""
        return self._cell

    @cell.setter
    @typechecked
    def cell(self, new: Cell) -> None:
        """
        Replace the unit-cell category for this structure.

        Parameters
        ----------
        new : Cell
            New unit-cell instance.
        """
        self._cell = new

    # ------------------------------------------------------------------
    #  Space group (read-only, single type)
    # ------------------------------------------------------------------

    @property
    def space_group(self) -> SpaceGroup:
        """Space-group category for this structure."""
        return self._space_group

    @space_group.setter
    @typechecked
    def space_group(self, new: SpaceGroup) -> None:
        """
        Replace the space-group category for this structure.

        Parameters
        ----------
        new : SpaceGroup
            New space-group instance.
        """
        self._space_group = new

    # ------------------------------------------------------------------
    #  Atom sites (read-only, single type)
    # ------------------------------------------------------------------

    @property
    def atom_sites(self) -> AtomSites:
        """Atom-sites collection for this structure."""
        return self._atom_sites

    @atom_sites.setter
    @typechecked
    def atom_sites(self, new: AtomSites) -> None:
        """
        Replace the atom-sites collection for this structure.

        Parameters
        ----------
        new : AtomSites
            New atom-sites collection.
        """
        self._atom_sites = new

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def show(self) -> None:
        """Display an ASCII projection of the structure in 2D."""
        console.paragraph(f"Structure 🧩 '{self.name}'")
        console.print('Not implemented yet.')

    def show_as_cif(self) -> None:
        """Render the CIF text for this structure in the terminal."""
        console.paragraph(f"Structure 🧩 '{self.name}' as cif")
        render_cif(self._cif_for_display())
