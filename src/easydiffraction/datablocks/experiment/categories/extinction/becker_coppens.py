# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Becker-Coppens isotropic extinction correction for single crystals.
"""

from __future__ import annotations

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import CalculatorSupport
from easydiffraction.core.metadata import Compatibility
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import MembershipValidator
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.variable import Parameter
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.datablocks.experiment.categories.extinction.factory import ExtinctionFactory
from easydiffraction.datablocks.experiment.item.enums import CalculatorEnum
from easydiffraction.datablocks.experiment.item.enums import ExtinctionModelEnum
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.io.cif.handler import CifHandler


@ExtinctionFactory.register
class BeckerCoppensExtinction(CategoryItem):
    """
    Becker-Coppens spherical extinction correction for single crystals.

    Combines primary and secondary extinction into a single correction
    factor ``y = y_p * y_s``, following the Becker-Coppens formalism.
    The mosaicity distribution for the secondary extinction can be
    either Gaussian (``'gauss'``) or Lorentzian (``'lorentz'``).

    Parameters are the crystal ``radius`` (in μm) and the ``mosaicity``
    (in arc-minutes, as expected by CrysPy).
    """

    type_info = TypeInfo(
        tag='becker-coppens',
        description='Becker-Coppens isotropic extinction correction',
    )
    compatibility = Compatibility(
        sample_form=frozenset({SampleFormEnum.SINGLE_CRYSTAL}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY}),
    )

    def __init__(self) -> None:
        super().__init__()

        self._model = StringDescriptor(
            name='model',
            description='Mosaicity distribution model (gauss or lorentz)',
            value_spec=AttributeSpec(
                default=ExtinctionModelEnum.default().value,
                validator=MembershipValidator(
                    allowed=[member.value for member in ExtinctionModelEnum],
                ),
            ),
            cif_handler=CifHandler(names=['_extinction.model']),
        )

        self._mosaicity = Parameter(
            name='mosaicity',
            description='Mosaicity of the crystal',
            units='arcmin',
            value_spec=AttributeSpec(
                default=1.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_extinction.mosaicity']),
        )
        self._radius = Parameter(
            name='radius',
            description='Mean radius of the crystal',
            units='μm',
            value_spec=AttributeSpec(
                default=1.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_extinction.radius']),
        )

        self._identity.category_code = 'extinction'

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def model(self) -> StringDescriptor:
        """
        Mosaicity distribution model (``'gauss'`` or ``'lorentz'``).

        Reading this property returns the underlying
        ``StringDescriptor`` object. Assigning to it updates the
        descriptor value.
        """
        return self._model

    @model.setter
    def model(self, value: str) -> None:
        self._model.value = value

    @property
    def mosaicity(self) -> Parameter:
        """
        Mosaicity of the crystal (arcmin).

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
        Mean radius of the crystal (μm).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._radius

    @radius.setter
    def radius(self, value: float) -> None:
        self._radius.value = value
