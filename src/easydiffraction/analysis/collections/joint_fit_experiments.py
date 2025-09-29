# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause


from easydiffraction.core.categories import CategoryCollection
from easydiffraction.core.categories import CategoryItem
from easydiffraction.core.parameters import Descriptor


class JointFitExperiment(CategoryItem):
    _class_public_attrs = {
        'name',
        'id',
        'weight',
    }

    @property
    def category_key(self) -> str:
        return 'joint_fit_experiment'

    def __init__(self, id: str, weight: float) -> None:
        super().__init__()

        self.id: Descriptor = Descriptor(
            value=id,  # TODO: need new name instead of id
            name='id',
            value_type=str,
            full_cif_names=['_joint_fit_experiment.id'],
            default_value=id,
        )
        self.weight: Descriptor = Descriptor(
            value=weight,
            name='weight',
            value_type=float,
            full_cif_names=['_joint_fit_experiment.weight'],
            default_value=weight,
        )
        self._category_entry_attr_name = self.id.name
        self.name = self.id.value


class JointFitExperiments(CategoryCollection):
    """Collection manager for experiments that are fitted together in a
    `joint` fit.
    """

    def __init__(self):
        super().__init__(item_type=JointFitExperiment)
