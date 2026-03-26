# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Exclude ranges of x from fitting/plotting (masked regions)."""

from __future__ import annotations

from typing import List

import numpy as np

from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import Compatibility
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.validation import RegexValidator
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.datablocks.experiment.categories.excluded_regions.factory import (
    ExcludedRegionsFactory,
)
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.io.cif.handler import CifHandler
from easydiffraction.utils.logging import console
from easydiffraction.utils.utils import render_table


class ExcludedRegion(CategoryItem):
    """Closed interval [start, end] to be excluded."""

    def __init__(self):
        super().__init__()

        # TODO: Add point_id as for the background
        self._id = StringDescriptor(
            name='id',
            description='Identifier for this excluded region.',
            value_spec=AttributeSpec(
                default='0',
                # TODO: the following pattern is valid for dict key
                #  (keywords are not checked). CIF label is less strict.
                #  Do we need conversion between CIF and internal label?
                validator=RegexValidator(pattern=r'^[A-Za-z0-9_]*$'),
            ),
            cif_handler=CifHandler(names=['_excluded_region.id']),
        )
        self._start = NumericDescriptor(
            name='start',
            description='Start of the excluded region.',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_excluded_region.start']),
        )
        self._end = NumericDescriptor(
            name='end',
            description='End of the excluded region.',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_excluded_region.end']),
        )
        self._identity.category_code = 'excluded_regions'
        self._identity.category_entry_name = lambda: str(self._id.value)

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def id(self) -> StringDescriptor:
        """Identifier for this excluded region.

        Returns:
            StringDescriptor: Identifier for this excluded region.
        """
        return self._id

    @id.setter
    def id(self, value: str) -> None:
        """Set the identifier for this excluded region.

        Args:
            value (str): Identifier for this excluded region.
        """
        self._id.value = value

    @property
    def start(self) -> NumericDescriptor:
        """Start of the excluded region.

        Returns:
            NumericDescriptor: Start of the excluded region.
        """
        return self._start

    @start.setter
    def start(self, value: float) -> None:
        """Set the start of the excluded region.

        Args:
            value (float): Start of the excluded region.
        """
        self._start.value = value

    @property
    def end(self) -> NumericDescriptor:
        """End of the excluded region.

        Returns:
            NumericDescriptor: End of the excluded region.
        """
        return self._end

    @end.setter
    def end(self, value: float) -> None:
        """Set the end of the excluded region.

        Args:
            value (float): End of the excluded region.
        """
        self._end.value = value


@ExcludedRegionsFactory.register
class ExcludedRegions(CategoryCollection):
    """Collection of ExcludedRegion instances.

    Excluded regions define closed intervals [start, end] on the x-axis
    that are to be excluded from calculations and, as a result, from
    fitting and plotting.
    """

    type_info = TypeInfo(
        tag='default',
        description='Excluded x-axis regions for fitting and plotting',
    )
    compatibility = Compatibility(
        sample_form=frozenset({SampleFormEnum.POWDER}),
    )

    def __init__(self):
        super().__init__(item_type=ExcludedRegion)

    def _update(self, called_by_minimizer=False):
        del called_by_minimizer

        data = self._parent.data
        x = data.unfiltered_x

        # Start with a mask of all False (nothing excluded yet)
        combined_mask = np.full_like(x, fill_value=False, dtype=bool)

        # Combine masks for all excluded regions
        for region in self.values():
            start = region.start.value
            end = region.end.value
            region_mask = (x >= start) & (x <= end)
            combined_mask |= region_mask

        # Invert mask, as refinement status is opposite of excluded
        inverted_mask = ~combined_mask

        # Set refinement status in the data object
        data._set_calc_status(inverted_mask)

    def show(self) -> None:
        """Print a table of excluded [start, end] intervals."""
        # TODO: Consider moving this to the base class
        #  to avoid code duplication with implementations in Background,
        #  etc. Consider using parameter names as column headers
        columns_headers: List[str] = ['start', 'end']
        columns_alignment = ['left', 'left']
        columns_data: List[List[float]] = [[r.start.value, r.end.value] for r in self._items]

        console.paragraph('Excluded regions')
        render_table(
            columns_headers=columns_headers,
            columns_alignment=columns_alignment,
            columns_data=columns_data,
        )
