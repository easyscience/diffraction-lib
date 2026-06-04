# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from typing import Any
from typing import Self

from asteval import Interpreter

from easydiffraction.utils.logging import log

# ======================================================================


class SingletonBase:
    """
    Base class to implement Singleton pattern.

    Ensures only one shared instance of a class is ever created. Useful
    for managing shared state across the library.
    """

    _instance = None  # Class-level shared instance

    @classmethod
    def get(cls) -> Self:
        """Return the shared instance, creating it if needed."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


# ======================================================================


# TODO: Implement changing attr '.user_constrained' back to False
#  when removing constraints
class ConstraintsHandler(SingletonBase):
    """
    Manage parameter constraints using aliases and expressions.

    Uses the asteval interpreter for safe evaluation of mathematical
    expressions. Constraints are defined as: lhs_alias =
    expression(rhs_aliases).
    """

    def __init__(self) -> None:
        # Maps alias names
        # (like 'biso_La') → Alias(param=Parameter)
        self._alias_to_param: dict[str, Any] = {}

        # Stores raw user-defined constraints indexed by lhs_alias
        # Each value should contain: lhs_alias, rhs_expr
        self._constraints = {}

        # Internally parsed constraints as (lhs_alias, rhs_expr) tuples
        self._parsed_constraints: list[tuple[str, str]] = []

    def set_aliases(self, aliases: object) -> None:
        """
        Set the alias map (name → alias wrapper).

        Called when user registers parameter aliases like:
        alias='biso_La', param=model.atom_sites['La'].adp_iso
        """
        self._alias_to_param = dict(aliases.items())

    def set_constraints(self, constraints: object) -> None:
        """
        Set the constraints and triggers parsing into internal format.

        Called when user registers expressions like: lhs_alias='occ_Ba',
        rhs_expr='1 - occ_La'
        """
        self._constraints = constraints._items
        self._parse_constraints()

    def _parse_constraints(self) -> None:
        """Parse raw expressions into (lhs_alias, rhs_expr) pairs."""
        self._parsed_constraints = []

        for expr_obj in self._constraints:
            lhs_alias = expr_obj.lhs_alias
            rhs_expr = expr_obj.rhs_expr

            if lhs_alias and rhs_expr:
                constraint = (lhs_alias.strip(), rhs_expr.strip())
                self._parsed_constraints.append(constraint)

    def apply(self) -> None:
        """
        Evaluate constraints and apply them to dependent parameters.

        For each constraint:
        - Evaluate RHS using current values of aliased parameters
        - Locate the dependent parameter via direct alias reference
        - Update its value and mark it as user constrained
        """
        if not self._parsed_constraints:
            return  # Nothing to apply

        # Prepare a flat dict of {alias: value} for use in expressions
        param_values = {}
        for alias, alias_obj in self._alias_to_param.items():
            param = alias_obj.param
            param_values[alias] = param.value

        # Create an asteval interpreter for safe expression evaluation
        ae = Interpreter()
        ae.symtable.update(param_values)

        for lhs_alias, rhs_expr in self._parsed_constraints:
            try:
                self._apply_one_constraint(ae, lhs_alias, rhs_expr)
            except (ValueError, TypeError, ArithmeticError, KeyError, AttributeError) as error:
                print(f"Failed to apply constraint '{lhs_alias} = {rhs_expr}': {error}")

    def _apply_one_constraint(
        self,
        ae: Interpreter,
        lhs_alias: str,
        rhs_expr: str,
    ) -> None:
        """Evaluate and apply one parsed constraint expression."""
        rhs_value = ae(rhs_expr)
        if ae.error:
            error_msgs = '; '.join(str(e.get_error()) for e in ae.error)
            ae.error.clear()
            log.error(
                f"Constraint '{lhs_alias} = {rhs_expr}' could not be "
                f'evaluated: {error_msgs}. '
                f'Make sure every name in the expression is registered '
                f'as an alias via analysis.aliases.create().',
                exc_type=ValueError,
            )
        param = self._alias_to_param[lhs_alias].param
        param._set_value_user_constrained(rhs_value)
