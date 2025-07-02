import numpy as np
from typing import Type

from easydiffraction.core.objects import (
    Parameter,
    Descriptor,
    Component,
    Collection
)


class ExcludedRegion(Component):
    @property
    def category_key(self) -> str:
        return "excluded_region"

    @property
    def cif_category_key(self) -> str:
        return "excluded_region"

    def __init__(self,
                 minimum: float,
                 maximum: float):
        super().__init__()

        self.minimum = Descriptor(
            value=minimum,
            name="minimum",
            cif_name="minimum"
        )
        self.maximum = Parameter(
            value=maximum,
            name="maximum",
            cif_name="maximum"
        )

        # Select which of the input parameters is used for the
        # as ID for the whole object
        self._entry_id = f'{minimum}-{maximum}'

        # Lock further attribute additions to prevent
        # accidental modifications by users
        self._locked = True


class ExcludedRegions(Collection):
    """
    Collection of ExcludedRegion instances.
    """
    @property
    def _type(self) -> str:
        return "category"  # datablock or category

    @property
    def _child_class(self) -> Type[ExcludedRegion]:
        return ExcludedRegion

    def on_item_added(self, item: ExcludedRegion) -> None:
        """
        Mark excluded points in the experiment pattern when a new region is added.
        """
        experiment = self._parent
        pattern = experiment.datastore.pattern
        x = pattern.x

        # Boolean mask for points within the new excluded region
        in_region = (x >= item.minimum.value) & (x <= item.maximum.value)

        # Update the exclusion mask
        pattern.excluded[in_region] = True
