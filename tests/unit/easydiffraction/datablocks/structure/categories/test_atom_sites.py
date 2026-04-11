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


class TestAtomSites:
    def test_type_info(self):
        from easydiffraction.datablocks.structure.categories.atom_sites.default import AtomSites

        assert AtomSites.type_info.tag == 'default'

    def test_instantiation(self):
        from easydiffraction.datablocks.structure.categories.atom_sites.default import AtomSites

        sites = AtomSites()
        assert sites is not None
