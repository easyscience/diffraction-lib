from easydiffraction.core.objects import (
    Descriptor,
    Collection, Component
)


class JointFitExperiment(Component):
    def __init__(self, id: str, weight: float):
        super().__init__()

        self.id = Descriptor(
            value=id,
            name="id",
            cif_name="id"
        )
        self.weight = Descriptor(
            value=weight,
            name="weight",
            cif_name="weight"
        )

    @property
    def cif_category_key(self):
        return "joint_fit_experiment"

    @property
    def category_key(self):
        return "joint_fit_experiment"

    @property
    def _entry_id(self):
        return self.id.value


class JointFitExperiments(Collection):
    """
    Collection manager for experiments that are fitted together
    in a `joint` fit.
    """
    @property
    def _type(self):
        return "category"  # datablock or category

    def add(self, id: str, weight: float):
        expt = JointFitExperiment(id, weight)
        self._items[expt.id.value] = expt
