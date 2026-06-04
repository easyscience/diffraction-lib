# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Structure datablock item."""

from typeguard import typechecked

from easydiffraction.core.datablock import DatablockItem
from easydiffraction.datablocks.structure.categories.atom_site_aniso import AtomSiteAnisoCollection
from easydiffraction.datablocks.structure.categories.atom_site_aniso.default import AtomSiteAniso
from easydiffraction.datablocks.structure.categories.atom_site_aniso.factory import (
    AtomSiteAnisoFactory,
)
from easydiffraction.datablocks.structure.categories.atom_sites import AtomSites
from easydiffraction.datablocks.structure.categories.atom_sites.enums import AdpTypeEnum
from easydiffraction.datablocks.structure.categories.atom_sites.factory import AtomSitesFactory
from easydiffraction.datablocks.structure.categories.cell import Cell
from easydiffraction.datablocks.structure.categories.cell.factory import CellFactory
from easydiffraction.datablocks.structure.categories.geom import Geom
from easydiffraction.datablocks.structure.categories.geom.factory import GeomFactory
from easydiffraction.datablocks.structure.categories.space_group import SpaceGroup
from easydiffraction.datablocks.structure.categories.space_group.factory import SpaceGroupFactory
from easydiffraction.datablocks.structure.categories.space_group_wyckoff import (
    SpaceGroupWyckoffCollection,
)
from easydiffraction.datablocks.structure.categories.space_group_wyckoff.factory import (
    SpaceGroupWyckoffFactory,
)
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
        self._atom_site_aniso_type: str = AtomSiteAnisoFactory.default_tag()
        self._atom_site_aniso = AtomSiteAnisoFactory.create(self._atom_site_aniso_type)
        self._geom_type: str = GeomFactory.default_tag()
        self._geom = GeomFactory.create(self._geom_type)
        self._space_group_wyckoff_type: str = SpaceGroupWyckoffFactory.default_tag()
        self._space_group_wyckoff = SpaceGroupWyckoffFactory.create(self._space_group_wyckoff_type)
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
    #  Atom site aniso (read-only, single type)
    # ------------------------------------------------------------------

    @property
    def atom_site_aniso(self) -> AtomSiteAnisoCollection:
        """Anisotropic-ADP collection for this structure."""
        return self._atom_site_aniso

    @atom_site_aniso.setter
    @typechecked
    def atom_site_aniso(self, new: AtomSiteAnisoCollection) -> None:
        """
        Replace the anisotropic-ADP collection for this structure.

        Parameters
        ----------
        new : AtomSiteAnisoCollection
            New aniso collection.
        """
        self._atom_site_aniso = new

    @property
    def geom(self) -> Geom:
        """Bond-geometry cutoffs for this structure."""
        return self._geom

    @geom.setter
    @typechecked
    def geom(self, new: Geom) -> None:
        """
        Replace the bond-geometry cutoffs for this structure.

        Parameters
        ----------
        new : Geom
            New bond-geometry-cutoff category.
        """
        self._geom = new

    @property
    def space_group_wyckoff(self) -> SpaceGroupWyckoffCollection:
        """
        Read-only Wyckoff table derived from the current space group.
        """
        return self._space_group_wyckoff

    # ------------------------------------------------------------------
    # Private methods
    # ------------------------------------------------------------------

    def _sync_atom_site_aniso(self) -> None:
        """
        Reconcile ``atom_site_aniso`` with anisotropic atoms only.

        Adds an entry for every atom whose ``adp_type`` is ``Bani`` or
        ``Uani``, removes entries whose label is stale or whose atom has
        switched to an isotropic type, and reorders CIF names on all
        atom-site parameters to match each atom's ``adp_type``.
        """
        aniso_types = {AdpTypeEnum.BANI, AdpTypeEnum.UANI}
        existing_labels = {a.label.value for a in self._atom_sites}
        aniso_labels_needed = {
            a.label.value for a in self._atom_sites if a.adp_type.value in aniso_types
        }
        current_aniso_labels = {a.label.value for a in self._atom_site_aniso}

        # Add missing entries for anisotropic atoms
        for atom in self._atom_sites:
            lbl = atom.label.value
            if lbl not in current_aniso_labels and atom.adp_type.value in aniso_types:
                entry = AtomSiteAniso()
                entry.label = lbl
                self._atom_site_aniso.add(entry)

        # Remove entries for isotropic atoms and stale labels
        stale = [
            a.label.value
            for a in self._atom_site_aniso
            if a.label.value not in existing_labels or a.label.value not in aniso_labels_needed
        ]
        for lbl in stale:
            self._atom_site_aniso.remove(lbl)

        # Reorder CIF names to match each atom's adp_type
        for atom in self._atom_sites:
            atom._reorder_adp_cif_names(atom.adp_type.value)

    def _update_categories(
        self,
        *,
        called_by_minimizer: bool = False,
    ) -> None:
        """Update categories with atom_site_aniso sync."""
        if not called_by_minimizer and not self._need_categories_update:
            return

        self._space_group_wyckoff._replace_from_space_group()
        self._sync_atom_site_aniso()

        for category in self.categories:
            category._update(called_by_minimizer=called_by_minimizer)

        self._need_categories_update = False

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def show_as_cif(self) -> None:
        """Render the CIF text for this structure in the terminal."""
        console.paragraph(f"Structure 🧩 '{self.name}' as cif")
        render_cif(self._cif_for_display())
