import pandas as pd
from tabulate import tabulate


class BaseCollection:
    """
    Base class for collections like SampleModels and Experiments.
    Provides common methods for gathering and displaying parameters.
    """

    def __init__(self):
        self._items = {}

    def get_all_parameters(self):
        """
        Collects all parameters from each item and its components, including nested collections.
        Returns a list of dictionaries with full CIF names and attributes.
        """
        params = []

        for item_id, item in self._items.items():
            components = item.__dict__

            for comp_name, component in components.items():
                if component is None:
                    continue

                # Handle iterable components (e.g., AtomSites)
                if hasattr(component, '__iter__') and not isinstance(component, (str, bytes, dict)):
                    for subcomponent in component:
                        if hasattr(subcomponent, '__dict__'):
                            params += self._extract_params(item_id, subcomponent)
                else:
                    # Handle normal components (like cell, space_group, etc.)
                    if hasattr(component, '__dict__'):
                        params += self._extract_params(item_id, component)

        return params

    def _extract_params(self, item_id, component):
        """
        Extracts parameters from a single component.
        Returns a list of parameter dictionaries.
        """
        params = []
        category = getattr(component, 'cif_category_name', '')

        for attr_name in dir(component):
            if attr_name.startswith('_'):
                continue

            attr = getattr(component, attr_name)

            if callable(attr):
                continue

            if getattr(attr, 'is_parameter', False):
                cif_name = self._compose_cif_name(component, category, attr)
                param_info = {
                    "block": item_id,
                    "component": component.__class__.__name__,
                    "param_name": attr_name,
                    "cif_name": cif_name,
                    "value": attr.value,
                    "error": '' if attr.uncertainty == 0.0 else attr.uncertainty,
                    "free": attr.free
                }
                params.append(param_info)

        return params

    def _compose_cif_name(self, component, category, attr):
        """
        Composes the CIF name based on the component and attribute.
        """
        if category == '_atom_site':
            label = getattr(component, 'label', None)
            if label:
                return f"{category}['{label.value}'].{attr.cif_name}"
        return f"{category}.{attr.cif_name}"

    def get_free_params(self):
        """
        Collects only the parameters marked as free (refinable).
        Returns a list of parameter dictionaries.
        """
        free_params = []

        for item_id, item in self._items.items():
            components = item.__dict__

            for comp_name, component in components.items():
                if component is None:
                    continue

                subcomponents = (
                    component if hasattr(component, '__iter__') and not isinstance(component, (str, bytes, dict))
                    else [component]
                )

                for subcomponent in subcomponents:
                    if not hasattr(subcomponent, '__dict__'):
                        continue

                    category = getattr(subcomponent, 'cif_category_name', '')

                    for attr_name in dir(subcomponent):
                        if attr_name.startswith('_'):
                            continue

                        attr = getattr(subcomponent, attr_name)

                        if callable(attr):
                            continue

                        if getattr(attr, 'is_parameter', False) and attr.free:
                            cif_name = self._compose_cif_name(subcomponent, category, attr)
                            param_info = {
                                "block": item_id,
                                "cif_name": cif_name,
                                "value": attr.value,
                                "error": '' if attr.uncertainty == 0.0 else attr.uncertainty,
                                "free": attr.free,
                                "parameter": attr
                            }
                            free_params.append(param_info)

        return free_params

    def _display_table(self, params, title):
        """
        Displays a formatted table using tabulate or fallback to pandas.
        """
        if not params:
            print(f"{title}\nNo parameters found.")
            return

        df = pd.DataFrame(params)

        # Ensure columns exist
        expected_cols = ["block", "cif_name", "value", "error", "free"]
        valid_cols = [col for col in expected_cols if col in df.columns]

        if not valid_cols:
            print(f"{title}\nNo valid columns found in DataFrame.")
            return

        df = df[valid_cols]

        print(f"\n{title}")
        try:
            print(tabulate(df, headers="keys", tablefmt="psql", showindex=False))
        except ImportError:
            print(df.to_string(index=False))

    def show_all_parameters_table(self):
        """
        Displays all parameters as a table.
        """
        params = self.get_all_parameters()
        self._display_table(params, "All Parameters:")

    def show_free_params(self):
        """
        Displays only the parameters that are free to refine.
        """
        params = self.get_free_params()
        self._display_table(params, "Free Parameters:")