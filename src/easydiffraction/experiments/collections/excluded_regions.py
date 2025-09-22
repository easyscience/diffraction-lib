# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from typing import List

from easydiffraction.core.objects import CategoryCollection
from easydiffraction.core.objects import CategoryItem
from easydiffraction.core.objects import Descriptor
from easydiffraction.core.objects import Parameter
from easydiffraction.utils.formatting import paragraph
from easydiffraction.utils.utils import render_table


class ExcludedRegion(CategoryItem):
    _allowed_attributes = {
        'start',
        'end',
    }

    @property
    def category_key(self) -> str:
        return 'excluded_regions'

    def __init__(
        self,
        start: float,
        end: float,
    ):
        super().__init__()

        self.start = Descriptor(
            value=start,
            name='start',
            value_type=float,
            full_cif_names=['_excluded_region.start'],
            default_value=start,
            description='Start of the excluded region.',
        )
        self.end = Parameter(
            value=end,
            name='end',
            full_cif_names=['_excluded_region.end'],
            default_value=end,
            description='End of the excluded region.',
        )
        # self._category_entry_attr_name = f'{start}-{end}'
        self._category_entry_attr_name = self.start.name


class ExcludedRegions(CategoryCollection):
    """Collection of ExcludedRegion instances."""

    def __init__(self):
        super().__init__(child_class=ExcludedRegion)

    def _on_item_added(self, item: ExcludedRegion) -> None:
        """Mark excluded points in the experiment pattern when a new
        region is added.
        """
        datastore = self._parent.datastore

        # Boolean mask for points within the new excluded region
        in_region = (datastore.full_x >= item.start.value) & (datastore.full_x <= item.end.value)

        # Update the exclusion mask
        datastore.excluded[in_region] = True

        # Update the excluded points in the datastore
        datastore.x = datastore.full_x[~datastore.excluded]
        datastore.meas = datastore.full_meas[~datastore.excluded]
        datastore.meas_su = datastore.full_meas_su[~datastore.excluded]

    def show(self) -> None:
        # TODO: Consider moving this to the base class
        #  to avoid code duplication with implementations in Background,
        #  etc. Consider using parameter names as column headers
        columns_headers: List[str] = ['start', 'end']
        columns_alignment = ['left', 'left']
        columns_data: List[List[float]] = []
        for region in self._items.values():
            start = region.start.value
            end = region.end.value
            columns_data.append([start, end])

        print(paragraph('Excluded regions'))
        render_table(
            columns_headers=columns_headers,
            columns_alignment=columns_alignment,
            columns_data=columns_data,
        )
