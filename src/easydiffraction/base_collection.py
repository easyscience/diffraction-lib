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
                # Skip None components
                if component is None:
                    continue

                # If it's a list-like collection (e.g., AtomSites)
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
        """
        params = []

        # Use getattr for better attribute access (ignore callables and privates)
        for attr_name in dir(component):
            if attr_name.startswith('_'):
                continue

            attr = getattr(component, attr_name)

            # Skip methods
            if callable(attr):
                continue

            if hasattr(attr, 'is_parameter') and attr.is_parameter:
                # Handle AtomSite case specially to show the label in cif_name
                if getattr(component, 'cif_category_name', '') == '_atom_site':
                    label = getattr(component, 'label', None)
                    if label:
                        cif_name = f"{component.cif_category_name}['{label.value}'].{attr.cif_name}"
                    else:
                        cif_name = f"{component.cif_category_name}.{attr.cif_name}"
                else:
                    cif_name = f"{component.cif_category_name}.{attr.cif_name}"

                param_info = {
                    "item_id": item_id,
                    "component": component.__class__.__name__,
                    "param_name": attr_name,
                    "cif_name": cif_name,
                    "value": attr.value,
                    "error": attr.uncertainty if attr.uncertainty != 0.0 else '',
                    "free": attr.vary
                }
                params.append(param_info)

        return params

    def get_free_params(self):
        """
        Collects only the parameters marked as free (refinable).
        """
        all_params = self.get_all_parameters()
        free_params = [param for param in all_params if param["free"]]
        return free_params

    def show_all_parameters_table(self):
        """
        Displays all parameters as a table.
        """
        params = self.get_all_parameters()

        if not params:
            print("No parameters found.")
            return

        df = pd.DataFrame(params)
        df.rename(columns={
            "item_id": "block",
            "cif_name": "cif_name",
            "error": "error",
            "free": "free"
        }, inplace=True)

        df = df[["block", "cif_name", "value", "error", "free"]]

        try:
            print(tabulate(df, headers="keys", tablefmt="psql", showindex=False))
        except ImportError:
            print(df.to_string(index=False))

    def show_free_params(self):
        """
        Displays only the free (refinable) parameters as a table.
        """
        params = self.get_free_params()

        if not params:
            print("Free Parameters:\nNo free parameters found.")
            return

        df = pd.DataFrame(params)
        df.rename(columns={
            "item_id": "block",
            "cif_name": "cif_name",
            "error": "error",
            "free": "free"
        }, inplace=True)

        df = df[["block", "cif_name", "value", "error", "free"]]

        print("Free Parameters:")
        try:
            print(tabulate(df, headers="keys", tablefmt="psql", showindex=False))
        except ImportError:
            print(df.to_string(index=False))