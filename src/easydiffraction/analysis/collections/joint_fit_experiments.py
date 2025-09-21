# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from typing import Type

from easydiffraction.core.objects import CategoryCollection
from easydiffraction.core.objects import CategoryItem
from easydiffraction.core.objects import Descriptor


class JointFitExperiment(CategoryItem):
    @property
    def category_key(self) -> str:
        return 'joint_fit_experiment'

    def __init__(self, id: str, weight: float) -> None:
        super().__init__()

        self.id: Descriptor = Descriptor(
            value=id,
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

        # Select which of the input parameters is used for the
        # as ID for the whole object
        self._entry_name = id

        # Lock further attribute additions to prevent
        # accidental modifications by users
        self._locked = True


class JointFitExperiments(CategoryCollection):
    """Collection manager for experiments that are fitted together in a
    `joint` fit.
    """

    @property
    def _type(self) -> str:
        return 'category'  # datablock or category

    @property
    def _child_class(self) -> Type[JointFitExperiment]:
        return JointFitExperiment
