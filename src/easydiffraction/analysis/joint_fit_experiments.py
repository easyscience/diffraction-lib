from easydiffraction.core.collection import Collection
from easydiffraction.core.parameter import Descriptor

class JointFitExperiments(Collection):
    """
    Collection manager for experiments that are fitted together
    in a `joint` fit.
    """
    def __init__(self):
        super().__init__()

    def add(self, id: str, weight: float):
        """Add an experiment with it's associated weight"""
        # Save both id and weight as immutable Descriptors
        self.id = Descriptor(
            value=id,
            cif_name="id"
        )
        self.weight = Descriptor(
            value=weight,
            cif_name="weight"
        )
        self._items[id] = weight

    def __getitem__(self, key):
        return self._items[key]

    def __setitem__(self, key, value):
        self._items[key] = value
