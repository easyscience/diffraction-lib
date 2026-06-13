# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause


def test_linked_structures_add_and_cif_headers():
    from easydiffraction.datablocks.experiment.categories.linked_structures import LinkedStructure
    from easydiffraction.datablocks.experiment.categories.linked_structures import LinkedStructures

    lp = LinkedStructure()
    lp.structure_id = 'Si'
    lp.scale = 2.0
    assert lp.structure_id.value == 'Si'
    assert lp.scale.value == 2.0

    coll = LinkedStructures()
    coll.create(structure_id='Si', scale=2.0)

    # CIF loop header presence
    cif = coll.as_cif
    assert 'loop_' in cif
    assert '_linked_structure.structure_id' in cif
    assert '_linked_structure.scale' in cif
