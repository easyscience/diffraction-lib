# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.core.objects import Datablock
from easydiffraction.crystallography import crystallography as ecr
from easydiffraction.sample_models.collections.atom_sites import AtomSites
from easydiffraction.sample_models.components.cell import Cell
from easydiffraction.sample_models.components.space_group import SpaceGroup
from easydiffraction.utils.decorators import enforce_type
from easydiffraction.utils.formatting import paragraph
from easydiffraction.utils.utils import render_cif


class BaseSampleModel(Datablock):
    """Base sample model: structure container with only a name.

    Wraps crystallographic information including space group, cell, and
    atomic sites. Creation from CIF is handled by the factory; this base
    class accepts only the `name`.
    """

    _allowed_attributes = {
        'space_group',
        'cell',
        'atom_sites',
    }

    def __init__(self, name: str):
        super().__init__()
        self._name = name
        self.space_group = SpaceGroup()
        self.cell = Cell()
        self.atom_sites = AtomSites()

    # -----------
    # Space group
    # -----------

    @property
    def space_group(self):
        return self._space_group

    @space_group.setter
    @enforce_type
    def space_group(self, new_space_group: SpaceGroup):
        self._space_group = new_space_group

    # ----
    # Cell
    # ----

    @property
    def cell(self):
        return self._cell

    @cell.setter
    @enforce_type
    def cell(self, new_cell: Cell):
        self._cell = new_cell

    # ----------
    # Atom sites
    # ----------

    @property
    def atom_sites(self):
        return self._atom_sites

    @atom_sites.setter
    @enforce_type
    def atom_sites(self, new_atom_sites: AtomSites):
        self._atom_sites = new_atom_sites

    # --------------------
    # Symmetry constraints
    # --------------------

    def _apply_cell_symmetry_constraints(self):
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

    def _apply_atomic_coordinates_symmetry_constraints(self):
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
                #  For now, we just skip applying constraints if wyckoff
                #  letter is not set. Alternatively, could raise an
                #  error or warning
                #  print(f"Warning: Wyckoff letter is not ...")
                #  raise ValueError("Wyckoff letter is not ...")
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

    def _apply_atomic_displacement_symmetry_constraints(self):
        pass

    def apply_symmetry_constraints(self):
        self._apply_cell_symmetry_constraints()
        self._apply_atomic_coordinates_symmetry_constraints()
        self._apply_atomic_displacement_symmetry_constraints()

    # -----------
    # CIF methods
    # -----------

    def as_cif(self) -> str:
        """Export the sample model to CIF format.

        Returns:
            str: CIF string representation of the sample model.
        """
        # Data block header
        cif_lines = [f'data_{self.name}']

        # Space Group
        cif_lines += ['', self.space_group.as_cif]

        # Unit Cell
        cif_lines += ['', self.cell.as_cif]

        # Atom Sites
        cif_lines += ['', self.atom_sites.as_cif]

        return '\n'.join(cif_lines)

    # ------------
    # Show methods
    # ------------

    def show_structure(self):
        """Show an ASCII projection of the structure on a 2D plane."""
        print(paragraph(f"Sample model 🧩 '{self.name}' structure view"))
        print('Not implemented yet.')

    def show_params(self):
        """Display structural parameters (space group, unit cell, atomic
        sites).
        """
        print(f'\nSampleModel ID: {self.name}')
        print(f'Space group: {self.space_group.name_h_m}')
        print(f'Cell parameters: {self.cell.as_dict()}')
        print('Atom sites:')
        self.atom_sites.show()

    def show_as_cif(self) -> None:
        cif_text: str = self.as_cif()
        paragraph_title: str = paragraph(f"Sample model 🧩 '{self.name}' as cif")
        render_cif(cif_text, paragraph_title)


class SampleModel:
    """User-facing API for creating a sample model.

    Use keyword-only arguments:
    - `name` for a minimal, empty model
    - `cif_path` to load from a CIF file
    - `cif_str` to load from CIF content
    """

    def __new__(cls, **kwargs):
        # Lazy import to avoid circular import at module load time
        from easydiffraction.sample_models.sample_model_factory import SampleModelFactory

        return SampleModelFactory.create(**kwargs)
