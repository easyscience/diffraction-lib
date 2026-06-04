# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for atom_sites category (default and factory)."""


def test_module_import():
    import easydiffraction.datablocks.structure.categories.atom_sites as MUT

    expected_module_name = 'easydiffraction.datablocks.structure.categories.atom_sites'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


class TestAtomSitesFactory:
    def test_supported_tags(self):
        from easydiffraction.datablocks.structure.categories.atom_sites.factory import (
            AtomSitesFactory,
        )

        tags = AtomSitesFactory.supported_tags()
        assert 'default' in tags

    def test_default_tag(self):
        from easydiffraction.datablocks.structure.categories.atom_sites.factory import (
            AtomSitesFactory,
        )

        assert AtomSitesFactory.default_tag() == 'default'

    def test_create(self):
        from easydiffraction.datablocks.structure.categories.atom_sites.default import AtomSites
        from easydiffraction.datablocks.structure.categories.atom_sites.factory import (
            AtomSitesFactory,
        )

        obj = AtomSitesFactory.create('default')
        assert isinstance(obj, AtomSites)


class TestAtomSite:
    def test_instantiation(self):
        from easydiffraction.datablocks.structure.categories.atom_sites.default import AtomSite

        site = AtomSite()
        assert site is not None

    def test_identity_category_code(self):
        from easydiffraction.datablocks.structure.categories.atom_sites.default import AtomSite

        site = AtomSite()
        assert site._identity.category_code == 'atom_site'

    def test_defaults(self):
        from easydiffraction.datablocks.structure.categories.atom_sites.default import AtomSite

        site = AtomSite()
        assert site.label.value == 'Si'
        assert site.type_symbol.value == 'Tb'
        assert site.fract_x.value == 0.0
        assert site.fract_y.value == 0.0
        assert site.fract_z.value == 0.0
        assert site.occupancy.value == 1.0
        assert site.adp_iso.value == 0.0
        assert site.adp_type.value == 'Biso'

    def test_label_setter(self):
        from easydiffraction.datablocks.structure.categories.atom_sites.default import AtomSite

        site = AtomSite()
        site.label = 'Fe1'
        assert site.label.value == 'Fe1'

    def test_type_symbol_setter(self):
        from easydiffraction.datablocks.structure.categories.atom_sites.default import AtomSite

        site = AtomSite()
        site.type_symbol = 'Fe'
        assert site.type_symbol.value == 'Fe'

    def test_coordinate_setters(self):
        from easydiffraction.datablocks.structure.categories.atom_sites.default import AtomSite

        site = AtomSite()
        site.fract_x = 0.25
        site.fract_y = 0.5
        site.fract_z = 0.75
        assert site.fract_x.value == 0.25
        assert site.fract_y.value == 0.5
        assert site.fract_z.value == 0.75

    def test_occupancy_setter(self):
        from easydiffraction.datablocks.structure.categories.atom_sites.default import AtomSite

        site = AtomSite()
        site.occupancy = 0.5
        assert site.occupancy.value == 0.5

    def test_adp_iso_setter(self):
        from easydiffraction.datablocks.structure.categories.atom_sites.default import AtomSite

        site = AtomSite()
        site.adp_iso = 1.5
        assert site.adp_iso.value == 1.5

    def test_type_symbol_allowed_values(self):
        from easydiffraction.datablocks.structure.categories.atom_sites.default import AtomSite

        site = AtomSite()
        allowed = site._type_symbol_allowed_values
        assert isinstance(allowed, list)
        assert len(allowed) > 0
        assert 'Fe' in allowed

    def test_wyckoff_letter_allowed_values(self):
        from easydiffraction.datablocks.structure.item.base import Structure

        # Allowed letters are derived from the parent structure's space
        # group, so the atom must live inside a structure with a
        # tabulated space group; a parentless AtomSite has no allowed
        # letters.
        structure = Structure(name='s')
        structure.space_group.name_h_m = 'P m -3 m'
        structure.atom_sites.create(label='X', type_symbol='O', adp_iso=0.5)
        allowed = structure.atom_sites['X']._wyckoff_letter_allowed_values
        assert 'a' in allowed

    def test_uses_iucr_casing_with_legacy_aliases(self):
        from easydiffraction.datablocks.structure.categories.atom_sites.default import AtomSite

        site = AtomSite()

        assert site.adp_type._cif_handler.names == [
            '_atom_site.ADP_type',
            '_atom_site.adp_type',
        ]
        assert site.wyckoff_letter._cif_handler.names == [
            '_atom_site.Wyckoff_symbol',
            '_atom_site.Wyckoff_letter',
            '_atom_site.wyckoff_letter',
        ]


class TestAtomSites:
    def test_type_info(self):
        from easydiffraction.datablocks.structure.categories.atom_sites.default import AtomSites

        assert AtomSites.type_info.tag == 'default'

    def test_instantiation(self):
        from easydiffraction.datablocks.structure.categories.atom_sites.default import AtomSites

        sites = AtomSites()
        assert sites is not None


# ------------------------------------------------------------------
#  _sync_iso_from_aniso
# ------------------------------------------------------------------


