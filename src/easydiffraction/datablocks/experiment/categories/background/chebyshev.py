# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Chebyshev polynomial background model.

Provides a collection of polynomial terms and evaluation helpers.
"""

from __future__ import annotations

import numpy as np
from numpy.polynomial.chebyshev import chebval

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import CalculatorSupport
from easydiffraction.core.metadata import Compatibility
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.validation import RegexValidator
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.core.variable import Parameter
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.datablocks.experiment.categories.background.base import BackgroundBase
from easydiffraction.datablocks.experiment.categories.background.factory import BackgroundFactory
from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import CalculatorEnum
from easydiffraction.io.cif.handler import TagSpec
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log
from easydiffraction.utils.utils import render_table


class PolynomialTerm(CategoryItem):
    """
    Chebyshev polynomial term.

    New public attribute names: ``order`` and ``coef`` replacing the
    longer ``chebyshev_order`` / ``chebyshev_coef``. Backward-compatible
    aliases are kept so existing serialized data / external code does
    not break immediately. Tests should migrate to the short names.
    """

    _category_code = 'background'
    _category_entry_name = 'id'

    def __init__(self) -> None:
        super().__init__()

        self._id = StringDescriptor(
            name='id',
            description='Identifier for this background polynomial term',
            value_spec=AttributeSpec(
                default='0',
                # TODO: the following pattern is valid for dict key
                #  (keywords are not checked). CIF label is less strict.
                #  Do we need conversion between CIF and internal label?
                validator=RegexValidator(pattern=r'^[A-Za-z0-9_]*$'),
            ),
            tags=TagSpec(edi_names=['_background.id'], cif_names=['_pd_background.id']),
        )
        self._order = NumericDescriptor(
            name='order',
            description='Order used in a Chebyshev polynomial background term',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_background.order'], cif_names=['_pd_background.Chebyshev_order']
            ),
        )
        self._coef = Parameter(
            name='coef',
            description='Coefficient used in a Chebyshev polynomial background term',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_background.coef'], cif_names=['_pd_background.Chebyshev_coef']
            ),
        )

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def id(self) -> StringDescriptor:
        """
        Identifier for this background polynomial term.

        Reading this property returns the underlying
        ``StringDescriptor`` object. Assigning to it updates the
        parameter value.
        """
        return self._id

    @id.setter
    def id(self, value: str) -> None:
        self._id.value = value

    @property
    def order(self) -> NumericDescriptor:
        """
        Order used in a Chebyshev polynomial background term.

        Reading this property returns the underlying
        ``NumericDescriptor`` object. Assigning to it updates the
        parameter value.
        """
        return self._order

    @order.setter
    def order(self, value: float) -> None:
        self._order.value = value

    @property
    def coef(self) -> Parameter:
        """
        Coefficient used in a Chebyshev polynomial background term.

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._coef

    @coef.setter
    def coef(self, value: float) -> None:
        self._coef.value = value


@BackgroundFactory.register
class ChebyshevPolynomialBackground(BackgroundBase):
    """Chebyshev polynomial background model."""

    type_info = TypeInfo(
        tag='chebyshev',
        description='Chebyshev polynomial background',
    )
    compatibility = Compatibility(
        beam_mode=frozenset({
            BeamModeEnum.CONSTANT_WAVELENGTH,
            BeamModeEnum.TIME_OF_FLIGHT,
        }),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY, CalculatorEnum.CRYSFML}),
    )

    def __init__(self) -> None:
        super().__init__(item_type=PolynomialTerm)

    def _update(
        self,
        *,
        called_by_minimizer: bool = False,
    ) -> None:
        """Evaluate polynomial background over x data."""
        del called_by_minimizer

        data = self._parent.data
        x = data.x

        if not self._items:
            log.warning('No background points found. Setting background to zero.')
            data._set_intensity_bkg(np.zeros_like(x))
            return

        u = (x - x.min()) / (x.max() - x.min()) * 2 - 1
        coefs = [term.coef.value for term in self._items]

        y = chebval(u, coefs)
        data._set_intensity_bkg(y)

    def show(self) -> None:
        """Print a table of polynomial orders and coefficients."""
        columns_headers: list[str] = ['Order', 'Coefficient']
        columns_alignment = ['left', 'left']
        columns_data: list[list[int | float]] = [
            [t.order.value, t.coef.value] for t in self._items
        ]

        console.paragraph('Chebyshev polynomial background terms')
        render_table(
            columns_headers=columns_headers,
            columns_alignment=columns_alignment,
            columns_data=columns_data,
        )
