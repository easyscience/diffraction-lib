# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Exclude ranges of x from fitting/plotting (masked regions)."""

from __future__ import annotations

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
from easydiffraction.io.cif.handler import TagSpec
from easydiffraction.utils.logging import console
from easydiffraction.utils.utils import render_table


class ExcludedRegion(CategoryItem):
    """Closed interval [start, end] to be excluded."""

    _category_code = 'excluded_regions'
    _category_entry_name = 'id'

    def __init__(self) -> None:
        super().__init__()

        # TODO: Add id as for the background
        self._id = StringDescriptor(
            name='id',
            description='Identifier for this excluded region',
            value_spec=AttributeSpec(
                default='0',
                # TODO: the following pattern is valid for dict key
                #  (keywords are not checked). CIF label is less strict.
                #  Do we need conversion between CIF and internal label?
                validator=RegexValidator(pattern=r'^[A-Za-z0-9_]*$'),
            ),
            tags=TagSpec(
                edi_names=['_excluded_region.id'],
                cif_names=['_easydiffraction_excluded_region.id'],
            ),
        )
        self._start = NumericDescriptor(
            name='start',
            description='Start of the excluded region.',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_excluded_region.start'],
                cif_names=['_easydiffraction_excluded_region.start'],
            ),
        )
        self._end = NumericDescriptor(
            name='end',
            description='End of the excluded region.',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_excluded_region.end'],
                cif_names=['_easydiffraction_excluded_region.end'],
            ),
        )

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def id(self) -> StringDescriptor:
        """
        Identifier for this excluded region.

        Reading this property returns the underlying
        ``StringDescriptor`` object. Assigning to it updates the
        parameter value.
        """
        return self._id

    @id.setter
    def id(self, value: str) -> None:
        self._id.value = value

    @property
    def start(self) -> NumericDescriptor:
        """
        Start of the excluded region.

        Reading this property returns the underlying
        ``NumericDescriptor`` object. Assigning to it updates the
        parameter value.
        """
        return self._start

    @start.setter
    def start(self, value: float) -> None:
        self._start.value = value

    @property
    def end(self) -> NumericDescriptor:
        """
        End of the excluded region.

        Reading this property returns the underlying
        ``NumericDescriptor`` object. Assigning to it updates the
        parameter value.
        """
        return self._end

    @end.setter
    def end(self, value: float) -> None:
        self._end.value = value


@ExcludedRegionsFactory.register
class ExcludedRegions(CategoryCollection):
    """
    Collection of ExcludedRegion instances.

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

    def __init__(self) -> None:
        super().__init__(item_type=ExcludedRegion)
        # Signature of the last applied mask (point count + region
        # bounds): lets minimizer iterations skip the re-apply during a
        # fit, where the grid and region bounds are invariant.
        self._last_applied_signature: tuple | None = None

    def _update(
        self,
        *,
        called_by_minimizer: bool = False,
    ) -> None:
        data = self._parent.data

        # The included/excluded split depends only on the x-grid and the
        # region bounds, both fixed during a fit. Skip the full re-apply
        # (an unfiltered_x build plus an all-point calc_status write) on
        # minimizer iterations when neither has changed. A non-minimizer
        # update (e.g. a public calculate, a data reload, or a region
        # edit) always re-applies, so changes are never missed.
        regions_signature = tuple(
            (region.start.value, region.end.value) for region in self.values()
        )
        signature = (len(data._items), regions_signature)
        if called_by_minimizer and signature == self._last_applied_signature:
            return

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
        self._last_applied_signature = signature

    def show(self) -> None:
        """Print a table of excluded [start, end] intervals."""
        # TODO: Consider moving this to the base class
        #  to avoid code duplication with implementations in Background,
        #  etc. Consider using parameter names as column headers
        columns_headers: list[str] = ['start', 'end']
        columns_alignment = ['left', 'left']
        columns_data: list[list[float]] = [[r.start.value, r.end.value] for r in self._items]

        console.paragraph('Excluded regions')
        render_table(
            columns_headers=columns_headers,
            columns_alignment=columns_alignment,
            columns_data=columns_data,
        )
