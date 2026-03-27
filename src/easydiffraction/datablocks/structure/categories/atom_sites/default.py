# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Atom site category.

Defines :class:`AtomSite` items and :class:`AtomSites` collection used
in crystallographic structures.
"""

from __future__ import annotations

from cryspy.A_functions_base.database import DATABASE

from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import MembershipValidator
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.validation import RegexValidator
from easydiffraction.core.variable import Parameter
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.crystallography import crystallography as ecr
from easydiffraction.datablocks.structure.categories.atom_sites.factory import AtomSitesFactory
from easydiffraction.io.cif.handler import CifHandler


class AtomSite(CategoryItem):
    """
    Single atom site with fractional coordinates and ADP.

    Attributes are represented by descriptors to support validation and
    CIF serialization.
    """

    def __init__(self) -> None:
        """Initialise the atom site with default descriptor values."""
        super().__init__()

        self._label = StringDescriptor(
            name='label',
            description='Unique identifier for the atom site.',
            value_spec=AttributeSpec(
                default='Si',
                # TODO: the following pattern is valid for dict key
                #  (keywords are not checked). CIF label is less strict.
                #  Do we need conversion between CIF and internal label?
                validator=RegexValidator(pattern=r'^[A-Za-z_][A-Za-z0-9_]*$'),
            ),
            cif_handler=CifHandler(names=['_atom_site.label']),
        )
        self._type_symbol = StringDescriptor(
            name='type_symbol',
            description='Chemical symbol of the atom at this site.',
            value_spec=AttributeSpec(
                default='Tb',
                validator=MembershipValidator(allowed=self._type_symbol_allowed_values),
            ),
            cif_handler=CifHandler(names=['_atom_site.type_symbol']),
        )
        self._fract_x = Parameter(
            name='fract_x',
            description='Fractional x-coordinate of the atom site within the unit cell.',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_atom_site.fract_x']),
        )
        self._fract_y = Parameter(
            name='fract_y',
            description='Fractional y-coordinate of the atom site within the unit cell.',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_atom_site.fract_y']),
        )
        self._fract_z = Parameter(
            name='fract_z',
            description='Fractional z-coordinate of the atom site within the unit cell.',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_atom_site.fract_z']),
        )
        self._wyckoff_letter = StringDescriptor(
            name='wyckoff_letter',
            description='Wyckoff letter indicating the symmetry of the '
            'atom site within the space group.',
            value_spec=AttributeSpec(
                default=self._wyckoff_letter_default_value,
                validator=MembershipValidator(allowed=self._wyckoff_letter_allowed_values),
            ),
            cif_handler=CifHandler(
                names=[
                    '_atom_site.Wyckoff_letter',
                    '_atom_site.Wyckoff_symbol',
                ]
            ),
        )
        self._occupancy = Parameter(
            name='occupancy',
            description='Occupancy of the atom site, representing the '
            'fraction of the site occupied by the atom type.',
            value_spec=AttributeSpec(
                default=1.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_atom_site.occupancy']),
        )
        self._b_iso = Parameter(
            name='b_iso',
            description='Isotropic atomic displacement parameter (ADP) for the atom site.',
            units='Å²',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0.0),
            ),
            cif_handler=CifHandler(names=['_atom_site.B_iso_or_equiv']),
        )
        self._adp_type = StringDescriptor(
            name='adp_type',
            description='Type of atomic displacement parameter (ADP) '
            'used (e.g., Biso, Uiso, Uani, Bani).',
            value_spec=AttributeSpec(
                default='Biso',
                validator=MembershipValidator(allowed=['Biso']),
            ),
            cif_handler=CifHandler(names=['_atom_site.adp_type']),
        )

        self._identity.category_code = 'atom_site'
        self._identity.category_entry_name = lambda: str(self.label.value)

    # ------------------------------------------------------------------
    #  Private helper methods
    # ------------------------------------------------------------------

    @property
    def _type_symbol_allowed_values(self) -> list[str]:
        """
        Return chemical symbols accepted by *cryspy*.

        Returns
        -------
        list[str]
            Unique element/isotope symbols from the database.
        """
        return list({key[1] for key in DATABASE['Isotopes']})

    @property
    def _wyckoff_letter_allowed_values(self) -> list[str]:
        """
        Return allowed Wyckoff-letter symbols.

        Returns
        -------
        list[str]
            Currently a hard-coded placeholder list.
        """
        # TODO: Need to now current space group. How to access it? Via
        #  parent Cell? Then letters =
        #  list(SPACE_GROUPS[62, 'cab']['Wyckoff_positions'].keys())
        #  Temporarily return hardcoded list:
        return ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']

    @property
    def _wyckoff_letter_default_value(self) -> str:
        """
        Return the default Wyckoff letter.

        Returns
        -------
        str
            First element of the allowed values list.
        """
        # TODO: What to pass as default?
        return self._wyckoff_letter_allowed_values[0]

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def label(self) -> StringDescriptor:
        """
        Unique identifier for the atom site.

        Reading this property returns the underlying
        ``StringDescriptor`` object. Assigning to it updates the
        parameter value.
        """
        return self._label

    @label.setter
    def label(self, value: str) -> None:
        self._label.value = value

    @property
    def type_symbol(self) -> StringDescriptor:
        """
        Chemical symbol of the atom at this site.

        Reading this property returns the underlying
        ``StringDescriptor`` object. Assigning to it updates the
        parameter value.
        """
        return self._type_symbol

    @type_symbol.setter
    def type_symbol(self, value: str) -> None:
        self._type_symbol.value = value

    @property
    def adp_type(self) -> StringDescriptor:
        """
        ADP type used (e.g., Biso, Uiso, Uani, Bani).

        Reading this property returns the underlying
        ``StringDescriptor`` object. Assigning to it updates the
        parameter value.
        """
        return self._adp_type

    @adp_type.setter
    def adp_type(self, value: str) -> None:
        self._adp_type.value = value

    @property
    def wyckoff_letter(self) -> StringDescriptor:
        """
        Wyckoff letter for the atom site symmetry position.

        Reading this property returns the underlying
        ``StringDescriptor`` object. Assigning to it updates the
        parameter value.
        """
        return self._wyckoff_letter

    @wyckoff_letter.setter
    def wyckoff_letter(self, value: str) -> None:
        self._wyckoff_letter.value = value

    @property
    def fract_x(self) -> Parameter:
        """
        Fractional x-coordinate of the atom site within the unit cell.

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._fract_x

    @fract_x.setter
    def fract_x(self, value: float) -> None:
        self._fract_x.value = value

    @property
    def fract_y(self) -> Parameter:
        """
        Fractional y-coordinate of the atom site within the unit cell.

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._fract_y

    @fract_y.setter
    def fract_y(self, value: float) -> None:
        self._fract_y.value = value

    @property
    def fract_z(self) -> Parameter:
        """
        Fractional z-coordinate of the atom site within the unit cell.

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._fract_z

    @fract_z.setter
    def fract_z(self, value: float) -> None:
        self._fract_z.value = value

    @property
    def occupancy(self) -> Parameter:
        """
        Occupancy fraction of the atom type at this site.

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._occupancy

    @occupancy.setter
    def occupancy(self, value: float) -> None:
        self._occupancy.value = value

    @property
    def b_iso(self) -> Parameter:
        """
        Isotropic ADP for the atom site (Å²).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._b_iso

    @b_iso.setter
    def b_iso(self, value: float) -> None:
        self._b_iso.value = value


