# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Atom site category.

Defines :class:`AtomSite` items and :class:`AtomSites` collection used
in crystallographic structures.
"""

from __future__ import annotations

import math

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
from easydiffraction.datablocks.structure.categories.atom_sites.enums import AdpTypeEnum
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
                validator=RangeValidator(ge=0.0, le=1.0),
            ),
            cif_handler=CifHandler(names=['_atom_site.occupancy']),
        )
        self._adp_iso = Parameter(
            name='adp_iso',
            description='Isotropic atomic displacement parameter (ADP) for the atom site.',
            units='Å²',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0.0, le=10.0),
            ),
            cif_handler=CifHandler(
                names=[
                    '_atom_site.B_iso_or_equiv',
                    '_atom_site.U_iso_or_equiv',
                ]
            ),
        )
        self._adp_type = StringDescriptor(
            name='adp_type',
            description='Type of atomic displacement parameter (ADP) '
            'used (e.g., Biso, Uiso, Uani, Bani).',
            value_spec=AttributeSpec(
                default=AdpTypeEnum.default(),
                validator=MembershipValidator(allowed=[m.value for m in AdpTypeEnum]),
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

    def _convert_adp_values(self, old_type: str, new_type: str) -> None:
        """
        Convert ADP values when the type changes.

        Handles B ↔ U conversion using B = 8π²U and iso ↔ ani seeding.

        Parameters
        ----------
        old_type : str
            Previous ADP type value.
        new_type : str
            New ADP type value.
        """
        old_enum = AdpTypeEnum(old_type)
        new_enum = AdpTypeEnum(new_type)
        factor = 8.0 * math.pi**2
        old_is_b = old_enum in {AdpTypeEnum.BISO, AdpTypeEnum.BANI}
        new_is_u = new_enum in {AdpTypeEnum.UISO, AdpTypeEnum.UANI}
        old_is_iso = old_enum in {AdpTypeEnum.BISO, AdpTypeEnum.UISO}
        new_is_iso = new_enum in {AdpTypeEnum.BISO, AdpTypeEnum.UISO}

        # Ani → Iso: collapse tensor to scalar first (in old units)
        if not old_is_iso and new_is_iso:
            self._collapse_aniso_to_iso()

        # B ↔ U conversion for iso value
        if old_is_b and new_is_u:
            self._adp_iso.value /= factor
        elif not old_is_b and not new_is_u:
            self._adp_iso.value *= factor

        # Iso → Ani: seed diagonal from (already converted) adp_iso
        if old_is_iso and not new_is_iso:
            self._seed_aniso_from_iso()
        elif not old_is_iso and not new_is_iso:
            # Ani → Ani (e.g. Bani→Uani): apply B↔U to aniso values
            aniso = self._get_aniso_entry()
            if aniso is not None:
                self._convert_aniso_values(
                    aniso,
                    old_is_b=old_is_b,
                    new_is_u=new_is_u,
                    factor=factor,
                )

    def _seed_aniso_from_iso(self) -> None:
        """Seed aniso diagonal from current adp_iso value."""
        aniso = self._get_aniso_entry()
        if aniso is None:
            # Entry not yet created; force sync on parent
            structure = getattr(self._parent, '_parent', None)
            if structure is not None and hasattr(structure, '_sync_atom_site_aniso'):
                structure._sync_atom_site_aniso()
                aniso = self._get_aniso_entry()
        if aniso is None:
            return
        iso_val = self._adp_iso.value
        aniso.adp_11 = iso_val
        aniso.adp_22 = iso_val
        aniso.adp_33 = iso_val
        aniso.adp_12 = 0.0
        aniso.adp_13 = 0.0
        aniso.adp_23 = 0.0

    def _collapse_aniso_to_iso(self) -> None:
        """
        Set adp_iso to the mean of the aniso diagonal.

        Writes directly to ``_value`` to bypass range validation,
        because intermediate minimizer steps can produce negative
        anisotropic components whose mean falls outside the nominal
        ``[0, 100]`` range.
        """
        aniso = self._get_aniso_entry()
        if aniso is None:
            return
        self._adp_iso._value = (aniso.adp_11.value + aniso.adp_22.value + aniso.adp_33.value) / 3.0

    def _get_aniso_entry(self) -> object | None:
        """Return the matching AtomSiteAniso entry, or None."""
        # _parent is absent before the atom is added to a collection
        if '_parent' not in self.__dict__:
            return None
        structure = getattr(self._parent, '_parent', None)
        if structure is None:
            return None
        aniso_coll = getattr(structure, '_atom_site_aniso', None)
        if aniso_coll is None:
            return None
        lbl = self._label.value
        if lbl in aniso_coll:
            return aniso_coll[lbl]
        return None

    @staticmethod
    def _convert_aniso_values(
        aniso: object,
        *,
        old_is_b: bool,
        new_is_u: bool,
        factor: float,
    ) -> None:
        """Apply B↔U conversion to all six aniso tensor components."""
        if old_is_b and new_is_u:
            for attr in ('adp_11', 'adp_22', 'adp_33', 'adp_12', 'adp_13', 'adp_23'):
                p = getattr(aniso, attr)
                p.value /= factor
        elif not old_is_b and not new_is_u:
            for attr in ('adp_11', 'adp_22', 'adp_33', 'adp_12', 'adp_13', 'adp_23'):
                p = getattr(aniso, attr)
                p.value *= factor

    def _reorder_adp_cif_names(self, new_type: str) -> None:
        """
        Reorder CIF names on adp_iso and aniso params for serialisation.

        Parameters
        ----------
        new_type : str
            The new ADP type value.
        """
        is_u = AdpTypeEnum(new_type) in {AdpTypeEnum.UISO, AdpTypeEnum.UANI}
        if is_u:
            self._adp_iso._cif_handler._names = [
                '_atom_site.U_iso_or_equiv',
                '_atom_site.B_iso_or_equiv',
            ]
        else:
            self._adp_iso._cif_handler._names = [
                '_atom_site.B_iso_or_equiv',
                '_atom_site.U_iso_or_equiv',
            ]

        # Reorder aniso CIF names
        aniso = self._get_aniso_entry()
        if aniso is None:
            return
        for suffix in ('11', '22', '33', '12', '13', '23'):
            param = getattr(aniso, f'_adp_{suffix}')
            if is_u:
                param._cif_handler._names = [
                    f'_atom_site_aniso.U_{suffix}',
                    f'_atom_site_aniso.B_{suffix}',
                ]
            else:
                param._cif_handler._names = [
                    f'_atom_site_aniso.B_{suffix}',
                    f'_atom_site_aniso.U_{suffix}',
                ]

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
        old_type = self._adp_type.value
        self._adp_type.value = value
        new_type = self._adp_type.value
        if old_type != new_type:
            self._convert_adp_values(old_type, new_type)
            self._reorder_adp_cif_names(new_type)
            parent = getattr(self, '_parent', None)
            if parent is not None:
                parent._propagate_adp_convention(self)

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
    def adp_iso(self) -> Parameter:
        """
        Isotropic ADP for the atom site (Å²).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._adp_iso

    @adp_iso.setter
    def adp_iso(self, value: float) -> None:
        self._adp_iso.value = value

    @property
    def adp_iso_as_b(self) -> float:
        """
        Return the isotropic ADP as a B-factor value.

        When ``adp_type`` is ``Uiso`` or ``Uani`` the stored U value is
        converted to B via B = 8π²U.  Otherwise the stored value is
        returned unchanged.

        Returns
        -------
        float
            Equivalent B_iso value.
        """
        if AdpTypeEnum(self._adp_type.value) in {AdpTypeEnum.UISO, AdpTypeEnum.UANI}:
            return self._adp_iso.value * 8.0 * math.pi**2
        return self._adp_iso.value


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

    def _propagate_adp_convention(self, source: AtomSite) -> None:
        """
        Align all atoms to the B/U convention of *source*.

        When an atom switches between B and U convention, all siblings
        are converted to the same convention so that CIF loop headers
        remain consistent.

        Parameters
        ----------
        source : AtomSite
            The atom whose convention just changed.
        """
        new_enum = AdpTypeEnum(source._adp_type.value)
        target_is_u = new_enum in {AdpTypeEnum.UISO, AdpTypeEnum.UANI}

        for atom in self._items:
            if atom is source:
                continue
            sib_enum = AdpTypeEnum(atom._adp_type.value)
            sib_is_u = sib_enum in {AdpTypeEnum.UISO, AdpTypeEnum.UANI}
            if sib_is_u == target_is_u:
                continue
            sib_is_iso = sib_enum in {AdpTypeEnum.BISO, AdpTypeEnum.UISO}
            if target_is_u:
                target = AdpTypeEnum.UISO if sib_is_iso else AdpTypeEnum.UANI
            else:
                target = AdpTypeEnum.BISO if sib_is_iso else AdpTypeEnum.BANI
            old_sib = atom._adp_type.value
            atom._adp_type._value = target.value
            atom._convert_adp_values(old_sib, target.value)
            atom._reorder_adp_cif_names(target.value)

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

    def _apply_adp_symmetry_constraints(self) -> None:
        """
        Apply symmetry rules to anisotropic ADP tensor components.

        For each atom with an anisotropic ADP type and a Wyckoff letter,
        enforces the tensor constraints dictated by the site symmetry.
        Also sets ``free = False`` on tensor components that are fixed
        by symmetry and on ``adp_iso`` for all anisotropic atoms.
        """
        structure = self._parent
        aniso_types = {AdpTypeEnum.BANI.value, AdpTypeEnum.UANI.value}
        space_group_name = structure.space_group.name_h_m.value
        space_group_coord_code = structure.space_group.it_coordinate_system_code.value
        aniso_collection = structure.atom_site_aniso

        for atom in self._items:
            if atom.adp_type.value not in aniso_types:
                continue
            # Isotropic ADP is not refinable for aniso atoms
            atom._adp_iso.free = False
            wl = atom.wyckoff_letter.value
            if not wl:
                continue
            lbl = atom.label.value
            if lbl not in aniso_collection:
                continue
            aniso_entry = aniso_collection[lbl]
            dummy = {
                'adp_11': aniso_entry.adp_11.value,
                'adp_22': aniso_entry.adp_22.value,
                'adp_33': aniso_entry.adp_33.value,
                'adp_12': aniso_entry.adp_12.value,
                'adp_13': aniso_entry.adp_13.value,
                'adp_23': aniso_entry.adp_23.value,
            }
            site_fract = (
                atom.fract_x.value,
                atom.fract_y.value,
                atom.fract_z.value,
            )
            dummy, ref_i = ecr.apply_atom_site_aniso_symmetry_constraints(
                atom_site_aniso=dummy,
                name_hm=space_group_name,
                coord_code=space_group_coord_code,
                _wyckoff_letter=wl,
                site_fract=site_fract,
            )
            adp_keys = ('adp_11', 'adp_22', 'adp_33', 'adp_12', 'adp_13', 'adp_23')
            for key, is_free in zip(adp_keys, ref_i, strict=False):
                param = getattr(aniso_entry, key)
                param.value = dummy[key]
                if not is_free:
                    param.free = False

    def _sync_iso_from_aniso(self) -> None:
        """
        Update ``adp_iso`` from the anisotropic tensor for aniso atoms.

        For every atom whose ADP type is anisotropic (Bani / Uani), sets
        ``adp_iso`` to the mean of the three diagonal tensor components
        so that the isotropic value stays consistent with the current
        tensor state.
        """
        aniso_types = {AdpTypeEnum.BANI.value, AdpTypeEnum.UANI.value}
        for atom in self._items:
            if atom.adp_type.value in aniso_types:
                atom._collapse_aniso_to_iso()

    def _update(
        self,
        *,
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
        self._apply_adp_symmetry_constraints()
        self._sync_iso_from_aniso()
