import re
from asteval import Interpreter


class BaseSingleton:
    _instance = None  # shared singleton instance

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


class UidMapHandler(BaseSingleton):
    def __init__(self):
        self._uid_map = {}

    def set_uid_map(self, params: list):
        self._uid_map = {param.uid: param for param in params}

    def get_uid_map(self):
        return self._uid_map


class ConstraintsHandler(BaseSingleton):
    def __init__(self):
        self._constraints = []
        self._alias_to_param = {}  # maps alias to parameter object
        self._uid_to_param = {}    # maps uid to parameter object

    def add(self, **kwargs):
        if 'expression' not in kwargs:
            raise ValueError("Expression must be provided as 'expression'='...'")
        expression = kwargs.pop('expression')
        alias_map = kwargs

        # Store alias-to-param and uid-to-param mappings
        for alias, param in alias_map.items():
            self._alias_to_param[alias] = param
            self._uid_to_param[param.uid] = param

        # Replace aliases in the expression with parameter UIDs
        parsed_expr = expression
        for alias, param in alias_map.items():
            parsed_expr = re.sub(rf'\b{alias}\b', f'params["{param.uid}"].value', parsed_expr)

        constraint = {
            'aliases': alias_map,
            'original_expr': expression,
            'parsed_expr': parsed_expr
        }
        self._constraints.append(constraint)

    def remove(self, number: int):
        if number < 1 or number > len(self._constraints):
            raise IndexError(f"No constraint with number {number}")
        removed = self._constraints.pop(number - 1)
        #print(f"Removed constraint: {removed['original_expr']}")

    def apply(self, parameters: list):
        if not parameters:
            return

        if not self._constraints:
            return

        asteval_interpreter = Interpreter()

        uid_map_handler = UidMapHandler.get()
        uid_map = uid_map_handler.get_uid_map()

        for constraint in self._constraints:
            try:
                expr = constraint['parsed_expr']

                # Extract dependent UID
                lhs_match = re.match(r'params\["(.+?)"\]\.value\s*=', expr)
                if not lhs_match:
                    print(f"Could not identify dependent parameter in: {constraint['original_expr']}")
                    continue

                dependent_uid = lhs_match.group(1)

                # Prepare 'params' dictionary for evaluation
                asteval_interpreter.symtable['params'] = uid_map

                # Evaluate
                asteval_interpreter(expr)

                # Set .constrained = True
                uid_map[dependent_uid].constrained = True

                # If ae(expr) is not working:

                # Evaluate only RHS of expression
                #rhs_expr = expr.split('=', 1)[1].strip()
                #rhs_value = ae(rhs_expr)

                # Apply to the real parameter
                #uid_map[dependent_uid].value = float(rhs_value)
                #uid_map[dependent_uid].constrained = True

            except Exception as e:
                print(f"Error applying constraint '{constraint['original_expr']}': {e}")

    # TODO: Implement changing atrr '.constrained' back to False
    #  when removing constraints