# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Chebyshev polynomial background model.

Provides a collection of polynomial terms and evaluation helpers.
"""

from __future__ import annotations

from typing import List
from typing import Union

import numpy as np
from numpy.polynomial.chebyshev import chebval

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


class PolynomialTerm(CategoryItem):
    """Chebyshev polynomial term.

    New public attribute names: ``order`` and ``coef`` replacing the
    longer ``chebyshev_order`` / ``chebyshev_coef``. Backward-compatible
    aliases are kept so existing serialized data / external code does
    not break immediately. Tests should migrate to the short names.
    """

    def __init__(self, *, order: int, coef: float) -> None:
        super().__init__()

        # Canonical descriptors
        self._order = NumericDescriptor(
            name='order',
            description='Order used in a Chebyshev polynomial background term',
            value_spec=AttributeSpec(
                value=order,
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_pd_background.Chebyshev_order']),
        )
        self._coef = Parameter(
            name='coef',
            description='Coefficient used in a Chebyshev polynomial background term',
            value_spec=AttributeSpec(
                value=coef,
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_pd_background.Chebyshev_coef']),
        )

        self._identity.category_code = 'background'
        self._identity.category_entry_name = lambda: str(self.order.value)

    @property
    def order(self):
        return self._order

    @order.setter
    def order(self, value):
        self._order.value = value

    @property
    def coef(self):
        return self._coef

    @coef.setter
    def coef(self, value):
        self._coef.value = value


class ChebyshevPolynomialBackground(BackgroundBase):
    _description: str = 'Chebyshev polynomial background'

    def __init__(self):
        super().__init__(item_type=PolynomialTerm)

    def calculate(self, x_data):
        """Evaluate polynomial background over x_data."""
        if not self._items:
            log.warning('No background points found. Setting background to zero.')
            return np.zeros_like(x_data)

        u = (x_data - x_data.min()) / (x_data.max() - x_data.min()) * 2 - 1
        coefs = [term.coef.value for term in self._items]
        y_data = chebval(u, coefs)
        return y_data

    def show(self) -> None:
        """Print a table of polynomial orders and coefficients."""
        columns_headers: List[str] = ['Order', 'Coefficient']
        columns_alignment = ['left', 'left']
        columns_data: List[List[Union[int, float]]] = [
            [t.order.value, t.coef.value] for t in self._items
        ]

        console.paragraph('Chebyshev polynomial background terms')
        render_table(
            columns_headers=columns_headers,
            columns_alignment=columns_alignment,
            columns_data=columns_data,
        )
