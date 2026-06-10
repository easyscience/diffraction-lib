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
from easydiffraction.core.display_handler import DisplayHandler
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import MembershipValidator
from easydiffraction.core.validation import PermissiveMembershipValidator
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.validation import RegexValidator
from easydiffraction.core.variable import EnumDescriptor
from easydiffraction.core.variable import IntegerDescriptor
from easydiffraction.core.variable import Parameter
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.crystallography import crystallography as ecr
from easydiffraction.datablocks.structure.categories.atom_sites.enums import AdpTypeEnum
from easydiffraction.datablocks.structure.categories.atom_sites.factory import AtomSitesFactory
from easydiffraction.io.cif.handler import CifHandler
from easydiffraction.utils.logging import log


class AtomSite(CategoryItem):
    """
    Single atom site with fractional coordinates and ADP.

    Attributes are represented by descriptors to support validation and
    CIF serialization.
    """

    _category_code = 'atom_site'
    _category_entry_name = 'label'

    def __init__(self) -> None:
        """Initialise the atom site with default descriptor values."""
        super().__init__()
        # Set when a Wyckoff letter is assigned without a parent context
        # (e.g. create() before the atom is added); the update flow then
        # validates it once the parent structure is available.
        self._wyckoff_letter_needs_validation = False
        # Wyckoff-detection baselines (None until first detection);
        # compared in the update flow to decide whether to re-detect.
        self._wyckoff_coord_baseline: tuple[float, float, float] | None = None
        self._wyckoff_key_baseline: tuple[str, str | None] | None = None

        self._label = StringDescriptor(
            name='label',
            description='Unique identifier for the atom site.',
            display_handler=DisplayHandler(
                display_name='Label',
                latex_name='Label',
            ),
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
            display_handler=DisplayHandler(
                display_name='Type',
                latex_name='Type',
            ),
            value_spec=AttributeSpec(
                default='Tb',
                validator=MembershipValidator(allowed=self._type_symbol_allowed_values),
            ),
            cif_handler=CifHandler(names=['_atom_site.type_symbol']),
        )
        self._fract_x = Parameter(
            name='fract_x',
            description='Fractional x-coordinate of the atom site within the unit cell.',
            display_handler=DisplayHandler(
                display_name='x',
                latex_name=r'$x$',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_atom_site.fract_x']),
        )
        self._fract_y = Parameter(
            name='fract_y',
            description='Fractional y-coordinate of the atom site within the unit cell.',
            display_handler=DisplayHandler(
                display_name='y',
                latex_name=r'$y$',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_atom_site.fract_y']),
        )
        self._fract_z = Parameter(
            name='fract_z',
            description='Fractional z-coordinate of the atom site within the unit cell.',
            display_handler=DisplayHandler(
                display_name='z',
                latex_name=r'$z$',
            ),
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
            display_handler=DisplayHandler(
                display_name='Wyckoff',
                latex_name='Wyckoff',
            ),
            value_spec=AttributeSpec(
                default=self._wyckoff_letter_default_value,
                validator=PermissiveMembershipValidator(
                    allowed=lambda: self._wyckoff_letter_allowed_values,
                ),
            ),
            cif_handler=CifHandler(
                names=[
                    '_atom_site.Wyckoff_symbol',
                    '_atom_site.Wyckoff_letter',
                    '_atom_site.wyckoff_letter',
                ]
            ),
        )
        self._multiplicity = IntegerDescriptor(
            name='multiplicity',
            description='Site multiplicity derived from the Wyckoff '
            'position; None for an untabulated space group.',
            display_handler=DisplayHandler(
                display_name='Mult.',
                latex_name='Mult.',
            ),
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_atom_site.site_symmetry_multiplicity']),
        )
        self._occupancy = Parameter(
            name='occupancy',
            description='Occupancy of the atom site, representing the '
            'fraction of the site occupied by the atom type.',
            display_handler=DisplayHandler(
                display_name='Occ.',
                latex_name='Occ.',
            ),
            value_spec=AttributeSpec(
                default=1.0,
                validator=RangeValidator(ge=0.0, le=1.0),
            ),
            cif_handler=CifHandler(names=['_atom_site.occupancy']),
        )
        self._adp_iso = Parameter(
            name='adp_iso',
            description='Isotropic atomic displacement parameter (ADP) for the atom site.',
            units='angstrom_squared',
            display_handler=DisplayHandler(
                display_name='Uiso',
                display_units='Å²',
                latex_name=r'$U_{\mathrm{iso}}$',
                latex_units=r'\AA$^2$',
            ),
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
        self._adp_type = EnumDescriptor(
            name='adp_type',
            enum=AdpTypeEnum,
            description='Type of atomic displacement parameter (ADP) '
            'used (e.g., Biso, Uiso, Uani, Bani).',
            display_handler=DisplayHandler(
                display_name='ADP type',
                latex_name='ADP type',
            ),
            cif_handler=CifHandler(names=['_atom_site.ADP_type', '_atom_site.adp_type']),
        )

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

    def _resolve_structure_space_group(self) -> object | None:
        """
        Return the parent structure's space-group category, or ``None``.

        Walks ``AtomSite`` → atom-sites collection → structure; returns
        ``None`` when any link is missing (no parent context yet).
        """
        collection = getattr(self, '_parent', None)
        structure = getattr(collection, '_parent', None) if collection is not None else None
        return getattr(structure, 'space_group', None) if structure is not None else None

    @property
    def _wyckoff_letter_allowed_values(self) -> list[str]:
        """
        Allowed Wyckoff letters for the current space group.

        Returns
        -------
        list[str]
            ``['', *letters]`` for a tabulated space group (empty first,
            so an unset letter is valid); ``[]`` when there is no parent
            context or the space group is untabulated.
        """
        space_group = self._resolve_structure_space_group()
        if space_group is None:
            return []
        positions = ecr.space_group_wyckoff_table(
            space_group.name_h_m.value,
            space_group.it_coordinate_system_code.value,
        )
        if positions is None:
            return []
        return ['', *positions]

    @property
    def _wyckoff_letter_default_value(self) -> str:
        """
        Return the default Wyckoff letter.

        Returns
        -------
        str
            The first allowed value (empty string), or ``''`` when no
            letters are allowed.
        """
        allowed = self._wyckoff_letter_allowed_values
        return allowed[0] if allowed else ''

    def _convert_adp_values(self, old_type: str, new_type: str) -> None:
        """
        Convert ADP values when the type changes.

        Handles B ↔ U conversion using B = 8π²U and iso ↔ ani seeding.
        Conversions to or from the dimensionless ``beta`` tensor are
        cell-dependent and delegated to :meth:`_convert_adp_values_beta`.

        Parameters
        ----------
        old_type : str
            Previous ADP type value.
        new_type : str
            New ADP type value.
        """
        old_enum = AdpTypeEnum(old_type)
        new_enum = AdpTypeEnum(new_type)
        if AdpTypeEnum.BETA in (old_enum, new_enum):
            self._convert_adp_values_beta(old_enum, new_enum)
            return
        factor = 8.0 * math.pi**2
        old_is_b = old_enum in {AdpTypeEnum.BISO, AdpTypeEnum.BANI}
        new_is_u = new_enum in {AdpTypeEnum.UISO, AdpTypeEnum.UANI}
        old_is_iso = old_enum in {AdpTypeEnum.BISO, AdpTypeEnum.UISO}
        new_is_iso = new_enum in {AdpTypeEnum.BISO, AdpTypeEnum.UISO}

        # Ani → Iso: collapse tensor to scalar first (in old units)
        if not old_is_iso and new_is_iso:
            self._collapse_aniso_to_iso()
            structure = getattr(getattr(self, '_parent', None), '_parent', None)
            if structure is not None and hasattr(structure, '_sync_atom_site_aniso'):
                structure._sync_atom_site_aniso()

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
        Set adp_iso to the equivalent isotropic value from the tensor.

        Writes directly to ``_value`` to bypass range validation,
        because intermediate minimizer steps can produce negative
        anisotropic components whose mean falls outside the nominal
        ``[0, 100]`` range. For a beta atom the dimensionless diagonal is
        mapped to U first (via the reciprocal cell), so the stored
        equivalent is a real U magnitude consistent with the Uani type
        rather than a dimensionless beta value.
        """
        aniso = self._get_aniso_entry()
        if aniso is None:
            return
        if self._adp_type.value == AdpTypeEnum.BETA.value:
            diag = self._beta_diagonal_as_u(aniso)
        else:
            diag = (aniso.adp_11.value, aniso.adp_22.value, aniso.adp_33.value)
        self._adp_iso._value = (diag[0] + diag[1] + diag[2]) / 3.0

    def _beta_diagonal_as_u(self, aniso: object) -> tuple[float, float, float]:
        """
        Return the U-tensor diagonal ``(U11, U22, U33)`` for a beta atom.

        Maps the dimensionless beta diagonal back to U via the reciprocal
        cell (``U_ii = beta_ii / (2*pi**2 * a*_i**2)``).

        Parameters
        ----------
        aniso : object
            The atom's :class:`AtomSiteAniso` entry holding beta values.

        Returns
        -------
        tuple[float, float, float]
            The equivalent U diagonal components.
        """
        a_star, b_star, c_star = self._reciprocal_lengths_for_conversion()
        two_pi_sq = 2.0 * math.pi**2
        return (
            aniso.adp_11.value / (two_pi_sq * a_star * a_star),
            aniso.adp_22.value / (two_pi_sq * b_star * b_star),
            aniso.adp_33.value / (two_pi_sq * c_star * c_star),
        )

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

    def _convert_adp_values_beta(self, old_enum: AdpTypeEnum, new_enum: AdpTypeEnum) -> None:
        """
        Convert ADP values to or from the dimensionless beta tensor.

        The beta transform is cell-dependent
        (``beta_ij = 2*pi**2 * U_ij * a*_i * a*_j``), so it routes through
        the parent structure's reciprocal cell and pivots on the U
        tensor. ``beta`` is always anisotropic, so switching from an
        isotropic type seeds the diagonal first and switching to an
        isotropic type collapses it afterwards.

        Parameters
        ----------
        old_enum : AdpTypeEnum
            Previous ADP type.
        new_enum : AdpTypeEnum
            New ADP type.

        Raises
        ------
        ValueError
            If no parent unit cell is reachable for the conversion.
        """
        factor = 8.0 * math.pi**2
        two_pi_sq = 2.0 * math.pi**2
        suffixes = ('11', '22', '33', '12', '13', '23')
        a_star, b_star, c_star = self._reciprocal_lengths_for_conversion()
        pairs = (
            a_star * a_star,
            b_star * b_star,
            c_star * c_star,
            a_star * b_star,
            a_star * c_star,
            b_star * c_star,
        )

        if new_enum is AdpTypeEnum.BETA:
            # Build a U tensor (seeding the diagonal from the iso value
            # first when coming from an isotropic type), then map U → β.
            if old_enum in {AdpTypeEnum.BISO, AdpTypeEnum.UISO}:
                self._seed_aniso_from_iso()
            aniso = self._get_aniso_entry()
            if aniso is None:
                return
            if old_enum in {AdpTypeEnum.BISO, AdpTypeEnum.BANI}:
                for suffix in suffixes:
                    getattr(aniso, f'_adp_{suffix}').value /= factor
            for suffix, pair in zip(suffixes, pairs):
                p = getattr(aniso, f'_adp_{suffix}')
                p.value = two_pi_sq * p.value * pair
            return

        # old_enum is BETA, new_enum is a B/U type: map β → U, then
        # apply U → B and/or collapse the diagonal to the iso value.
        aniso = self._get_aniso_entry()
        if aniso is None:
            return
        for suffix, pair in zip(suffixes, pairs):
            p = getattr(aniso, f'_adp_{suffix}')
            p.value = p.value / (two_pi_sq * pair)
        if new_enum in {AdpTypeEnum.BISO, AdpTypeEnum.BANI}:
            for suffix in suffixes:
                getattr(aniso, f'_adp_{suffix}').value *= factor
        if new_enum in {AdpTypeEnum.BISO, AdpTypeEnum.UISO}:
            self._collapse_aniso_to_iso()
            structure = getattr(getattr(self, '_parent', None), '_parent', None)
            if structure is not None and hasattr(structure, '_sync_atom_site_aniso'):
                structure._sync_atom_site_aniso()

    def _reciprocal_lengths_for_conversion(self) -> tuple[float, float, float]:
        """
        Return ``(a*, b*, c*)`` from the parent structure's cell.

        Returns
        -------
        tuple[float, float, float]
            Reciprocal-cell edge lengths in inverse angstrom.

        Raises
        ------
        ValueError
            If the atom has no reachable parent cell, so a beta
            conversion cannot be performed safely.
        """
        structure = getattr(getattr(self, '_parent', None), '_parent', None)
        cell = getattr(structure, 'cell', None) if structure is not None else None
        if cell is None:
            msg = (
                f"Cannot convert the ADP type to or from 'beta' for atom "
                f"'{self._label.value}': no unit cell is reachable. Add the atom "
                f'to a structure with a defined cell before switching to or from '
                f'the beta tensor.'
            )
            raise ValueError(msg)
        return ecr.reciprocal_cell_lengths(
            cell.length_a.value,
            cell.length_b.value,
            cell.length_c.value,
            cell.angle_alpha.value,
            cell.angle_beta.value,
            cell.angle_gamma.value,
        )

    def _reorder_adp_cif_names(self, new_type: str) -> None:
        """
        Reorder CIF names on adp_iso and aniso params for serialisation.

        Parameters
        ----------
        new_type : str
            The new ADP type value.
        """
        if AdpTypeEnum(new_type) is AdpTypeEnum.BETA:
            self._reorder_adp_cif_names_beta()
            return
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

    def _reorder_adp_cif_names_beta(self) -> None:
        """Put the beta-family CIF names first for a beta-tensor atom."""
        # adp_iso has no beta form; keep its B/U-equivalent ordering.
        self._adp_iso._cif_handler._names = [
            '_atom_site.B_iso_or_equiv',
            '_atom_site.U_iso_or_equiv',
        ]
        aniso = self._get_aniso_entry()
        if aniso is None:
            return
        for suffix in ('11', '22', '33', '12', '13', '23'):
            param = getattr(aniso, f'_adp_{suffix}')
            param._cif_handler._names = [
                f'_atom_site_aniso.beta_{suffix}',
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
    def adp_type(self) -> EnumDescriptor:
        """
        ADP type used (e.g., Biso, Uiso, Uani, Bani).

        Reading this property returns the underlying ``EnumDescriptor``
        object. Assigning to it updates the parameter value.
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
        if self._resolve_structure_space_group() is None:
            # No parent context yet (e.g. create() before the atom is
            # added): store the raw value and defer validation to the
            # update flow, which resolves it once context is available.
            self._wyckoff_letter_needs_validation = True
            self._wyckoff_letter._set_value_from_minimizer(value)
        else:
            self._wyckoff_letter.value = value

    @property
    def multiplicity(self) -> IntegerDescriptor:
        """
        Read-only site multiplicity derived from the Wyckoff position.

        Populated by Wyckoff detection; ``value`` is ``None`` when the
        space group is untabulated. There is no public setter.
        """
        return self._multiplicity

    def _set_wyckoff_letter_detected(self, letter: str) -> None:
        """
        Set the auto-detected Wyckoff letter, bypassing validation.

        Modelled on ``_set_value_from_minimizer``: detection supplies a
        trusted letter, written directly rather than re-validated
        against the (dynamic) allowed-letters set.
        """
        self._wyckoff_letter._set_value_from_minimizer(letter)

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
        converted to B via B = 8π²U. For a ``beta`` atom the equivalent
        B is computed straight from the dimensionless beta tensor via the
        reciprocal cell (independent of the stored ``adp_iso``), so it is
        never stale after a type switch. Otherwise the stored value is
        returned unchanged.

        Returns
        -------
        float
            Equivalent B_iso value.
        """
        adp_enum = AdpTypeEnum(self._adp_type.value)
        if adp_enum is AdpTypeEnum.BETA:
            aniso = self._get_aniso_entry()
            if aniso is None:
                return self._adp_iso.value
            u_diag = self._beta_diagonal_as_u(aniso)
            return (u_diag[0] + u_diag[1] + u_diag[2]) / 3.0 * 8.0 * math.pi**2
        if adp_enum in {AdpTypeEnum.UISO, AdpTypeEnum.UANI}:
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

    def _apply_atomic_coordinates_symmetry_constraints(
        self, *, called_by_minimizer: bool = False
    ) -> None:
        """
        Detect Wyckoff letters and snap coordinates to symmetry.

        For each atom: resolve any pending no-context Wyckoff letter;
        (re)detect the letter when it is empty or the coordinates /
        space-group key changed (skipped under a minimizer); snap
        coordinates to the selected orbit representative; and record the
        multiplicity and constrained-axis flags. Atoms in an untabulated
        space group keep their stored letter unvalidated, with no
        multiplicity or constraints.

        Parameters
        ----------
        called_by_minimizer : bool, default=False
            When True (per fit iteration), skip re-detection and
            warnings; only the silent coordinate snap runs.
        """
        structure = self._parent
        name_hm = structure.space_group.name_h_m.value
        coord_code = structure.space_group.it_coordinate_system_code.value
        supported = ecr.space_group_wyckoff_table(name_hm, coord_code) is not None
        for atom in self._items:
            if atom._wyckoff_letter_needs_validation:
                self._resolve_pending_wyckoff_letter(atom, name_hm)
            if supported:
                self._detect_and_snap_atom(
                    atom, name_hm, coord_code, called_by_minimizer=called_by_minimizer
                )
            else:
                self._mark_atom_untabulated(
                    atom, (name_hm, coord_code), called_by_minimizer=called_by_minimizer
                )

    @staticmethod
    def _resolve_pending_wyckoff_letter(atom: AtomSite, name_hm: str) -> None:
        """
        Validate a deferred no-context Wyckoff letter; raise if invalid.
        """
        stored = atom.wyckoff_letter.value
        allowed = atom._wyckoff_letter_allowed_values
        if allowed and stored not in allowed:
            msg = (
                f'Invalid Wyckoff letter {stored!r} for space group '
                f'{name_hm!r}; allowed letters: {allowed}'
            )
            raise ValueError(msg)
        atom._wyckoff_letter_needs_validation = False

    def _mark_atom_untabulated(
        self,
        atom: AtomSite,
        key: tuple[str, str | None],
        *,
        called_by_minimizer: bool,
    ) -> None:
        """Handle an atom whose space group is absent from the table."""
        atom._multiplicity.value = None
        self._clear_fract_symmetry_constrained(atom)
        if atom.wyckoff_letter.value and not called_by_minimizer:
            log.warning(
                f'Wyckoff letter of {atom.label.value} is stored but not '
                f'validated because the space group is untabulated'
            )
        atom._wyckoff_coord_baseline = (atom.fract_x.value, atom.fract_y.value, atom.fract_z.value)
        atom._wyckoff_key_baseline = key

    def _detect_and_snap_atom(
        self,
        atom: AtomSite,
        name_hm: str,
        coord_code: str | None,
        *,
        called_by_minimizer: bool,
    ) -> None:
        """
        Detect (if triggered) and snap one atom to its Wyckoff position.
        """
        key = (name_hm, coord_code)
        letter_before = atom.wyckoff_letter.value
        coords = (atom.fract_x.value, atom.fract_y.value, atom.fract_z.value)
        # A ``None`` baseline marks the first population
        # (create/load), not a later edit. Treat coordinates or the
        # space-group key as "changed" only against an existing
        # baseline, so an explicit initial letter is preserved (routed
        # to ``wyckoff_position_info`` below) instead of being
        # overwritten by all-letter detection. The ADR requires a
        # user-supplied letter to persist until a genuine later
        # coordinate or space-group-key edit.
        coords_changed = atom._wyckoff_coord_baseline is not None and any(
            abs(a - b) > ecr._WYCKOFF_DETECTION_TOL
            for a, b in zip(coords, atom._wyckoff_coord_baseline, strict=True)
        )
        key_changed = atom._wyckoff_key_baseline is not None and atom._wyckoff_key_baseline != key
        detect = (not called_by_minimizer) and (not letter_before or coords_changed or key_changed)
        if detect:
            position = ecr.detect_wyckoff_position(name_hm, coord_code, coords)
            if position is not None and letter_before and position.letter != letter_before:
                log.warning(
                    f'change moved the Wyckoff letter of {atom.label.value} '
                    f'from {letter_before} to {position.letter}'
                )
            if position is not None:
                atom._set_wyckoff_letter_detected(position.letter)
        elif letter_before:
            position = ecr.wyckoff_position_info(
                name_hm, coord_code, letter_before, fract_xyz=coords
            )
        else:
            position = None

        if position is None or position.coord_template is None:
            atom._multiplicity.value = None
            self._clear_fract_symmetry_constrained(atom)
            atom._wyckoff_coord_baseline = coords
            atom._wyckoff_key_baseline = key
            return

        atom._multiplicity.value = position.multiplicity
        snapped, flags = ecr.snap_to_wyckoff_template(position.coord_template, coords)
        atom.fract_x.value = snapped[0]
        atom.fract_y.value = snapped[1]
        atom.fract_z.value = snapped[2]
        atom._fract_x._set_symmetry_constrained(value=flags['fract_x'])
        atom._fract_y._set_symmetry_constrained(value=flags['fract_y'])
        atom._fract_z._set_symmetry_constrained(value=flags['fract_z'])
        moved = any(
            abs(s - c) > ecr._WYCKOFF_DETECTION_TOL for s, c in zip(snapped, coords, strict=True)
        )
        if moved and not called_by_minimizer:
            if not detect:
                log.warning(
                    f'coordinates of {atom.label.value} did not fit letter '
                    f'{position.letter} and were adjusted'
                )
            elif letter_before and position.letter == letter_before:
                log.warning(
                    f'coordinates of {atom.label.value} were adjusted to satisfy '
                    f'Wyckoff letter {position.letter}'
                )
        atom._wyckoff_coord_baseline = snapped
        atom._wyckoff_key_baseline = key

    @staticmethod
    def _clear_fract_symmetry_constrained(atom: AtomSite) -> None:
        """
        Clear fractional-coordinate symmetry constraints.
        """
        for axis_param in (atom._fract_x, atom._fract_y, atom._fract_z):
            axis_param._set_symmetry_constrained(value=False)

    def _apply_adp_symmetry_constraints(self) -> None:
        """
        Apply symmetry rules to anisotropic ADP tensor components.

        For each atom with an anisotropic ADP type and a Wyckoff letter,
        enforces the tensor constraints dictated by the site symmetry.
        Tensor components constrained by symmetry are flagged as
        ``symmetry_constrained`` (which also forces ``free = False``),
        and ``adp_iso`` is flagged as fixed for all anisotropic atoms.
        """
        structure = self._parent
        aniso_types = {AdpTypeEnum.BANI.value, AdpTypeEnum.UANI.value, AdpTypeEnum.BETA.value}
        space_group_name = structure.space_group.name_h_m.value
        space_group_coord_code = structure.space_group.it_coordinate_system_code.value
        aniso_collection = structure.atom_site_aniso

        for atom in self._items:
            is_aniso = atom.adp_type.value in aniso_types
            # Isotropic ADP is not refinable for aniso atoms
            atom._adp_iso._set_symmetry_constrained(value=is_aniso)
            if not is_aniso:
                continue
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
                param._set_symmetry_constrained(value=not is_free)

    def _sync_iso_from_aniso(self) -> None:
        """
        Update ``adp_iso`` from the anisotropic tensor for aniso atoms.

        For every atom whose ADP type is anisotropic (Bani / Uani), sets
        ``adp_iso`` to the mean of the three diagonal tensor components
        so that the isotropic value stays consistent with the current
        tensor state.
        """
        aniso_types = {AdpTypeEnum.BANI.value, AdpTypeEnum.UANI.value, AdpTypeEnum.BETA.value}
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
            When True, Wyckoff re-detection and warnings are skipped;
            only the silent coordinate snap runs.
        """
        self._apply_atomic_coordinates_symmetry_constraints(
            called_by_minimizer=called_by_minimizer
        )
        self._apply_adp_symmetry_constraints()
        self._sync_iso_from_aniso()
