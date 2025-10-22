# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Line-segment background model.

Interpolate user-specified points to form a background curve.
"""

from __future__ import annotations

from typing import List

import numpy as np
from scipy.interpolate import interp1d

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.parameters import NumericDescriptor
from easydiffraction.core.parameters import Parameter
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import DataTypes
from easydiffraction.core.validation import RangeValidator
from easydiffraction.experiments.categories.background.base import BackgroundBase
from easydiffraction.io.cif.handler import CifHandler
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log
from easydiffraction.utils.utils import render_table


class LineSegment(CategoryItem):
    """Single background control point for interpolation."""

    def __init__(self, *, x: float, y: float):
        super().__init__()

        self._x = NumericDescriptor(
            name='x',
            description=(
                'X-coordinates used to create many straight-line segments '
                'representing the background in a calculated diffractogram.'
            ),
            value_spec=AttributeSpec(
                value=x,
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_pd_background.line_segment_X']),
        )
        self._y = Parameter(
            name='y',  # TODO: rename to intensity
            description=(
                'Intensity used to create many straight-line segments '
                'representing the background in a calculated diffractogram'
            ),
            value_spec=AttributeSpec(
                value=y,
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),  # TODO: rename to intensity
            cif_handler=CifHandler(names=['_pd_background.line_segment_intensity']),
        )

        self._identity.category_code = 'background'
        self._identity.category_entry_name = lambda: str(self.x.value)

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x.value = value

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y.value = value


class LineSegmentBackground(BackgroundBase):
    _description: str = 'Linear interpolation between points'

    def __init__(self):
        super().__init__(item_type=LineSegment)

    def calculate(self, x_data):
        """Interpolate background points over x_data."""
        if not self:
            log.warning('No background points found. Setting background to zero.')
            return np.zeros_like(x_data)

        background_x = np.array([point.x.value for point in self.values()])
        background_y = np.array([point.y.value for point in self.values()])
        interp_func = interp1d(
            background_x,
            background_y,
            kind='linear',
            bounds_error=False,
            fill_value=(background_y[0], background_y[-1]),
        )
        y_data = interp_func(x_data)
        return y_data

    def show(self) -> None:
        """Print a table of control points (x, intensity)."""
        columns_headers: List[str] = ['X', 'Intensity']
        columns_alignment = ['left', 'left']
        columns_data: List[List[float]] = [[p.x.value, p.y.value] for p in self._items]

        console.paragraph('Line-segment background points')
        render_table(
            columns_headers=columns_headers,
            columns_alignment=columns_alignment,
            columns_data=columns_data,
        )
