# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Anisotropic ADP category.

Defines :class:`AtomSiteAniso` items and
:class:`AtomSiteAnisoCollection` used alongside :class:`AtomSites` to
hold anisotropic displacement parameters.
"""

from __future__ import annotations

from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.display_handler import DisplayHandler
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.variable import Parameter
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.datablocks.structure.categories.atom_site_aniso.factory import (
    AtomSiteAnisoFactory,
)
from easydiffraction.io.cif.handler import CifHandler


class _AnisoAdpParameter(Parameter):
    """
    Aniso ADP component whose display units track ``adp_type``.

    For ``adp_type == 'beta'`` the tensor components are dimensionless,
    so display units are suppressed at resolve time. The stored unit
    metadata is left unchanged (a single declared unit per the value
    model); only the resolved display string is type-aware. All other
    behaviour is inherited from :class:`Parameter`.
    """

    def resolve_display_units(self, context: str) -> str:
        """
        Return display units, suppressed for a beta-tensor owner.

        Parameters
        ----------
        context : str
            One of ``'latex'``, ``'html'``, or ``'gui'``.

        Returns
        -------
        str
            The inherited display units, or an empty string when the
            owning atom uses the dimensionless ``beta`` ADP type.
        """
        from easydiffraction.datablocks.structure.categories.atom_sites.enums import (  # noqa: PLC0415
            AdpTypeEnum,
        )

        units = super().resolve_display_units(context)
        if self._owning_adp_type() == AdpTypeEnum.BETA.value:
            return ''
        return units

    def _owning_adp_type(self) -> str | None:
        """Return the owning atom's ``adp_type`` value, or ``None``."""
        # Tolerant walk: display can resolve units before the
        # param → aniso item → collection → structure → atom_site chain
        # is fully wired (e.g. during construction or for a detached
        # parameter). Any broken link falls back to the declared unit
        # rather than raising in a display path.
        aniso_item = getattr(self, '_parent', None)
        atom_id = getattr(getattr(aniso_item, '_id', None), 'value', None)
        collection = getattr(aniso_item, '_parent', None)
        structure = getattr(collection, '_parent', None)
        atom_sites = getattr(structure, 'atom_sites', None)
        if atom_sites is None or atom_id is None:
            return None
        try:
            atom = atom_sites[atom_id]
        except (KeyError, TypeError):
            return None
        return getattr(getattr(atom, 'adp_type', None), 'value', None)