class TestSyncIsoFromAniso:
    def _make_structure(self, adp_type='Biso', adp_iso=0.5):
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

    def test_sync_updates_iso_for_bani_atom(self):
        import math

        structure = self._make_structure(adp_type='Biso', adp_iso=0.5)
        structure.atom_sites['Si'].adp_type = 'Bani'
        aniso = structure.atom_site_aniso['Si']
        aniso.adp_11 = 0.3
        aniso.adp_22 = 0.6
        aniso.adp_33 = 0.9
        structure.atom_sites._sync_iso_from_aniso()
        expected = (0.3 + 0.6 + 0.9) / 3.0
        assert math.isclose(structure.atom_sites['Si'].adp_iso.value, expected, rel_tol=1e-10)

    def test_sync_updates_iso_for_uani_atom(self):
        import math

        structure = self._make_structure(adp_type='Uiso', adp_iso=0.05)
        structure.atom_sites['Si'].adp_type = 'Uani'
        aniso = structure.atom_site_aniso['Si']
        aniso.adp_11 = 0.01
        aniso.adp_22 = 0.02
        aniso.adp_33 = 0.03
        structure.atom_sites._sync_iso_from_aniso()
        expected = (0.01 + 0.02 + 0.03) / 3.0
        assert math.isclose(structure.atom_sites['Si'].adp_iso.value, expected, rel_tol=1e-10)

    def test_sync_skips_iso_atoms(self):
        structure = self._make_structure(adp_type='Biso', adp_iso=0.5)
        structure.atom_sites._sync_iso_from_aniso()
        assert structure.atom_sites['Si'].adp_iso.value == 0.5

    def test_update_calls_sync(self):
        """Verify _update() triggers _sync_iso_from_aniso().

        In P m -3 m Wyckoff a, symmetry forces U11=U22=U33.
        We set all diags to 0.3 (satisfying the constraint), then
        manually overwrite adp_iso to a wrong value.  After _update(),
        adp_iso must be resynced from the (still-equal) diags.
        """
        structure = self._make_structure(adp_type='Biso', adp_iso=0.5)
        structure.space_group.name_h_m = 'P m -3 m'
        structure.atom_sites['Si'].adp_type = 'Bani'
        aniso = structure.atom_site_aniso['Si']
        aniso.adp_11 = 0.3
        aniso.adp_22 = 0.3
        aniso.adp_33 = 0.3
        # Force adp_iso to a wrong value so we can confirm _update resyncs it
        structure.atom_sites['Si'].adp_iso = 0.99
        structure.atom_sites._update()
        assert structure.atom_sites['Si'].adp_iso.value == 0.3


# ------------------------------------------------------------------
#  adp_iso_as_b property
# ------------------------------------------------------------------


class TestAdpIsoAsB:
    def _make_structure(self, adp_type='Biso', adp_iso=0.5):
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

    def test_biso_as_b_returns_same_value(self):
        structure = self._make_structure(adp_type='Biso', adp_iso=0.5)
        assert structure.atom_sites['Si'].adp_iso_as_b == 0.5

    def test_uiso_as_b_converts(self):
        import math

        u_val = 0.005
        structure = self._make_structure(adp_type='Uiso', adp_iso=u_val)
        expected_b = u_val * 8.0 * math.pi**2
        assert math.isclose(structure.atom_sites['Si'].adp_iso_as_b, expected_b, rel_tol=1e-10)

    def test_bani_as_b_returns_iso_value(self):
        structure = self._make_structure(adp_type='Biso', adp_iso=0.5)
        structure.atom_sites['Si'].adp_type = 'Bani'
        assert structure.atom_sites['Si'].adp_iso_as_b == 0.5

    def test_uani_as_b_converts(self):
        import math

        u_val = 0.005
        structure = self._make_structure(adp_type='Uiso', adp_iso=u_val)
        structure.atom_sites['Si'].adp_type = 'Uani'
        expected_b = u_val * 8.0 * math.pi**2
        assert math.isclose(structure.atom_sites['Si'].adp_iso_as_b, expected_b, rel_tol=1e-10)


# ------------------------------------------------------------------
#  Wyckoff letter detection / multiplicity
# ------------------------------------------------------------------


