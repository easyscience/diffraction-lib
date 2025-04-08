from easydiffraction.core.parameter import (Parameter,
                                            Descriptor)
from easydiffraction.core.component import StandardComponent
from easydiffraction.core.collection import Collection


class LinkedPhase(StandardComponent):
    @property
    def cif_category_key(self):
        return "_pd_phase_block"

    def __init__(self, id: str, scale: float):
        super().__init__()

        self.id = Descriptor(
            value=id,
            cif_param_name="id"
        )
        self.scale = Parameter(
            value=scale,
            cif_param_name="scale"
        )

        self._locked = True  # Lock further attribute additions

        # TODO: Add _id as in AtomSite

class LinkedPhases(Collection):
    """
    Collection of LinkedPhase instances.
    """
    @property
    def _type(self):
        return "category"  # datablock or category

    def add(self, id: str, scale: float):
        phase = LinkedPhase(id, scale)
        self._items[phase.id.value] = phase
