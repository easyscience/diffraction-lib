# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for atom_site_aniso category (default and factory)."""

import math


# ------------------------------------------------------------------
#  Module import
# ------------------------------------------------------------------


def test_module_import():
    import easydiffraction.datablocks.structure.categories.atom_site_aniso as MUT

    expected_module_name = 'easydiffraction.datablocks.structure.categories.atom_site_aniso'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


# ------------------------------------------------------------------
#  Factory
# ------------------------------------------------------------------


class TestAtomSiteAnisoFactory:
    def test_supported_tags(self):
        from easydiffraction.datablocks.structure.categories.atom_site_aniso.factory import (
            AtomSiteAnisoFactory,
        )

        tags = AtomSiteAnisoFactory.supported_tags()
        assert 'default' in tags

    def test_default_tag(self):
        from easydiffraction.datablocks.structure.categories.atom_site_aniso.factory import (
            AtomSiteAnisoFactory,
        )

        assert AtomSiteAnisoFactory.default_tag() == 'default'

    def test_create(self):
        from easydiffraction.datablocks.structure.categories.atom_site_aniso.default import (
            AtomSiteAnisoCollection,
        )
        from easydiffraction.datablocks.structure.categories.atom_site_aniso.factory import (
            AtomSiteAnisoFactory,
        )

        obj = AtomSiteAnisoFactory.create('default')
        assert isinstance(obj, AtomSiteAnisoCollection)


# ------------------------------------------------------------------
#  AtomSiteAniso item
# ------------------------------------------------------------------


class TestAtomSiteAniso:
    def test_instantiation(self):
        from easydiffraction.datablocks.structure.categories.atom_site_aniso.default import (
            AtomSiteAniso,
        )

        entry = AtomSiteAniso()
        assert entry is not None

    def test_identity_category_code(self):
        from easydiffraction.datablocks.structure.categories.atom_site_aniso.default import (
            AtomSiteAniso,
        )

        entry = AtomSiteAniso()
        assert entry._identity.category_code == 'atom_site_aniso'

    def test_defaults(self):
        from easydiffraction.datablocks.structure.categories.atom_site_aniso.default import (
            AtomSiteAniso,
        )

        entry = AtomSiteAniso()
        assert entry.label.value == ''
        assert entry.adp_11.value == 0.0
        assert entry.adp_22.value == 0.0
        assert entry.adp_33.value == 0.0
        assert entry.adp_12.value == 0.0
        assert entry.adp_13.value == 0.0
        assert entry.adp_23.value == 0.0

    def test_label_setter(self):
        from easydiffraction.datablocks.structure.categories.atom_site_aniso.default import (
            AtomSiteAniso,
        )

        entry = AtomSiteAniso()
        entry.label = 'Si'
        assert entry.label.value == 'Si'

    def test_tensor_setters(self):
        from easydiffraction.datablocks.structure.categories.atom_site_aniso.default import (
            AtomSiteAniso,
        )

        entry = AtomSiteAniso()
        entry.adp_11 = 0.01
        entry.adp_22 = 0.02
        entry.adp_33 = 0.03
        entry.adp_12 = 0.04
        entry.adp_13 = 0.05
        entry.adp_23 = 0.06
        assert entry.adp_11.value == 0.01
        assert entry.adp_22.value == 0.02
        assert entry.adp_33.value == 0.03
        assert entry.adp_12.value == 0.04
        assert entry.adp_13.value == 0.05
        assert entry.adp_23.value == 0.06

    def test_dual_cif_names(self):
        from easydiffraction.datablocks.structure.categories.atom_site_aniso.default import (
            AtomSiteAniso,
        )

        entry = AtomSiteAniso()
        # Default order: B first
        assert entry._adp_11._cif_handler.names[0] == '_atom_site_aniso.B_11'
        assert entry._adp_11._cif_handler.names[1] == '_atom_site_aniso.U_11'

    def test_identity_entry_name_follows_label(self):
        from easydiffraction.datablocks.structure.categories.atom_site_aniso.default import (
            AtomSiteAniso,
        )

        entry = AtomSiteAniso()
        entry.label = 'Fe1'
        assert entry._identity.category_entry_name == 'Fe1'


# ------------------------------------------------------------------
#  AtomSiteAnisoCollection
# ------------------------------------------------------------------


