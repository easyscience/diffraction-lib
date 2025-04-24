from easydiffraction.core.objects import (
    Parameter,
    Descriptor,
    Component,
    Collection
)


class LinkedPhase(Component):
    def __init__(self, id: str, scale: float) -> None:
        super().__init__()

        self.id = Descriptor(
            value=id,
            name="id",
            cif_name="id"
        )
        self.scale = Parameter(
            value=scale,
            name="scale",
            cif_name="scale"
        )

        self._locked = True  # Lock further attribute additions

    @property
    def cif_category_key(self) -> str:
        return "pd_phase_block"

    @property
    def category_key(self) -> str:
        return "linked_phase"

    @property
    def _entry_id(self) -> str:
        return self.id.value


class LinkedPhases(Collection):
    """
    Collection of LinkedPhase instances.
    """
    @property
    def _type(self) -> str:
        return "category"  # datablock or category

    def add(self, id: str, scale: float) -> None:
        phase = LinkedPhase(id, scale)
        self._items[phase.id.value] = phase
