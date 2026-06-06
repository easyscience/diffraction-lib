# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Joint-fit weighting configuration.

Stores per-experiment weights to be used when multiple experiments are
fitted simultaneously.
"""

from __future__ import annotations

from easydiffraction.analysis.categories.joint_fit.factory import JointFitFactory
from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.validation import RegexValidator
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import CifHandler


class JointFitItem(CategoryItem):
    """A single joint-fit entry."""

    _category_code = 'joint_fit'
    _category_entry_name = 'experiment_id'

    def __init__(self) -> None:
        """Initialize the experiment id and weight descriptors."""
        super().__init__()

        self._experiment_id: StringDescriptor = StringDescriptor(
            name='experiment_id',
            description='Experiment identifier',  # TODO: revisit description
            value_spec=AttributeSpec(
                default='_',
                validator=RegexValidator(pattern=r'^[A-Za-z_][A-Za-z0-9_]*$'),
            ),
            cif_handler=CifHandler(
                names=['_joint_fit.experiment_id'],
                iucr_name='_easydiffraction_joint_fit.experiment_id',
            ),
        )
        self._weight: NumericDescriptor = NumericDescriptor(
            name='weight',
            description='Weight factor',  # TODO: revisit description
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=['_joint_fit.weight'],
                iucr_name='_easydiffraction_joint_fit.weight',
            ),
        )

    @property
    def experiment_id(self) -> StringDescriptor:
        """
        Experiment identifier.

        Reading this property returns the underlying
        ``StringDescriptor`` object. Assigning to it updates the
        parameter value.
        """
        return self._experiment_id

    @experiment_id.setter
    def experiment_id(self, value: str) -> None:
        """Set the experiment identifier value."""
        self._experiment_id.value = value

    @property
    def weight(self) -> NumericDescriptor:
        """
        Weight factor.

        Reading this property returns the underlying
        ``NumericDescriptor`` object. Assigning to it updates the
        parameter value.
        """
        return self._weight

    @weight.setter
    def weight(self, value: float) -> None:
        """Set the joint-fit weight factor value."""
        self._weight.value = value


@JointFitFactory.register
class JointFitCollection(CategoryCollection):
    """Collection of :class:`JointFitItem` items."""

    type_info = TypeInfo(
        tag='default',
        description='Joint-fit experiment weights',
    )

    def __init__(self) -> None:
        """Create an empty joint-fit collection."""
        super().__init__(item_type=JointFitItem)
