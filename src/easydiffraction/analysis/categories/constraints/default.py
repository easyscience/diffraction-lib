# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Simple symbolic constraint between parameters.

Represents an equation of the form ``lhs_alias = rhs_expr`` stored as a
single expression string.  The left- and right-hand sides are derived by
splitting the expression at the ``=`` sign.
"""

from __future__ import annotations

from easydiffraction.analysis.categories.constraints.factory import ConstraintsFactory
from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RegexValidator
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import CifHandler
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log
from easydiffraction.utils.utils import render_table


class Constraint(CategoryItem):
    """Single constraint item stored as ``lhs = rhs`` expression."""

    _category_code = 'constraint'
    _category_entry_name = 'id'

    def __init__(self) -> None:
        """Initialize the constraint id and expression descriptors."""
        super().__init__()

        self._id = StringDescriptor(
            name='id',
            description='Explicit identifier for this constraint row.',
            value_spec=AttributeSpec(
                default='_',
                validator=RegexValidator(pattern=r'^[A-Za-z0-9_]*$'),
            ),
            cif_handler=CifHandler(
                names=['_constraint.id'],
                iucr_name='_easydiffraction_constraint.id',
            ),
        )
        self._expression = StringDescriptor(
            name='expression',
            description='Constraint equation, e.g. "occ_Ba = 1 - occ_La".',
            value_spec=AttributeSpec(
                default='_',  # TODO: Maybe None?
                validator=RegexValidator(pattern=r'.*'),
            ),
            cif_handler=CifHandler(
                names=['_constraint.expression'],
                iucr_name='_easydiffraction_constraint.expression',
            ),
        )

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def id(self) -> StringDescriptor:
        """Explicit identifier for this constraint row."""
        return self._id

    @id.setter
    def id(self, value: str) -> None:
        """Set the constraint identifier value."""
        self._id.value = value

    @property
    def expression(self) -> StringDescriptor:
        """
        Full constraint equation (e.g. ``'occ_Ba = 1 - occ_La'``).

        Reading this property returns the underlying
        ``StringDescriptor`` object. Assigning to it updates the value.
        """
        return self._expression

    @expression.setter
    def expression(self, value: str) -> None:
        """Set the constraint equation value."""
        self._expression.value = value

    @property
    def lhs_alias(self) -> str:
        """Left-hand side alias derived from the expression."""
        return self._split_expression()[0]

    @property
    def rhs_expr(self) -> str:
        """Right-hand side expression derived from the expression."""
        return self._split_expression()[1]

    # ------------------------------------------------------------------
    #  Internal helpers
    # ------------------------------------------------------------------

    def _split_expression(self) -> tuple[str, str]:
        """
        Split the expression at the first ``=`` sign.

        Returns
        -------
        tuple[str, str]
            ``(lhs_alias, rhs_expr)`` with whitespace stripped.
        """
        raw = self._expression.value or ''
        if '=' not in raw:
            return (raw.strip(), '')
        lhs, rhs = raw.split('=', 1)
        return (lhs.strip(), rhs.strip())


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
        self._enabled: bool = False

    @property
    def enabled(self) -> bool:
        """Whether constraints are currently active."""
        return self._enabled

    def enable(self) -> None:
        """Activate constraints so they are applied during fitting."""
        self._enabled = True

    def disable(self) -> None:
        """Deactivate constraints without deleting them."""
        self._enabled = False

    def create(self, *, expression: str, id: str | None = None) -> None:
        """
        Create a constraint from an expression string.

        Automatically enables constraints on the first call.

        Parameters
        ----------
        expression : str
            Constraint equation, e.g. ``'biso_Co2 = biso_Co1'`` or
            ``'occ_Ba = 1 - occ_La'``.
        id : str | None, default=None
            Explicit row identifier. When not ``None``, this value is
            used as the collection key instead of the left-hand alias.
        """
        item = Constraint()
        item.expression = expression
        if id is not None:
            item.id = id
        elif item.lhs_alias:
            item.id = item.lhs_alias
        self.add(item)
        self._enabled = True

    def _after_from_cif(self) -> None:
        """
        Backfill explicit ids when loading older CIF constraint loops.
        """
        for item in self:
            constraint_id = item.id.value.strip()
            if constraint_id not in {'', '_', '?'} or not item.lhs_alias:
                continue
            item.id = item.lhs_alias

    def show(self) -> None:
        """Print a table of all user-defined symbolic constraints."""
        if not self._items:
            log.warning('No constraints defined.')
            return

        rows = [[constraint.id.value, constraint.expression.value] for constraint in self]

        console.paragraph('User defined constraints')
        render_table(
            columns_headers=['id', 'expression'],
            columns_alignment=['left', 'left'],
            columns_data=rows,
        )
        console.print(f'Constraints enabled: {self.enabled}')
