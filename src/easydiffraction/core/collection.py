import pandas as pd
from tabulate import tabulate


class Collection:
    """
    Base class for collections like SampleModels and Experiments.
    Provides common methods for gathering and displaying parameters.
    """

    def __init__(self):
        self._items = {}

    def __getitem__(self, key):
        return self._items[key]

    def __iter__(self):
        return iter(self._items.values())

    def get_all_parameters(self):
        """
        Collects all parameters from each item and its components, including nested collections.
        Returns a list of dictionaries with full CIF names and attributes.
        """
        # TODO: Fails to handle properly iterable_components
        # TODO: Need to refactor this method to use the new parameter,
        #  component and collection based system
        params = []

        for item_id, item in self._items.items():
            components = item.__dict__

            for comp_name, component in components.items():
                if component is None:
                    continue

                # Handle iterable_components (e.g., AtomSites)
                if hasattr(component, '__iter__') and not isinstance(component, (str, bytes, dict)):
                    for subcomponent in component:
                        if hasattr(subcomponent, '__dict__'):
                            params += self._extract_params(item_id, subcomponent)
                else:
                    # Handle standard_components (e.g., Cell, SpaceGroup)
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
        Returns a list of Parameter instances.
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

                    for attr_name in dir(subcomponent):
                        if attr_name.startswith('_'):
                            continue

                        attr = getattr(subcomponent, attr_name)

                        if callable(attr):
                            continue

                        if getattr(attr, 'is_parameter', False) and attr.free:
                            # Set the block_name for the parameter to generate its unique id
                            attr.block_name = item_id
                            # TODO: Refactor this method. Check if we need generate unique id here
                            #attr.uid = attr._generate_unique_id()
                            free_params.append(attr)

        return free_params

    def _display_table(self, params, title):
        """
        Displays a formatted table using tabulate or fallback to pandas.
        """
        if not params:
            print(f"{title}\nNo parameters found.")
            return

        # Convert a list of parameters to custom dictionaries
        params = [
            {
                'cif block': param['block'],
                'cif parameter': param['cif_name'],
                'value': param['value'],
                'error': param['error'] if param['error'] else '',
                'free': param['free']
            }
            for param in params
        ]

        df = pd.DataFrame(params)

        # Ensure columns exist
        expected_cols = ["cif block", "cif parameter", "value", "error", "free"]
        valid_cols = [col for col in expected_cols if col in df.columns]

        if not valid_cols:
            print(f"{title}\nNo valid columns found in DataFrame.")
            return

        df = df[valid_cols]

        print(f"\n{title}")
        try:
            print(tabulate(df, headers="keys", tablefmt="fancy_outline", showindex=False))
        except ImportError:
            print(df.to_string(index=False))

    def show_all_parameters_table(self):
        """
        Displays all parameters as a table.
        """
        params = self.get_all_parameters()
        self._display_table(params, f"All '{self.__class__.__name__}' parameters:")
