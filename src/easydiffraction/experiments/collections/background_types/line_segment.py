# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from typing import List

from scipy.interpolate import interp1d

from easydiffraction.experiments.collections.background_types.base import BackgroundBase
from easydiffraction.experiments.collections.background_types.base import Point
from easydiffraction.utils.formatting import paragraph
from easydiffraction.utils.formatting import warning
from easydiffraction.utils.utils import render_table


class LineSegmentBackground(BackgroundBase):
    _description: str = 'Linear interpolation between points'

    def __init__(self):
        super().__init__(item_type=Point)

    def calculate(self, x_data):
        """Interpolate background points over x_data."""
        if not self:
            print(warning('No background points found. Setting background to zero.'))
            # Lazy import to avoid global numpy import in base module
            import numpy as np

            return np.zeros_like(x_data)

        import numpy as np

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
        columns_headers: List[str] = ['X', 'Intensity']
        columns_alignment = ['left', 'left']
        columns_data: List[List[float]] = [[p.x.value, p.y.value] for p in self._items]

        print(paragraph('Line-segment background points'))
        render_table(
            columns_headers=columns_headers,
            columns_alignment=columns_alignment,
            columns_data=columns_data,
        )