class AtomSiteAniso(CategoryItem):
    """
    Single atom site anisotropic ADP entry.

    Each entry mirrors an :class:`AtomSite` by id and holds six
    tensor components whose physical meaning (B or U) is determined by
    ``atom_site.adp_type``.
    """

    _category_code = 'atom_site_aniso'
    _category_entry_name = 'id'

    def __init__(self) -> None:
        """Initialise with default zero-valued tensor components."""
        super().__init__()

        self._id = StringDescriptor(
            name='id',
            description='Atom-site id matching the parent atom_site entry.',
            value_spec=AttributeSpec(default=''),
            cif_handler=CifHandler(
                names=['_atom_site_aniso.id'],
                import_names=['_atom_site_aniso.label'],
                iucr_name='_atom_site_aniso.label',
            ),
        )

        self._adp_11 = _AnisoAdpParameter(
            name='adp_11',
            description='Anisotropic ADP tensor component (1,1).',
            units='angstrom_squared',
            display_handler=DisplayHandler(
                display_name='U11',
                display_units='Å²',
                latex_name=r'$U_{11}$',
                latex_units=r'\AA$^2$',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0.0, le=10.0),
            ),
            cif_handler=CifHandler(
                project_name='_atom_site_aniso.adp_11',
                names=['_atom_site_aniso.adp_11'],
                import_names=[
                    '_atom_site_aniso.B_11',
                    '_atom_site_aniso.U_11',
                    '_atom_site_aniso.beta_11',
                ],
                iucr_name='_atom_site_aniso.B_11',
            ),
        )
        self._adp_22 = _AnisoAdpParameter(
            name='adp_22',
            description='Anisotropic ADP tensor component (2,2).',
            units='angstrom_squared',
            display_handler=DisplayHandler(
                display_name='U22',
                display_units='Å²',
                latex_name=r'$U_{22}$',
                latex_units=r'\AA$^2$',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0.0, le=10.0),
            ),
            cif_handler=CifHandler(
                project_name='_atom_site_aniso.adp_22',
                names=['_atom_site_aniso.adp_22'],
                import_names=[
                    '_atom_site_aniso.B_22',
                    '_atom_site_aniso.U_22',
                    '_atom_site_aniso.beta_22',
                ],
                iucr_name='_atom_site_aniso.B_22',
            ),
        )
        self._adp_33 = _AnisoAdpParameter(
            name='adp_33',
            description='Anisotropic ADP tensor component (3,3).',
            units='angstrom_squared',
            display_handler=DisplayHandler(
                display_name='U33',
                display_units='Å²',
                latex_name=r'$U_{33}$',
                latex_units=r'\AA$^2$',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0.0, le=10.0),
            ),
            cif_handler=CifHandler(
                project_name='_atom_site_aniso.adp_33',
                names=['_atom_site_aniso.adp_33'],
                import_names=[
                    '_atom_site_aniso.B_33',
                    '_atom_site_aniso.U_33',
                    '_atom_site_aniso.beta_33',
                ],
                iucr_name='_atom_site_aniso.B_33',
            ),
        )
        self._adp_12 = _AnisoAdpParameter(
            name='adp_12',
            description='Anisotropic ADP tensor component (1,2).',
            units='angstrom_squared',
            display_handler=DisplayHandler(
                display_name='U12',
                display_units='Å²',
                latex_name=r'$U_{12}$',
                latex_units=r'\AA$^2$',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                project_name='_atom_site_aniso.adp_12',
                names=['_atom_site_aniso.adp_12'],
                import_names=[
                    '_atom_site_aniso.B_12',
                    '_atom_site_aniso.U_12',
                    '_atom_site_aniso.beta_12',
                ],
                iucr_name='_atom_site_aniso.B_12',
            ),
        )
        self._adp_13 = _AnisoAdpParameter(
            name='adp_13',
            description='Anisotropic ADP tensor component (1,3).',
            units='angstrom_squared',
            display_handler=DisplayHandler(
                display_name='U13',
                display_units='Å²',
                latex_name=r'$U_{13}$',
                latex_units=r'\AA$^2$',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                project_name='_atom_site_aniso.adp_13',
                names=['_atom_site_aniso.adp_13'],
                import_names=[
                    '_atom_site_aniso.B_13',
                    '_atom_site_aniso.U_13',
                    '_atom_site_aniso.beta_13',
                ],
                iucr_name='_atom_site_aniso.B_13',
            ),
        )
        self._adp_23 = _AnisoAdpParameter(
            name='adp_23',
            description='Anisotropic ADP tensor component (2,3).',
            units='angstrom_squared',
            display_handler=DisplayHandler(
                display_name='U23',
                display_units='Å²',
                latex_name=r'$U_{23}$',
                latex_units=r'\AA$^2$',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                project_name='_atom_site_aniso.adp_23',
                names=['_atom_site_aniso.adp_23'],
                import_names=[
                    '_atom_site_aniso.B_23',
                    '_atom_site_aniso.U_23',
                    '_atom_site_aniso.beta_23',
                ],
                iucr_name='_atom_site_aniso.B_23',
            ),
        )

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def id(self) -> StringDescriptor:
        """ID matching the parent atom_site entry."""
        return self._id

    @id.setter
    def id(self, value: str) -> None:
        self._id.value = value

    @property
    def adp_11(self) -> Parameter:
        """Anisotropic ADP tensor component (1,1) in Å²."""
        return self._adp_11

    @adp_11.setter
    def adp_11(self, value: float) -> None:
        self._adp_11.value = value

    @property
    def adp_22(self) -> Parameter:
        """Anisotropic ADP tensor component (2,2) in Å²."""
        return self._adp_22

    @adp_22.setter
    def adp_22(self, value: float) -> None:
        self._adp_22.value = value

    @property
    def adp_33(self) -> Parameter:
        """Anisotropic ADP tensor component (3,3) in Å²."""
        return self._adp_33

    @adp_33.setter
    def adp_33(self, value: float) -> None:
        self._adp_33.value = value

    @property
    def adp_12(self) -> Parameter:
        """Anisotropic ADP tensor component (1,2) in Å²."""
        return self._adp_12

    @adp_12.setter
    def adp_12(self, value: float) -> None:
        self._adp_12.value = value

    @property
    def adp_13(self) -> Parameter:
        """Anisotropic ADP tensor component (1,3) in Å²."""
        return self._adp_13

    @adp_13.setter
    def adp_13(self, value: float) -> None:
        self._adp_13.value = value

    @property
    def adp_23(self) -> Parameter:
        """Anisotropic ADP tensor component (2,3) in Å²."""
        return self._adp_23

    @adp_23.setter
    def adp_23(self, value: float) -> None:
        self._adp_23.value = value


@AtomSiteAnisoFactory.register
class AtomSiteAnisoCollection(CategoryCollection):
    """Collection of :class:`AtomSiteAniso` instances."""

    type_info = TypeInfo(
        tag='default',
        description='Anisotropic ADP collection',
    )

    def __init__(self) -> None:
        """Initialise an empty aniso-ADP collection."""
        super().__init__(item_type=AtomSiteAniso)

    def _skip_cif_serialization(self) -> bool:
        """
        Return ``True`` when no atoms use an anisotropic ADP type.

        Returns
        -------
        bool
            ``True`` if CIF output should be suppressed.
        """
        structure = getattr(self, '_parent', None)
        if structure is None:
            return True
        atom_sites = getattr(structure, '_atom_sites', None)
        if atom_sites is None:
            return True
        from easydiffraction.datablocks.structure.categories.atom_sites.enums import (  # noqa: PLC0415
            AdpTypeEnum,
        )

        aniso_types = {AdpTypeEnum.BANI.value, AdpTypeEnum.UANI.value, AdpTypeEnum.BETA.value}
        return not any(atom.adp_type.value in aniso_types for atom in atom_sites)
