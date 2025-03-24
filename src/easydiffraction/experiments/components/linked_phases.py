from typing import List, Union, Iterator

from easydiffraction.parameter import Parameter, Descriptor

class LinkedPhase:
    cif_category_name = "_pd_phase_block"

    def __init__(
        self,
        id: str,
        scale: float
    ):
        # Descriptors (static values, non-refinable)
        self.id = Descriptor(id, cif_name="id")

        # Parameters (refinable)
        self.scale = Parameter(scale, cif_name="scale")

    def as_cif_row(self) -> str:
        return (
            f"{self.id.value} {self.scale.value}"
        )

class LinkedPhases:
    def __init__(self):
        self.phases: List[LinkedPhase] = []

    def add(
        self,
        id: str,
        scale: float
    ):
        phase = LinkedPhase(id, scale)
        self.phases.append(phase)

    def as_cif_loop(self) -> str:
        lines = [
            "loop_",
            "_pd_phase_block.id",
            "_pd_phase_block.scale"
        ]
        for phase in self.phases:
            lines.append(phase.as_cif_row())
        return "\n".join(lines)

    def __iter__(self) -> Iterator[LinkedPhase]:
        """
        Iterate through linked phases.
        """
        return iter(self.phases)

    def __getitem__(self, key: Union[int, str]) -> LinkedPhase:
        """
        Access a LinkedPhase by index or by id.
        """
        if isinstance(key, int):
            try:
                return self.phases[key]
            except IndexError:
                raise IndexError(f"No LinkedPhase at index {key}.")
        elif isinstance(key, str):
            for phase in self.phases:
                if phase.id.value == key:
                    return phase
            raise KeyError(f"No LinkedPhase with id '{key}' found.")
        else:
            raise TypeError("Key must be an integer index or a string id.")

    def __len__(self) -> int:
        """
        Return the number of linked phases.
        """
        return len(self.phases)
