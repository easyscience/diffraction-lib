# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Structure datablock item."""

from typeguard import typechecked

from easydiffraction.core.datablock import DatablockItem
from easydiffraction.crystallography import crystallography as ecr
from easydiffraction.datablocks.structure.categories.atom_sites import AtomSites
from easydiffraction.datablocks.structure.categories.cell import Cell
from easydiffraction.datablocks.structure.categories.space_group import SpaceGroup
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
        self._cell: Cell = Cell()
        self._space_group: SpaceGroup = SpaceGroup()
        self._atom_sites: AtomSites = AtomSites()
        self._identity.datablock_entry_name = lambda: self.name

    # ------------------------------------------------------------------
    # Private helper methods
    # ------------------------------------------------------------------

    def _apply_cell_symmetry_constraints(self) -> None:
        """Apply symmetry rules to unit-cell parameters in place."""
        dummy_cell = {
            'lattice_a': self.cell.length_a.value,
            'lattice_b': self.cell.length_b.value,
            'lattice_c': self.cell.length_c.value,
            'angle_alpha': self.cell.angle_alpha.value,
            'angle_beta': self.cell.angle_beta.value,
            'angle_gamma': self.cell.angle_gamma.value,
        }
        space_group_name = self.space_group.name_h_m.value
        ecr.apply_cell_symmetry_constraints(cell=dummy_cell, name_hm=space_group_name)
        self.cell.length_a.value = dummy_cell['lattice_a']
        self.cell.length_b.value = dummy_cell['lattice_b']
        self.cell.length_c.value = dummy_cell['lattice_c']
        self.cell.angle_alpha.value = dummy_cell['angle_alpha']
        self.cell.angle_beta.value = dummy_cell['angle_beta']
        self.cell.angle_gamma.value = dummy_cell['angle_gamma']

    def _apply_atomic_coordinates_symmetry_constraints(self) -> None:
        """Apply symmetry rules to fractional coordinates of atom
        sites.
        """
        space_group_name = self.space_group.name_h_m.value
        space_group_coord_code = self.space_group.it_coordinate_system_code.value
        for atom in self.atom_sites:
            dummy_atom = {
                'fract_x': atom.fract_x.value,
                'fract_y': atom.fract_y.value,
                'fract_z': atom.fract_z.value,
            }
            wl = atom.wyckoff_letter.value
            if not wl:
                # TODO: Decide how to handle this case
                continue
            ecr.apply_atom_site_symmetry_constraints(
                atom_site=dummy_atom,
                name_hm=space_group_name,
                coord_code=space_group_coord_code,
                wyckoff_letter=wl,
            )
            atom.fract_x.value = dummy_atom['fract_x']
            atom.fract_y.value = dummy_atom['fract_y']
            atom.fract_z.value = dummy_atom['fract_z']

    def _apply_atomic_displacement_symmetry_constraints(self) -> None:
        """Apply symmetry constraints to atomic displacement parameters.

        Not yet implemented.
        """
        pass

    def _apply_symmetry_constraints(self) -> None:
        """Apply all available symmetry constraints to this
        structure.
        """
        self._apply_cell_symmetry_constraints()
        self._apply_atomic_coordinates_symmetry_constraints()
        self._apply_atomic_displacement_symmetry_constraints()

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        """Name identifier for this structure.

        Returns:
            str: The structure's name.
        """
        return self._name

    @name.setter
    @typechecked
    def name(self, new: str) -> None:
        """Set the name identifier for this structure.

        Args:
            new (str): New name string.
        """
        self._name = new

    @property
    def cell(self) -> Cell:
        """Unit-cell category for this structure.

        Returns:
            Cell: The unit-cell instance.
        """
        return self._cell

    @cell.setter
    @typechecked
    def cell(self, new: Cell) -> None:
        """Replace the unit-cell category for this structure.

        Args:
            new (Cell): New unit-cell instance.
        """
        self._cell = new

    @property
    def space_group(self) -> SpaceGroup:
        """Space-group category for this structure.

        Returns:
            SpaceGroup: The space-group instance.
        """
        return self._space_group

    @space_group.setter
    @typechecked
    def space_group(self, new: SpaceGroup) -> None:
        """Replace the space-group category for this structure.

        Args:
            new (SpaceGroup): New space-group instance.
        """
        self._space_group = new

    @property
    def atom_sites(self) -> AtomSites:
        """Atom-sites collection for this structure.

        Returns:
            AtomSites: The atom-sites collection instance.
        """
        return self._atom_sites

    @atom_sites.setter
    @typechecked
    def atom_sites(self, new: AtomSites) -> None:
        """Replace the atom-sites collection for this structure.

        Args:
            new (AtomSites): New atom-sites collection.
        """
        self._atom_sites = new

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