@AtomSitesFactory.register
class AtomSites(CategoryCollection):
    """Collection of :class:`AtomSite` instances."""

    type_info = TypeInfo(
        tag='default',
        description='Atom sites collection',
    )

    def __init__(self) -> None:
        """Initialise an empty atom-sites collection."""
        super().__init__(item_type=AtomSite)

    # ------------------------------------------------------------------
    #  Private helper methods
    # ------------------------------------------------------------------

    def _apply_atomic_coordinates_symmetry_constraints(self) -> None:
        """
        Apply symmetry rules to fractional coordinates of every site.

        Uses the parent structure's space-group symbol, IT coordinate
        system code and each atom's Wyckoff letter.  Atoms without a
        Wyckoff letter are silently skipped.
        """
        structure = self._parent
        space_group_name = structure.space_group.name_h_m.value
        space_group_coord_code = structure.space_group.it_coordinate_system_code.value
        for atom in self._items:
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

    def _update(
        self,
        called_by_minimizer: bool = False,
    ) -> None:
        """
        Recalculate atom sites after a change.

        Parameters
        ----------
        called_by_minimizer : bool, default=False
            Whether the update was triggered by the fitting minimizer.
            Currently unused.
        """
        del called_by_minimizer

        self._apply_atomic_coordinates_symmetry_constraints()
