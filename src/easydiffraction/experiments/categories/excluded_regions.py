# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Exclude ranges of x from fitting/plotting (masked regions)."""

from typing import List

from easydiffraction import log
from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.parameters import NumericDescriptor
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import DataTypes
from easydiffraction.core.validation import RangeValidator
from easydiffraction.io.cif.handler import CifHandler
from easydiffraction.utils.utils import render_table


class ExcludedRegion(CategoryItem):
    """Closed interval [start, end] to be excluded."""

    def __init__(
        self,
        *,
        start: float,
        end: float,
    ):
        super().__init__()

        self._start = NumericDescriptor(
            name='start',
            description='Start of the excluded region.',
            value_spec=AttributeSpec(
                value=start,
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=[
                    '_excluded_region.start',
                ]
            ),
        )
        self._end = NumericDescriptor(
            name='end',
            description='End of the excluded region.',
            value_spec=AttributeSpec(
                value=end,
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=[
                    '_excluded_region.end',
                ]
            ),
        )
        # self._category_entry_attr_name = f'{start}-{end}'
        # self._category_entry_attr_name = self.start.name
        # self.name = self.start.value
        self._identity.category_code = 'excluded_regions'
        self._identity.category_entry_name = lambda: self.start.value

    @property
    def start(self) -> NumericDescriptor:
        return self._start

    @start.setter
    def start(self, value: float):
        self._start.value = value

    @property
    def end(self) -> NumericDescriptor:
        return self._end

    @end.setter
    def end(self, value: float):
        self._end.value = value


class ExcludedRegions(CategoryCollection):
    """Collection of ExcludedRegion instances."""

    def __init__(self):
        super().__init__(item_type=ExcludedRegion)

    def add(self, item: ExcludedRegion) -> None:
        """Mark excluded points in the pattern when a region is
        added.
        """
        # 1. Call parent add first

        super().add(item)

        # 2. Now add extra behavior specific to ExcludedRegions

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
        """Print a table of excluded [start, end] intervals."""
        # TODO: Consider moving this to the base class
        #  to avoid code duplication with implementations in Background,
        #  etc. Consider using parameter names as column headers
        columns_headers: List[str] = ['start', 'end']
        columns_alignment = ['left', 'left']
        columns_data: List[List[float]] = [[r.start.value, r.end.value] for r in self._items]

        log.paragraph('Excluded regions')
        render_table(
            columns_headers=columns_headers,
            columns_alignment=columns_alignment,
            columns_data=columns_data,
        )
