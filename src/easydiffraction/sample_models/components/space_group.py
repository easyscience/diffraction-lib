from typing import Optional
from easydiffraction.core.objects import (
    Descriptor,
    Component
)


class SpaceGroup(Component):
    """
    Represents the space group of a sample model.
    """

    def __init__(self, name_h_m: str = "P 1", it_coordinate_system_code: Optional[int] = None) -> None:
        super().__init__()

        self.name_h_m = Descriptor(
            value=name_h_m,
            name="name_h_m",
            cif_name = "name_H-M_alt"
        )
        self.it_coordinate_system_code = Descriptor(
            value=it_coordinate_system_code,
            name="it_coordinate_system_code",
            cif_name="IT_coordinate_system_code"
        )

    @property
    def cif_category_key(self) -> str:
        return "space_group"

    @property
    def category_key(self) -> str:
        return "space_group"

    @property
    def _entry_id(self) -> Optional[str]:
        return None