class TestAtomSiteAnisoCollection:
    def test_type_info(self):
        from easydiffraction.datablocks.structure.categories.atom_site_aniso.default import (
            AtomSiteAnisoCollection,
        )

        assert AtomSiteAnisoCollection.type_info.tag == 'default'

    def test_instantiation(self):
        from easydiffraction.datablocks.structure.categories.atom_site_aniso.default import (
            AtomSiteAnisoCollection,
        )

        coll = AtomSiteAnisoCollection()
        assert coll is not None
        assert len(coll) == 0

    def test_skip_cif_serialization_no_parent(self):
        from easydiffraction.datablocks.structure.categories.atom_site_aniso.default import (
            AtomSiteAnisoCollection,
        )

        coll = AtomSiteAnisoCollection()
        # No parent → should skip
        assert coll._skip_cif_serialization() is True

    def test_skip_cif_serialization_isotropic(self):
        from easydiffraction.datablocks.structure.item.base import Structure

        structure = Structure(name='test')
        structure.atom_sites.create(label='Si', type_symbol='Si', adp_type='Biso', adp_iso=0.5)
        structure._sync_atom_site_aniso()
        assert structure.atom_site_aniso._skip_cif_serialization() is True

    def test_skip_cif_serialization_anisotropic(self):
        from easydiffraction.datablocks.structure.item.base import Structure

        structure = Structure(name='test')
        structure.atom_sites.create(label='Si', type_symbol='Si', adp_type='Biso', adp_iso=0.5)
        structure._sync_atom_site_aniso()
        structure.atom_sites['Si'].adp_type = 'Bani'
        assert structure.atom_site_aniso._skip_cif_serialization() is False


# ------------------------------------------------------------------
#  Structure ↔ aniso sync
# ------------------------------------------------------------------


class TestStructureAnisoSync:
    def test_sync_adds_missing_entries(self):
        from easydiffraction.datablocks.structure.item.base import Structure

        structure = Structure(name='test')
        structure.atom_sites.create(label='Si', type_symbol='Si')
        structure._sync_atom_site_aniso()
        assert 'Si' in structure.atom_site_aniso
        assert structure.atom_site_aniso['Si'].label.value == 'Si'

    def test_sync_removes_stale_entries(self):
        from easydiffraction.datablocks.structure.item.base import Structure

        structure = Structure(name='test')
        structure.atom_sites.create(label='Si', type_symbol='Si')
        structure.atom_sites.create(label='O', type_symbol='O')
        structure._sync_atom_site_aniso()
        assert len(structure.atom_site_aniso) == 2

        structure.atom_sites.remove('O')
        structure._sync_atom_site_aniso()
        assert len(structure.atom_site_aniso) == 1
        assert 'Si' in structure.atom_site_aniso

    def test_sync_multiple_atoms(self):
        from easydiffraction.datablocks.structure.item.base import Structure

        structure = Structure(name='test')
        structure.atom_sites.create(label='La', type_symbol='La')
        structure.atom_sites.create(label='Ba', type_symbol='Ba')
        structure.atom_sites.create(label='Co', type_symbol='Co')
        structure._sync_atom_site_aniso()
        assert len(structure.atom_site_aniso) == 3
        for lbl in ('La', 'Ba', 'Co'):
            assert lbl in structure.atom_site_aniso


# ------------------------------------------------------------------
#  ADP type conversion (iso ↔ ani)
# ------------------------------------------------------------------


