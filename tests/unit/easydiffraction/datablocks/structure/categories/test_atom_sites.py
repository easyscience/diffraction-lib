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
        from easydiffraction.datablocks.structure.categories.atom_sites.default import AtomSite

        site = AtomSite()
        allowed = site._wyckoff_letter_allowed_values
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
