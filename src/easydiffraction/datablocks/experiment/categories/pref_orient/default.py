# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Per-structure March-Dollase preferred-orientation corrections."""

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
from easydiffraction.datablocks.experiment.categories.pref_orient.factory import PrefOrientFactory
from easydiffraction.datablocks.experiment.item.enums import CalculatorEnum
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
from easydiffraction.io.cif.handler import CifHandler


class PrefOrient(CategoryItem):
    """March-Dollase preferred-orientation correction for one structure."""

    _category_code = 'preferred_orientation'
    _category_entry_name = 'structure_id'

    def __init__(self) -> None:
        super().__init__()

        self._structure_id = StringDescriptor(
            name='structure_id',
            description='Identifier of the corrected structure',
            value_spec=AttributeSpec(
                default='Si',
                validator=RegexValidator(pattern=r'^[A-Za-z_][A-Za-z0-9_]*$'),
            ),
            cif_handler=CifHandler(
                names=['_preferred_orientation.structure_id'],
                import_names=['_pref_orient.phase_id'],
                iucr_name='_pd_pref_orient_March_Dollase.phase_id',
            ),
            display_handler=DisplayHandler(
                display_name='Structure',
                latex_name='Structure',
            ),
        )
        self._march_r = Parameter(
            name='march_r',
            description='March coefficient (1 = no preferred orientation).',
            value_spec=AttributeSpec(
                default=1.0,
                validator=RangeValidator(gt=0.0),
            ),
            cif_handler=CifHandler(
                names=['_preferred_orientation.march_r'],
                import_names=['_pref_orient.march_r'],
                iucr_name='_pd_pref_orient_March_Dollase.r',
            ),
            display_handler=DisplayHandler(
                display_name='March coefficient',
                latex_name='r',
            ),
        )
        self._index_h = IntegerDescriptor(
            name='index_h',
            description='Texture-axis Miller index h',
            value_spec=AttributeSpec(default=0),
            cif_handler=CifHandler(
                names=['_preferred_orientation.index_h'],
                import_names=['_pref_orient.index_h'],
                iucr_name='_pd_pref_orient_March_Dollase.index_h',
            ),
            display_handler=DisplayHandler(
                display_name='h',
                latex_name='h',
            ),
        )
        self._index_k = IntegerDescriptor(
            name='index_k',
            description='Texture-axis Miller index k',
            value_spec=AttributeSpec(default=0),
            cif_handler=CifHandler(
                names=['_preferred_orientation.index_k'],
                import_names=['_pref_orient.index_k'],
                iucr_name='_pd_pref_orient_March_Dollase.index_k',
            ),
            display_handler=DisplayHandler(
                display_name='k',
                latex_name='k',
            ),
        )
        self._index_l = IntegerDescriptor(
            name='index_l',
            description='Texture-axis Miller index l',
            value_spec=AttributeSpec(default=1),
            cif_handler=CifHandler(
                names=['_preferred_orientation.index_l'],
                import_names=['_pref_orient.index_l'],
                iucr_name='_pd_pref_orient_March_Dollase.index_l',
            ),
            display_handler=DisplayHandler(
                display_name='l',
                latex_name='l',
            ),
        )
        self._march_random_fract = Parameter(
            name='march_random_fract',
            description='Random (untextured) fraction; 0 = pure March-Dollase.',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0.0, le=1.0),
            ),
            cif_handler=CifHandler(
                names=['_preferred_orientation.march_random_fract'],
                import_names=['_pref_orient.march_random_fract'],
                iucr_name='_easydiffraction_pref_orient.march_random_fract',
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
    def structure_id(self) -> StringDescriptor:
        """Identifier of the corrected structure."""
        return self._structure_id

    @structure_id.setter
    def structure_id(self, value: str) -> None:
        self._structure_id.value = value

    @property
    def march_r(self) -> Parameter:
        """March coefficient (1 = no preferred orientation)."""
        return self._march_r

    @march_r.setter
    def march_r(self, value: float) -> None:
        self._march_r.value = value

    # Miller indices use the ``index_h``/``index_k``/``index_l`` names
    # already established by the ``refln`` categories. This also avoids
    # a bare ambiguous ``l`` name (ruff E741/E743).

    @property
    def index_h(self) -> IntegerDescriptor:
        """Texture-axis Miller index h."""
        return self._index_h

    @index_h.setter
    def index_h(self, value: int) -> None:
        self._index_h.value = value

    @property
    def index_k(self) -> IntegerDescriptor:
        """Texture-axis Miller index k."""
        return self._index_k

    @index_k.setter
    def index_k(self, value: int) -> None:
        self._index_k.value = value

    @property
    def index_l(self) -> IntegerDescriptor:
        """Texture-axis Miller index l."""
        return self._index_l

    @index_l.setter
    def index_l(self, value: int) -> None:
        self._index_l.value = value

    @property
    def march_random_fract(self) -> Parameter:
        """Random (untextured) fraction; 0 = pure March-Dollase."""
        return self._march_random_fract

    @march_random_fract.setter
    def march_random_fract(self, value: float) -> None:
        self._march_random_fract.value = value


@PrefOrientFactory.register
class PrefOrients(CategoryCollection):
    """Collection of per-structure preferred-orientation corrections."""

    type_info = TypeInfo(
        tag='default',
        description='Per-structure March-Dollase preferred orientation',
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