class TestAtomSiteWyckoffDetection:
    @staticmethod
    def _structure(name_hm='P m -3 m'):
        from easydiffraction.datablocks.structure.item.base import Structure

        structure = Structure(name='s')
        structure.space_group.name_h_m = name_hm
        return structure

    def test_fill_if_empty_on_update(self):
        structure = self._structure()
        structure.atom_sites.create(label='A', type_symbol='O', adp_iso=0.5)
        structure._update_categories()
        atom = structure.atom_sites['A']
        assert atom.wyckoff_letter.value == 'a'
        assert atom.multiplicity.value == 1

    def test_redetect_via_property_setter(self):
        structure = self._structure()
        structure.atom_sites.create(label='A', type_symbol='O', adp_iso=0.5)
        structure._update_categories()
        structure.atom_sites['A'].fract_x = 0.3
        structure._update_categories()
        assert structure.atom_sites['A'].wyckoff_letter.value == 'e'

    def test_redetect_via_descriptor_value(self):
        structure = self._structure()
        structure.atom_sites.create(label='A', type_symbol='O', adp_iso=0.5)
        structure._update_categories()
        structure.atom_sites['A'].fract_x.value = 0.3
        structure._update_categories()
        assert structure.atom_sites['A'].wyckoff_letter.value == 'e'

    def test_explicit_letter_preserved_on_first_update(self):
        # (0.5,0,0) lies on both 'e' = (x,0,0) and the more special
        # 'd' = (1/2,0,0); an explicit 'e' must be kept, not detected 'd'.
        structure = self._structure()
        structure.atom_sites.create(
            label='E',
            type_symbol='O',
            fract_x=0.5,
            fract_y=0.0,
            fract_z=0.0,
            adp_iso=0.5,
            wyckoff_letter='e',
        )
        structure._update_categories()
        atom = structure.atom_sites['E']
        assert atom.wyckoff_letter.value == 'e'
        assert atom.multiplicity.value == 6

    def test_invalid_explicit_letter_raises_on_update(self):
        import pytest

        structure = self._structure()
        structure.atom_sites.create(label='Z', type_symbol='O', adp_iso=0.5, wyckoff_letter='z')
        with pytest.raises(ValueError, match='Invalid Wyckoff letter'):
            structure._update_categories()

    def test_same_letter_edit_snaps_off_orbit_coordinate(self):
        # 'e' = (x,0,0): a small off-orbit nudge in fract_y (within the
        # detection tolerance) keeps the letter 'e' and snaps fract_y back
        # to 0 while fract_x stays free.
        structure = self._structure()
        structure.atom_sites.create(
            label='E',
            type_symbol='O',
            fract_x=0.3,
            fract_y=0.0,
            fract_z=0.0,
            adp_iso=0.5,
        )
        structure._update_categories()
        assert structure.atom_sites['E'].wyckoff_letter.value == 'e'
        structure.atom_sites['E'].fract_x.value = 0.4
        structure.atom_sites['E'].fract_y.value = 0.0005
        structure._update_categories()
        atom = structure.atom_sites['E']
        assert atom.wyckoff_letter.value == 'e'
        assert abs(atom.fract_x.value - 0.4) < 1e-6
        assert abs(atom.fract_y.value) < 1e-6

    def test_space_group_change_redetects(self):
        structure = self._structure()
        structure.atom_sites.create(label='A', type_symbol='O', adp_iso=0.5)
        structure._update_categories()
        assert structure.atom_sites['A'].multiplicity.value == 1  # Pm-3m 'a'
        structure.space_group.name_h_m = 'F m -3 m'
        structure._update_categories()
        atom = structure.atom_sites['A']
        assert atom.wyckoff_letter.value == 'a'
        assert atom.multiplicity.value == 4  # Fm-3m 'a'

    def test_minimizer_path_keeps_letter_fixed(self):
        structure = self._structure()
        structure.atom_sites.create(
            label='E',
            type_symbol='O',
            fract_x=0.3,
            fract_y=0.0,
            fract_z=0.0,
            adp_iso=0.5,
        )
        structure._update_categories()
        # A minimizer step varies the free axis; the letter stays fixed
        # (no re-detection) and the free coordinate is preserved.
        structure.atom_sites['E'].fract_x.value = 0.4
        structure._update_categories(called_by_minimizer=True)
        assert structure.atom_sites['E'].wyckoff_letter.value == 'e'
        assert abs(structure.atom_sites['E'].fract_x.value - 0.4) < 1e-6

    def test_untabulated_group_preserves_letter_without_multiplicity(self, monkeypatch):
        from easydiffraction.crystallography import crystallography as ecr

        monkeypatch.setattr(ecr, 'space_group_wyckoff_table', lambda *a, **k: None)
        structure = self._structure()
        structure.atom_sites.create(label='X', type_symbol='O', adp_iso=0.5, wyckoff_letter='a')
        structure._update_categories()
        atom = structure.atom_sites['X']
        assert atom.wyckoff_letter.value == 'a'
        assert atom.multiplicity.value is None

    def test_no_record_contract_clears_multiplicity(self, monkeypatch):
        from easydiffraction.crystallography import crystallography as ecr

        monkeypatch.setattr(ecr, 'space_group_wyckoff_table', lambda *a, **k: None)
        structure = self._structure()
        structure.atom_sites.create(label='X', type_symbol='O', adp_iso=0.5)
        structure._update_categories()
        assert structure.atom_sites['X'].multiplicity.value is None
        assert '_atom_site.site_symmetry_multiplicity' in structure.as_cif

    def test_cif_round_trip_redrives_letter(self):
        from easydiffraction.datablocks.structure.item.factory import StructureFactory

        structure = self._structure()
        structure.atom_sites.create(label='A', type_symbol='O', adp_iso=0.5)
        structure._update_categories()
        reloaded = StructureFactory.from_cif_str(structure.as_cif)
        reloaded._update_categories()
        assert reloaded.atom_sites['A'].wyckoff_letter.value == 'a'
        assert reloaded.atom_sites['A'].multiplicity.value == 1
