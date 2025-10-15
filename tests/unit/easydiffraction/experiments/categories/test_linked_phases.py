def test_linked_phases_add_and_cif_headers():
    from easydiffraction.experiments.categories.linked_phases import LinkedPhase, LinkedPhases

    lp = LinkedPhase(id='Si', scale=2.0)
    assert lp.id.value == 'Si' and lp.scale.value == 2.0

    coll = LinkedPhases()
    coll.add(lp)

    # CIF loop header presence
    cif = coll.as_cif
    assert 'loop_' in cif and '_pd_phase_block.id' in cif and '_pd_phase_block.scale' in cif
