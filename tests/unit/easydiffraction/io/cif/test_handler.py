# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause


def test_tags_names_and_uid():
    import easydiffraction.io.cif.handler as H

    names = ['_cell.length_a', '_cell.length_b']
    h = H.TagSpec(edi_names=names)
    assert h.edi_names == names
    assert h.uid is None

    class Owner:
        unique_name = 'db.cat.entry.param'

    h.attach(Owner())
    assert h.uid == 'db.cat.entry.param'


def test_tags_cif_name_falls_back_to_first_name():
    from easydiffraction.io.cif.handler import TagSpec

    handler = TagSpec(edi_names=['_calculator.type'])

    assert handler.cif_name == '_calculator.type'


def test_tags_cif_name_uses_explicit_value():
    from easydiffraction.io.cif.handler import TagSpec

    handler = TagSpec(
        edi_names=['_calculator.type'], cif_names=['_easydiffraction_calculator.type']
    )

    assert handler.cif_name == '_easydiffraction_calculator.type'


def test_explicit_edi_name_overrides_first_and_leads_read_order():
    from easydiffraction.io.cif.handler import TagSpec

    handler = TagSpec(edi_names=['_a.x', '_a.y'], edi_name='_a.z')

    assert handler.edi_name == '_a.z'
    assert handler.edi_read_names == ['_a.z', '_a.x', '_a.y']


def test_edi_read_names_remove_duplicates():
    from easydiffraction.io.cif.handler import TagSpec

    handler = TagSpec(edi_names=['_a.x', '_a.x'])

    assert handler.edi_read_names == ['_a.x']


def test_cif_read_names_dedup_and_canonical_first():
    from easydiffraction.io.cif.handler import TagSpec

    handler = TagSpec(edi_names=['_a.x'], cif_names=['_b.y', '_b.z', '_b.y'])

    assert handler.cif_name == '_b.y'
    assert handler.cif_read_names == ['_b.y', '_b.z']


def test_cif_names_default_to_edi_names():
    from easydiffraction.io.cif.handler import TagSpec

    handler = TagSpec(edi_names=['_a.x'])

    assert handler.cif_names == ['_a.x']
    assert handler.cif_name == '_a.x'


def test_read_names_union_orders_edi_before_cif_and_dedupes():
    from easydiffraction.io.cif.handler import TagSpec

    handler = TagSpec(edi_names=['_a.x'], cif_names=['_a.x', '_b.y'])

    # Edi name first, then CIF-only aliases, with duplicates removed.
    assert handler.read_names == ['_a.x', '_b.y']
