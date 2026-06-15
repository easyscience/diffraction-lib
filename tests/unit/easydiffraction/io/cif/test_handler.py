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
