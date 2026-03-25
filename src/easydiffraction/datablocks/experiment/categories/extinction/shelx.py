# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
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
    """Shelx-style isotropic extinction correction for single
    crystals.
    """

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
            description='Mosaicity value for extinction correction.',
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
            description='Crystal radius for extinction correction.',
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
