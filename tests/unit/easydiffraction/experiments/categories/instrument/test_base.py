import pytest


def test_instrument_base_sets_category_code():
    from easydiffraction.experiments.categories.instrument.base import InstrumentBase

    class DummyInstr(InstrumentBase):
        def __init__(self):
            super().__init__()

    d = DummyInstr()
    assert d._identity.category_code == 'instrument'
