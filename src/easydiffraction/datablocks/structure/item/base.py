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
from easydiffraction.utils.logging import log
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
    #  Cell (switchable-category pattern)
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

    @property
    def cell_type(self) -> str:
        """Tag of the active unit-cell type."""
        return self._cell_type

    @cell_type.setter
    def cell_type(self, new_type: str) -> None:
        """
        Switch to a different unit-cell type.

        Parameters
        ----------
        new_type
            Cell tag (e.g. ``'default'``).
        """
        supported_tags = CellFactory.supported_tags()
        if new_type not in supported_tags:
            log.warning(
                f"Unsupported cell type '{new_type}'. "
                f'Supported: {supported_tags}. '
                f"For more information, use 'show_supported_cell_types()'",
            )
            return
        self._cell = CellFactory.create(new_type)
        self._cell_type = new_type
        console.paragraph(f"Cell type for structure '{self.name}' changed to")
        console.print(new_type)

    def show_supported_cell_types(self) -> None:
        """Print a table of supported unit-cell types."""
        CellFactory.show_supported()

    def show_current_cell_type(self) -> None:
        """Print the currently used unit-cell type."""
        console.paragraph('Current cell type')
        console.print(self.cell_type)

    # ------------------------------------------------------------------
    #  Space group (switchable-category pattern)
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

    @property
    def space_group_type(self) -> str:
        """Tag of the active space-group type."""
        return self._space_group_type

    @space_group_type.setter
    def space_group_type(self, new_type: str) -> None:
        """
        Switch to a different space-group type.

        Parameters
        ----------
        new_type
            Space-group tag (e.g. ``'default'``).
        """
        supported_tags = SpaceGroupFactory.supported_tags()
        if new_type not in supported_tags:
            log.warning(
                f"Unsupported space group type '{new_type}'. "
                f'Supported: {supported_tags}. '
                f"For more information, use 'show_supported_space_group_types()'",
            )
            return
        self._space_group = SpaceGroupFactory.create(new_type)
        self._space_group_type = new_type
        console.paragraph(f"Space group type for structure '{self.name}' changed to")
        console.print(new_type)

    def show_supported_space_group_types(self) -> None:
        """Print a table of supported space-group types."""
        SpaceGroupFactory.show_supported()

    def show_current_space_group_type(self) -> None:
        """Print the currently used space-group type."""
        console.paragraph('Current space group type')
        console.print(self.space_group_type)

    # ------------------------------------------------------------------
    #  Atom sites (switchable-category pattern)
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

    @property
    def atom_sites_type(self) -> str:
        """Tag of the active atom-sites collection type."""
        return self._atom_sites_type

    @atom_sites_type.setter
    def atom_sites_type(self, new_type: str) -> None:
        """
        Switch to a different atom-sites collection type.

        Parameters
        ----------
        new_type
            Atom-sites tag (e.g. ``'default'``).
        """
        supported_tags = AtomSitesFactory.supported_tags()
        if new_type not in supported_tags:
            log.warning(
                f"Unsupported atom sites type '{new_type}'. "
                f'Supported: {supported_tags}. '
                f"For more information, use 'show_supported_atom_sites_types()'",
            )
            return
        self._atom_sites = AtomSitesFactory.create(new_type)
        self._atom_sites_type = new_type
        console.paragraph(f"Atom sites type for structure '{self.name}' changed to")
        console.print(new_type)

    def show_supported_atom_sites_types(self) -> None:
        """Print a table of supported atom-sites collection types."""
        AtomSitesFactory.show_supported()

    def show_current_atom_sites_type(self) -> None:
        """Print the currently used atom-sites collection type."""
        console.paragraph('Current atom sites type')
        console.print(self.atom_sites_type)

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def show(self) -> None:
        """Display an ASCII projection of the structure on a 2D
        plane.
        """
        console.paragraph(f"Structure 🧩 '{self.name}'")
        console.print('Not implemented yet.')

    def show_as_cif(self) -> None:
        """Render the CIF text for this structure in the terminal."""
        console.paragraph(f"Structure 🧩 '{self.name}' as cif")
        render_cif(self.as_cif)
