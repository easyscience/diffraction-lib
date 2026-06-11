# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Per-phase March-Dollase preferred-orientation corrections."""

from __future__ import annotations

from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.display_handler import DisplayHandler
from easydiffraction.core.metadata import CalculatorSupport
from easydiffraction.core.metadata import Compatibility
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.validation import RegexValidator
from easydiffraction.core.variable import IntegerDescriptor
from easydiffraction.core.variable import Parameter
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.datablocks.experiment.categories.pref_orient.factory import (
    PrefOrientFactory,
)
from easydiffraction.datablocks.experiment.item.enums import CalculatorEnum
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
from easydiffraction.io.cif.handler import CifHandler


class PrefOrient(CategoryItem):
    """March-Dollase preferred-orientation correction for one phase."""

    _category_code = 'pref_orient'
    _category_entry_name = 'phase_id'

    def __init__(self) -> None:
        super().__init__()

        self._phase_id = StringDescriptor(
            name='phase_id',
            description='Identifier of the corrected phase',
            value_spec=AttributeSpec(
                default='Si',
                validator=RegexValidator(pattern=r'^[A-Za-z_][A-Za-z0-9_]*$'),
            ),
            cif_handler=CifHandler(
                names=['_pref_orient.phase_id'],
                iucr_name='_pd_pref_orient_March_Dollase.phase_id',
            ),
            display_handler=DisplayHandler(
                display_name='Phase',
                latex_name='Phase',
            ),
        )
        self._r = Parameter(
            name='r',
            description='March coefficient (1 = no preferred orientation).',
            value_spec=AttributeSpec(
                default=1.0,
                validator=RangeValidator(gt=0.0),
            ),
            cif_handler=CifHandler(
                names=['_pref_orient.r'],
                iucr_name='_pd_pref_orient_March_Dollase.r',
            ),
            display_handler=DisplayHandler(
                display_name='March coefficient',
                latex_name='r',
            ),
        )
        self._h = IntegerDescriptor(
            name='h',
            description='Texture-axis Miller index h',
            value_spec=AttributeSpec(default=0),
            cif_handler=CifHandler(
                names=['_pref_orient.index_h'],
                iucr_name='_pd_pref_orient_March_Dollase.index_h',
            ),
            display_handler=DisplayHandler(
                display_name='h',
                latex_name='h',
            ),
        )
        self._k = IntegerDescriptor(
            name='k',
            description='Texture-axis Miller index k',
            value_spec=AttributeSpec(default=0),
            cif_handler=CifHandler(
                names=['_pref_orient.index_k'],
                iucr_name='_pd_pref_orient_March_Dollase.index_k',
            ),
            display_handler=DisplayHandler(
                display_name='k',
                latex_name='k',
            ),
        )
        self._l = IntegerDescriptor(
            name='l',
            description='Texture-axis Miller index l',
            value_spec=AttributeSpec(default=1),
            cif_handler=CifHandler(
                names=['_pref_orient.index_l'],
                iucr_name='_pd_pref_orient_March_Dollase.index_l',
            ),
            display_handler=DisplayHandler(
                display_name='l',
                latex_name='l',
            ),
        )
        self._fraction = Parameter(
            name='fraction',
            description='Random (untextured) fraction; 0 = pure March-Dollase.',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0.0, le=1.0),
            ),
            cif_handler=CifHandler(
                names=['_pref_orient.fraction'],
                iucr_name='_easydiffraction_pref_orient.fraction',
            ),
            display_handler=DisplayHandler(
                display_name='Random fraction',
                latex_name='fraction',
            ),
        )

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def phase_id(self) -> StringDescriptor:
        """Identifier of the corrected phase."""
        return self._phase_id

    @phase_id.setter
    def phase_id(self, value: str) -> None:
        self._phase_id.value = value

    @property
    def r(self) -> Parameter:
        """March coefficient (1 = no preferred orientation)."""
        return self._r

    @r.setter
    def r(self, value: float) -> None:
        self._r.value = value

    @property
    def h(self) -> IntegerDescriptor:
        """Texture-axis Miller index h."""
        return self._h

    @h.setter
    def h(self, value: int) -> None:
        self._h.value = value

    @property
    def k(self) -> IntegerDescriptor:
        """Texture-axis Miller index k."""
        return self._k

    @k.setter
    def k(self, value: int) -> None:
        self._k.value = value

    @property
    def l(self) -> IntegerDescriptor:  # noqa: E743
        """Texture-axis Miller index l."""
        return self._l

    @l.setter
    def l(self, value: int) -> None:  # noqa: E743
        self._l.value = value

    @property
    def fraction(self) -> Parameter:
        """Random (untextured) fraction; 0 = pure March-Dollase."""
        return self._fraction

    @fraction.setter
    def fraction(self, value: float) -> None:
        self._fraction.value = value


@PrefOrientFactory.register
class PrefOrients(CategoryCollection):
    """Collection of per-phase preferred-orientation corrections."""

    type_info = TypeInfo(
        tag='default',
        description='Per-phase March-Dollase preferred orientation',
    )
    compatibility = Compatibility(
        sample_form=frozenset({SampleFormEnum.POWDER}),
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY}),
    )

    def __init__(self) -> None:
        """Create an empty collection of preferred-orientation rows."""
        super().__init__(item_type=PrefOrient)