class TestAdpTypeConversion:
    def _make_structure_with_atom(self, adp_type='Biso', adp_iso=0.5):
        from easydiffraction.datablocks.structure.item.base import Structure

        structure = Structure(name='test')
        structure.atom_sites.create(
            label='Si',
            type_symbol='Si',
            adp_type=adp_type,
            adp_iso=adp_iso,
        )
        structure._sync_atom_site_aniso()
        return structure

    def test_biso_to_bani_seeds_diagonal(self):
        structure = self._make_structure_with_atom(adp_type='Biso', adp_iso=0.5)
        structure.atom_sites['Si'].adp_type = 'Bani'
        aniso = structure.atom_site_aniso['Si']
        assert aniso.adp_11.value == 0.5
        assert aniso.adp_22.value == 0.5
        assert aniso.adp_33.value == 0.5
        assert aniso.adp_12.value == 0.0
        assert aniso.adp_13.value == 0.0
        assert aniso.adp_23.value == 0.0

    def test_biso_to_uani_seeds_converted_diagonal(self):
        factor = 8.0 * math.pi**2
        structure = self._make_structure_with_atom(adp_type='Biso', adp_iso=0.5)
        structure.atom_sites['Si'].adp_type = 'Uani'
        aniso = structure.atom_site_aniso['Si']
        expected_u = 0.5 / factor
        assert math.isclose(aniso.adp_11.value, expected_u, rel_tol=1e-10)
        assert math.isclose(aniso.adp_22.value, expected_u, rel_tol=1e-10)
        assert math.isclose(aniso.adp_33.value, expected_u, rel_tol=1e-10)

    def test_bani_to_biso_collapses_diagonal(self):
        structure = self._make_structure_with_atom(adp_type='Biso', adp_iso=0.5)
        structure.atom_sites['Si'].adp_type = 'Bani'
        # Modify diagonal
        aniso = structure.atom_site_aniso['Si']
        aniso.adp_11 = 0.3
        aniso.adp_22 = 0.6
        aniso.adp_33 = 0.9
        structure.atom_sites['Si'].adp_type = 'Biso'
        expected = (0.3 + 0.6 + 0.9) / 3.0
        assert math.isclose(structure.atom_sites['Si'].adp_iso.value, expected, rel_tol=1e-10)

    def test_uiso_to_uani_seeds_diagonal(self):
        structure = self._make_structure_with_atom(adp_type='Uiso', adp_iso=0.05)
        structure.atom_sites['Si'].adp_type = 'Uani'
        aniso = structure.atom_site_aniso['Si']
        assert math.isclose(aniso.adp_11.value, 0.05, rel_tol=1e-10)

    def test_bani_to_uani_converts_values(self):
        factor = 8.0 * math.pi**2
        structure = self._make_structure_with_atom(adp_type='Biso', adp_iso=0.5)
        structure.atom_sites['Si'].adp_type = 'Bani'
        # Now ani values are B=0.5
        structure.atom_sites['Si'].adp_type = 'Uani'
        aniso = structure.atom_site_aniso['Si']
        expected_u = 0.5 / factor
        assert math.isclose(aniso.adp_11.value, expected_u, rel_tol=1e-10)

    def test_round_trip_biso_uani_biso(self):
        structure = self._make_structure_with_atom(adp_type='Biso', adp_iso=0.5)
        structure.atom_sites['Si'].adp_type = 'Uani'
        structure.atom_sites['Si'].adp_type = 'Biso'
        assert math.isclose(structure.atom_sites['Si'].adp_iso.value, 0.5, rel_tol=1e-10)


# ------------------------------------------------------------------
#  CIF name reordering
# ------------------------------------------------------------------


class TestCifNameReordering:
    def test_biso_cif_names_default_order(self):
        from easydiffraction.datablocks.structure.categories.atom_sites.default import AtomSite

        site = AtomSite()
        assert site._adp_iso._cif_handler.names[0] == '_atom_site.B_iso_or_equiv'

    def test_uiso_reorders_iso_cif_names(self):
        from easydiffraction.datablocks.structure.item.base import Structure

        structure = Structure(name='test')
        structure.atom_sites.create(label='Si', type_symbol='Si', adp_type='Biso', adp_iso=0.5)
        structure._sync_atom_site_aniso()
        structure.atom_sites['Si'].adp_type = 'Uiso'
        assert (
            structure.atom_sites['Si']._adp_iso._cif_handler.names[0]
            == '_atom_site.U_iso_or_equiv'
        )

    def test_bani_reorders_aniso_cif_names(self):
        from easydiffraction.datablocks.structure.item.base import Structure

        structure = Structure(name='test')
        structure.atom_sites.create(label='Si', type_symbol='Si', adp_type='Biso', adp_iso=0.5)
        structure._sync_atom_site_aniso()
        structure.atom_sites['Si'].adp_type = 'Bani'
        aniso = structure.atom_site_aniso['Si']
        assert aniso._adp_11._cif_handler.names[0] == '_atom_site_aniso.B_11'

    def test_uani_reorders_aniso_cif_names(self):
        from easydiffraction.datablocks.structure.item.base import Structure

        structure = Structure(name='test')
        structure.atom_sites.create(label='Si', type_symbol='Si', adp_type='Biso', adp_iso=0.5)
        structure._sync_atom_site_aniso()
        structure.atom_sites['Si'].adp_type = 'Uani'
        aniso = structure.atom_site_aniso['Si']
        assert aniso._adp_11._cif_handler.names[0] == '_atom_site_aniso.U_11'
