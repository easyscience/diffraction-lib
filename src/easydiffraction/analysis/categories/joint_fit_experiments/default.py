# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Joint-fit experiment weighting configuration.

Stores per-experiment weights to be used when multiple experiments are
fitted simultaneously.
"""

from __future__ import annotations

from easydiffraction.analysis.categories.joint_fit_experiments.factory import (
    JointFitExperimentsFactory,
)
from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.validation import RegexValidator
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import CifHandler


class JointFitExperiment(CategoryItem):
    """A single joint-fit entry.

    Args:
        id: Experiment identifier used in the fit session.
        weight: Relative weight factor in the combined objective.
    """

    def __init__(self) -> None:
        super().__init__()

        self._id: StringDescriptor = StringDescriptor(
            name='id',  # TODO: need new name instead of id
            description='Experiment identifier',  # TODO
            value_spec=AttributeSpec(
                default='_',
                validator=RegexValidator(pattern=r'^[A-Za-z_][A-Za-z0-9_]*$'),
            ),
            cif_handler=CifHandler(names=['_joint_fit_experiment.id']),
        )
        self._weight: NumericDescriptor = NumericDescriptor(
            name='weight',
            description='Weight factor',  # TODO
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_joint_fit_experiment.weight']),
        )

        self._identity.category_code = 'joint_fit_experiment'
        self._identity.category_entry_name = lambda: str(self.id.value)

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def id(self) -> StringDescriptor:
        """Experiment identifier.

        Returns:
            StringDescriptor: Experiment identifier.
        """
        return self._id

    @id.setter
    def id(self, value: str) -> None:
        """Set the experiment identifier.

        Args:
            value: Experiment identifier.
        """
        self._id.value = value

    @property
    def weight(self) -> NumericDescriptor:
        """Weight factor.

        Returns:
            NumericDescriptor: Weight factor.
        """
        return self._weight

    @weight.setter
    def weight(self, value: float) -> None:
        """Set the weight factor.

        Args:
            value: Weight factor.
        """
        self._weight.value = value


@JointFitExperimentsFactory.register
class JointFitExperiments(CategoryCollection):
    """Collection of :class:`JointFitExperiment` items."""

    type_info = TypeInfo(
        tag='default',
        description='Joint-fit experiment weights',
    )

    def __init__(self):
        """Create an empty joint-fit experiments collection."""
        super().__init__(item_type=JointFitExperiment)
