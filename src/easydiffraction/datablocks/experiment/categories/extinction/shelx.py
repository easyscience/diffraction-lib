# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Shelx-style isotropic extinction correction."""

from __future__ import annotations

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import Compatibility
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.variable import Parameter
from easydiffraction.datablocks.experiment.categories.extinction.factory import ExtinctionFactory
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.io.cif.handler import CifHandler


@ExtinctionFactory.register
class ShelxExtinction(CategoryItem):
    """Shelx-style extinction correction for single crystals."""

    type_info = TypeInfo(
        tag='shelx',
        description='Shelx-style isotropic extinction correction',
    )
    compatibility = Compatibility(
        sample_form=frozenset({SampleFormEnum.SINGLE_CRYSTAL}),
    )

    def __init__(self) -> None:
        super().__init__()

        self._mosaicity = Parameter(
            name='mosaicity',
            description='Mosaicity value for extinction correction',
            units='deg',
            value_spec=AttributeSpec(
                default=1.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=[
                    '_extinction.mosaicity',
                ]
            ),
        )
        self._radius = Parameter(
            name='radius',
            description='Crystal radius for extinction correction',
            units='µm',
            value_spec=AttributeSpec(
                default=1.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=[
                    '_extinction.radius',
                ]
            ),
        )

        self._identity.category_code = 'extinction'

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def mosaicity(self) -> Parameter:
        """
        Mosaicity value for extinction correction (deg).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._mosaicity

    @mosaicity.setter
    def mosaicity(self, value: float) -> None:
        self._mosaicity.value = value

    @property
    def radius(self) -> Parameter:
        """
        Crystal radius for extinction correction (µm).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._radius

    @radius.setter
    def radius(self, value: float) -> None:
        self._radius.value = value
