# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
from typing import Optional

from easydiffraction.core.categories import CategoryCollection
from easydiffraction.core.categories import CategoryItem
from easydiffraction.core.parameters import Descriptor
from easydiffraction.core.parameters import Parameter


class AtomSite(CategoryItem):
    """Represents a single atom site within the crystal structure."""

    _class_public_attrs = {
        'name',
        'label',
        'type_symbol',
        'fract_x',
        'fract_y',
        'fract_z',
        'wyckoff_letter',
        'occupancy',
        'b_iso',
        'adp_type',
    }

    @property
    def category_key(self):
        return 'atom_sites'

    def __init__(
        self,
        label: Optional[str] = None,
        type_symbol: Optional[str] = None,
        fract_x: Optional[float] = None,
        fract_y: Optional[float] = None,
        fract_z: Optional[float] = None,
        wyckoff_letter: Optional[str] = None,
        occupancy: Optional[float] = None,
        b_iso: Optional[float] = None,
        adp_type: Optional[str] = None,
    ):  # TODO: add support for Uiso, Uani and Bani
        super().__init__()

        self.label = Descriptor(
            value=label,
            name='label',
            value_type=str,
            default_value='La',
            full_cif_names=['_atom_site.label'],
            description='Unique identifier for the atom site.',
        )
        self.type_symbol = Descriptor(
            value=type_symbol,
            name='type_symbol',
            value_type=str,
            default_value='La',
            full_cif_names=['_atom_site.type_symbol'],
            description='Chemical symbol of the atom at this site.',
        )
        self.adp_type = Descriptor(
            value=adp_type,
            name='adp_type',
            value_type=str,
            default_value='Biso',
            full_cif_names=['_atom_site.ADP_type'],
            description='Type of atomic displacement parameter (ADP) '
            'used (e.g., Biso, Uiso, Uani, Bani).',
        )
        self.wyckoff_letter = Descriptor(
            value=wyckoff_letter,
            name='wyckoff_letter',
            value_type=str,
            default_value=None,
            full_cif_names=['_atom_site.Wyckoff_letter', '_atom_site.Wyckoff_symbol'],
            description='Wyckoff letter indicating the symmetry of the '
            'atom site within the space group.',
        )
        self.fract_x = Parameter(
            value=fract_x,
            name='fract_x',
            default_value=0.0,
            full_cif_names=['_atom_site.fract_x'],
            description='Fractional x-coordinate of the atom site within the unit cell.',
        )
        self.fract_y = Parameter(
            value=fract_y,
            name='fract_y',
            default_value=0.0,
            full_cif_names=['_atom_site.fract_y'],
            description='Fractional y-coordinate of the atom site within the unit cell.',
        )
        self.fract_z = Parameter(
            value=fract_z,
            name='fract_z',
            default_value=0.0,
            full_cif_names=['_atom_site.fract_z'],
            description='Fractional z-coordinate of the atom site within the unit cell.',
        )
        self.occupancy = Parameter(
            value=occupancy,
            name='occupancy',
            default_value=1.0,
            physical_min=0.0,
            physical_max=1.0,
            full_cif_names=['_atom_site.occupancy'],
            description='Occupancy of the atom site, representing the '
            'fraction of the site occupied by the atom type.',
        )
        self.b_iso = Parameter(
            value=b_iso,
            name='b_iso',
            units='Å²',
            default_value=0.0,
            physical_min=0.0,
            full_cif_names=['_atom_site.B_iso_or_equiv'],
            description='Isotropic atomic displacement parameter (ADP) for the atom site.',
        )
        self._category_entry_attr_name = self.label.name
        self.name = self.label.value


class AtomSites(CategoryCollection):
    """Collection of AtomSite instances."""

    def __init__(self):
        super().__init__(item_type=AtomSite)
