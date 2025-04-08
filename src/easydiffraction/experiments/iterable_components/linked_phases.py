from easydiffraction.core.objects import (
    Parameter,
    Descriptor,
    Component,
    Collection
)


class LinkedPhase(Component):
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

    @property
    def cif_category_key(self):
        return "pd_phase_block"

    @property
    def category_key(self):
        return "linked_phase"

    @property
    def _entry_id(self):
        return self.id.value


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
