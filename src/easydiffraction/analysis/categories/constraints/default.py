# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Simple symbolic constraint between parameters.

Represents an equation of the form ``lhs_alias = rhs_expr`` where
``rhs_expr`` is evaluated elsewhere by the analysis engine.
"""

from __future__ import annotations

from easydiffraction.analysis.categories.constraints.factory import ConstraintsFactory
from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.singleton import ConstraintsHandler
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RegexValidator
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import CifHandler


class Constraint(CategoryItem):
    """
    Single constraint item.
    """

    def __init__(self) -> None:
        super().__init__()

        self._lhs_alias = StringDescriptor(
            name='lhs_alias',
            description='Left-hand side of the equation.',  # TODO
            value_spec=AttributeSpec(
                default='...',  # TODO
                validator=RegexValidator(pattern=r'.*'),
            ),
            cif_handler=CifHandler(names=['_constraint.lhs_alias']),
        )
        self._rhs_expr = StringDescriptor(
            name='rhs_expr',
            description='Right-hand side expression.',  # TODO
            value_spec=AttributeSpec(
                default='...',  # TODO
                validator=RegexValidator(pattern=r'.*'),
            ),
            cif_handler=CifHandler(names=['_constraint.rhs_expr']),
        )

        self._identity.category_code = 'constraint'
        self._identity.category_entry_name = lambda: str(self.lhs_alias.value)

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def lhs_alias(self) -> StringDescriptor:
        """
        Left-hand side of the equation.

        Reading this property returns the underlying
        ``StringDescriptor`` object. Assigning to it updates the
        parameter value.
        """
        return self._lhs_alias

    @lhs_alias.setter
    def lhs_alias(self, value: str) -> None:
        """Set the left-hand side alias string."""
        self._lhs_alias.value = value

    @property
    def rhs_expr(self) -> StringDescriptor:
        """
        Right-hand side expression.

        Reading this property returns the underlying
        ``StringDescriptor`` object. Assigning to it updates the
        parameter value.
        """
        return self._rhs_expr

    @rhs_expr.setter
    def rhs_expr(self, value: str) -> None:
        """Set the right-hand side expression string."""
        self._rhs_expr.value = value


@ConstraintsFactory.register
class Constraints(CategoryCollection):
    """Collection of :class:`Constraint` items."""

    type_info = TypeInfo(
        tag='default',
        description='Symbolic parameter constraints',
    )

    _update_priority = 90  # After most others, but before data categories

    def __init__(self) -> None:
        """Create an empty constraints collection."""
        super().__init__(item_type=Constraint)

    def _update(self, called_by_minimizer: bool = False) -> None:
        del called_by_minimizer

        constraints = ConstraintsHandler.get()
        constraints.apply()
