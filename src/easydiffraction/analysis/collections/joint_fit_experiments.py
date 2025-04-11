from easydiffraction.core.objects import (
    Descriptor,
    Component,
    Collection
)


class JointFitExperiment(Component):
    @property
    def category_key(self):
        return "joint_fit_experiment"

    @property
    def cif_category_key(self):
        return "joint_fit_experiment"

    def __init__(self,
                 id: str,
                 weight: float):
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

        # Select which of the input parameters is used for the
        # as ID for the whole object
        self._entry_id = id

        # Lock further attribute additions to prevent
        # accidental modifications by users
        self._locked = True


class JointFitExperiments(Collection):
    """
    Collection manager for experiments that are fitted together
    in a `joint` fit.
    """
    @property
    def _type(self):
        return "category"  # datablock or category

    @property
    def _child_class(self):
        return JointFitExperiment