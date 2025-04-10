from asteval import Interpreter


class BaseSingleton:
    """Base class to implement Singleton pattern.

    Ensures only one shared instance of a class is ever created.
    Useful for managing shared state across the library.
    """

    _instance = None  # Class-level shared instance

    @classmethod
    def get(cls):
        """Returns the shared instance, creating it if needed."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


class UidMapHandler(BaseSingleton):
    """Global handler to manage UID-to-Parameter object mapping."""

    def __init__(self):
        # Internal map: uid (str) → Parameter instance
        self._uid_map = {}

    def get_uid_map(self):
        """Returns the current UID-to-Parameter map."""
        return self._uid_map

    def set_uid_map(self, parameters: list):
        """Populates the UID map from a list of Parameter objects."""
        self._uid_map = {param.uid: param for param in parameters}


# TODO: Implement changing atrr '.constrained' back to False
#  when removing constraints
class ConstraintsHandler(BaseSingleton):
    """Manages user-defined parameter constraints using aliases and expressions.

    Uses the asteval interpreter for safe evaluation of mathematical expressions.
    Constraints are defined as: lhs_alias = expression(rhs_aliases).
    """

    def __init__(self):
        # Maps alias names (like 'biso_La') → ConstraintAlias(param=Parameter)
        self._alias_to_param = {}

        # Stores raw user-defined expressions indexed by ID
        # Each value should contain: lhs_alias, rhs_expr
        self._expressions = {}

        # Internally parsed constraints as (lhs_alias, rhs_expr) tuples
        self._parsed_constraints = []

    def set_aliases(self, constraint_aliases):
        """
        Sets the alias map (name → parameter wrapper).
        Called when user registers parameter aliases like:
            alias='biso_La', param=model.atom_sites['La'].b_iso
        """
        self._alias_to_param = constraint_aliases._items

    def set_expressions(self, constraint_expressions):
        """
        Sets the constraint expressions and triggers parsing into internal format.
        Called when user registers expressions like:
            lhs_alias='occ_Ba', rhs_expr='1 - occ_La'
        """
        self._expressions = constraint_expressions._items
        self._parse_constraints()

    def _parse_constraints(self):
        """
        Converts raw expression input into a normalized internal list of
        (lhs_alias, rhs_expr) pairs, stripping whitespace and skipping invalid entries.
        """
        self._parsed_constraints = []

        for expr_id, expr_obj in self._expressions.items():
            lhs_alias = expr_obj.lhs_alias.value
            rhs_expr = expr_obj.rhs_expr.value

            if lhs_alias and rhs_expr:
                constraint = (lhs_alias.strip(), rhs_expr.strip())
                self._parsed_constraints.append(constraint)

    def apply(self, parameters: list):
        """Evaluates constraints and applies them to dependent parameters.

        For each constraint:
        - Evaluate RHS using current values of aliases
        - Locate the dependent parameter by alias → uid → param
        - Update its value and mark it as constrained
        """
        if not self._parsed_constraints:
            return  # Nothing to apply

        # Retrieve global UID → Parameter object map
        uid_map = UidMapHandler.get().get_uid_map()

        # Prepare a flat dict of {alias_name: value} for use in expressions
        param_values = {
            alias: alias_obj.param.value
            for alias, alias_obj in self._alias_to_param.items()
        }

        # Create an asteval interpreter for safe expression evaluation
        ae = Interpreter()
        ae.symtable.update(param_values)

        for lhs_alias, rhs_expr in self._parsed_constraints:
            try:
                # Evaluate the RHS expression using the current values
                rhs_value = ae(rhs_expr)

                # Get the actual parameter object we want to update
                dependent_param = self._alias_to_param[lhs_alias].param
                uid = dependent_param.uid

                # Update its value in the UID map and mark it as constrained
                uid_map[uid].value = rhs_value
                uid_map[uid].constrained = True

            except Exception as error:
                print(f"Failed to apply constraint '{lhs_alias} = {rhs_expr}': {error}")
