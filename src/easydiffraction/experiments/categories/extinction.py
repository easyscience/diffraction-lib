# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Extinction correction category for single crystals."""

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.parameters import Parameter
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import DataTypes
from easydiffraction.core.validation import RangeValidator
from easydiffraction.io.cif.handler import CifHandler


class Extinction(CategoryItem):
    """Extinction correction category for single crystals."""

    def __init__(
        self,
        *,
        mosaicity=None,
        radius=None,
    ) -> None:
        super().__init__()

        self._mosaicity = Parameter(
            name='mosaicity',
            description='Mosaicity value in degrees for extinction correction.',
            value_spec=AttributeSpec(
                value=mosaicity,
                type_=DataTypes.NUMERIC,
                default=1.0,
                content_validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=[
                    '_extinction.mosaicity',
                ]
            ),
        )
        self._radius = Parameter(
            name='radius',
            description='Crystal radius in micrometers for extinction correction.',
            value_spec=AttributeSpec(
                value=radius,
                type_=DataTypes.NUMERIC,
                default=1.0,
                content_validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=[
                    '_extinction.radius',
                ]
            ),
        )

        self._identity.category_code = 'extinction'

    @property
    def mosaicity(self):
        return self._mosaicity

    @mosaicity.setter
    def mosaicity(self, value):
        self._mosaicity.value = value

    @property
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, value):
        self._radius.value = value
