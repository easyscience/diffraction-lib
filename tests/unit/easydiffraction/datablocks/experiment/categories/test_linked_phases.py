# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause


def test_linked_phases_add_and_cif_headers():
    from easydiffraction.datablocks.experiment.categories.linked_phases import LinkedPhase
    from easydiffraction.datablocks.experiment.categories.linked_phases import LinkedPhases

    lp = LinkedPhase()
    lp.id = 'Si'
    lp.scale = 2.0
    assert lp.id.value == 'Si'
    assert lp.scale.value == 2.0

    coll = LinkedPhases()
    coll.create(id='Si', scale=2.0)

    # CIF loop header presence
    cif = coll.as_cif
    assert 'loop_' in cif
    assert '_pd_phase_block.id' in cif
    assert '_pd_phase_block.scale' in cif
