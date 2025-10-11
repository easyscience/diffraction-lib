# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.core.categories import CategoryCollection
from easydiffraction.core.categories import CategoryItem
from easydiffraction.core.parameters import DescriptorFloat
from easydiffraction.core.parameters import DescriptorStr
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import DataTypes
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.validation import RegexValidator
from easydiffraction.io.cif.handler import CifHandler


class JointFitExperiment(CategoryItem):
    def __init__(
        self,
        *,
        id: str,
        weight: float,
    ) -> None:
        super().__init__()

        self._id: DescriptorStr = DescriptorStr(
            name='id',  # TODO: need new name instead of id
            description='...',
            value_spec=AttributeSpec(
                value=id,
                type_=DataTypes.STRING,
                default='...',
                content_validator=RegexValidator(pattern=r'^[A-Za-z_][A-Za-z0-9_]*$'),
            ),
            cif_handler=CifHandler(
                names=[
                    '_joint_fit_experiment.id',
                ]
            ),
        )
        self._weight: DescriptorFloat = DescriptorFloat(
            name='weight',
            description='...',
            value_spec=AttributeSpec(
                value=weight,
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=[
                    '_joint_fit_experiment.weight',
                ]
            ),
        )

        # self._category_entry_attr_name = self.id.name
        # self.name = self.id.value
        self._identity.category_code = 'joint_fit_experiment'
        self._identity.category_entry_name = lambda: self.id.value

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id.value = value

    @property
    def weight(self):
        return self._weight

    @weight.setter
    def weight(self, value):
        self._weight.value = value


class JointFitExperiments(CategoryCollection):
    """Collection manager for experiments that are fitted together in a
    `joint` fit.
    """

    def __init__(self):
        super().__init__(item_type=JointFitExperiment)
