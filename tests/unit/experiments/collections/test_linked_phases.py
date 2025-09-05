from easydiffraction.experiments.collections.linked_phases import LinkedPhase
from easydiffraction.experiments.collections.linked_phases import LinkedPhases


def test_linked_phase_category_key():
    lp = LinkedPhase(id='phase1', scale=1.0)
    assert lp.category_key == 'linked_phases'


def test_linked_phase_cif_category_key():
    lp = LinkedPhase(id='phase1', scale=1.0)
    assert lp.cif_category_key == 'pd_phase_block'


def test_linked_phase_init():
    lp = LinkedPhase(id='phase1', scale=1.23)
    assert lp.id.value == 'phase1'
    assert lp.id.name == 'id'
    assert lp.id.cif_name == 'id'
    assert lp.scale.value == 1.23
    assert lp.scale.name == 'scale'
    assert lp.scale.cif_name == 'scale'


def test_linked_phases_type():
    lps = LinkedPhases()
    assert lps._type == 'category'


def test_linked_phases_child_class():
    lps = LinkedPhases()
    assert lps._child_class is LinkedPhase


def test_linked_phases_init_empty():
    lps = LinkedPhases()
    assert len(lps._items) == 0


def test_linked_phases_add():
    lps = LinkedPhases()
    lps.add(id='phase1', scale=1.0)
    lps.add(id='phase2', scale=2.0)
    assert len(lps._items) == 2
    assert lps['phase1'].scale.value == 1.0
    assert lps['phase2'].scale.value == 2.0
