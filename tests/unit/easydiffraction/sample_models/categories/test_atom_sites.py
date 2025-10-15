from easydiffraction.sample_models.categories.atom_sites import AtomSite, AtomSites


def test_atom_site_defaults_and_setters():
    a = AtomSite(label="Si1", type_symbol="Si")
    a.fract_x = 0.1
    a.fract_y = 0.2
    a.fract_z = 0.3
    a.occupancy = 0.9
    a.b_iso = 1.5
    a.adp_type = "Biso"
    assert a.label.value == "Si1"
    assert a.type_symbol.value == "Si"
    assert (a.fract_x.value, a.fract_y.value, a.fract_z.value) == (0.1, 0.2, 0.3)
    assert a.occupancy.value == 0.9
    assert a.b_iso.value == 1.5
    assert a.adp_type.value == "Biso"


def test_atom_sites_collection_adds_by_label():
    sites = AtomSites()
    a = AtomSite(label="O1", type_symbol="O")
    sites.add(a)
    assert "O1" in sites.names
    assert sites["O1"].type_symbol.value == "O"
