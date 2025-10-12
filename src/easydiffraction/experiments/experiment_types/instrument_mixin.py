from __future__ import annotations

from typeguard import typechecked

from easydiffraction.experiments.category_items.instrument_setups import InstrumentBase
from easydiffraction.experiments.category_items.instrument_setups import InstrumentFactory


class InstrumentMixin:
    def __init__(self, *args, **kwargs):
        expt_type = kwargs.get('type')
        super().__init__(*args, **kwargs)
        self._instrument = InstrumentFactory.create(
            scattering_type=expt_type.scattering_type.value,
            beam_mode=expt_type.beam_mode.value,
        )

    @property
    def instrument(self):
        return self._instrument

    @instrument.setter
    @typechecked
    def instrument(self, new_instrument: InstrumentBase):
        self._instrument = new_instrument
        self._instrument._parent = self
