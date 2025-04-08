from easydiffraction.core.component import (StandardComponent,
                                            IterableComponent)


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

    def get_all_params(self):
        params = []
        for datablock in self._items.values():
            for component in datablock.components():
                if isinstance(component, StandardComponent):
                    standard_component = component
                    for param in standard_component.parameters():
                        param.cif_datablock_id = datablock.name
                        param.cif_category_key = standard_component.cif_category_key
                        param.cif_entry_id = ""
                        params.append(param)
                elif isinstance(component, IterableComponent):
                    iterable_component = component
                    for standard_component in iterable_component:
                        for param in standard_component.parameters():
                            param.cif_datablock_id = datablock.name
                            param.cif_category_key = standard_component.cif_category_key
                            param.cif_entry_id = standard_component.id.value
                            params.append(param)

        return params

    def get_fittable_params(self):
        all_params = self.get_all_params()
        params = []
        for param in all_params:
            if hasattr(param, 'free') and not param.constrained:
                params.append(param)
        return params

    def get_free_params(self):
        fittable_params = self.get_fittable_params()
        params = []
        for param in fittable_params:
            if param.free:
                params.append(param)
        return params
