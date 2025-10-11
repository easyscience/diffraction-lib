# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from typing import List
from typing import Union

from numpy.polynomial.chebyshev import chebval

from easydiffraction.experiments.collections.background_types.base import BackgroundBase
from easydiffraction.experiments.collections.background_types.base import PolynomialTerm
from easydiffraction.utils.formatting import paragraph
from easydiffraction.utils.formatting import warning
from easydiffraction.utils.utils import render_table


class ChebyshevPolynomialBackground(BackgroundBase):
    _description: str = 'Chebyshev polynomial background'

    def __init__(self):
        super().__init__(item_type=PolynomialTerm)

    def calculate(self, x_data):
        """Evaluate polynomial background over x_data."""
        if not self._items:
            print(warning('No background points found. Setting background to zero.'))
            import numpy as np

            return np.zeros_like(x_data)

        u = (x_data - x_data.min()) / (x_data.max() - x_data.min()) * 2 - 1
        coefs = [term.coef.value for term in self._items]
        y_data = chebval(u, coefs)
        return y_data

    def show(self) -> None:
        columns_headers: List[str] = ['Order', 'Coefficient']
        columns_alignment = ['left', 'left']
        columns_data: List[List[Union[int, float]]] = [
            [t.order.value, t.coef.value] for t in self._items
        ]

        print(paragraph('Chebyshev polynomial background terms'))
        render_table(
            columns_headers=columns_headers,
            columns_alignment=columns_alignment,
            columns_data=columns_data,
        )
