# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Base class for sample-absorption correction categories."""

from __future__ import annotations

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.switchable import SwitchableCategoryBase
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import MembershipValidator
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.datablocks.experiment.categories.absorption.factory import AbsorptionFactory
from easydiffraction.datablocks.experiment.item.enums import AbsorptionTypeEnum
from easydiffraction.io.cif.handler import CifHandler


class AbsorptionBase(CategoryItem, SwitchableCategoryBase):
    """Base class for sample-absorption correction categories."""

    _category_code = 'absorption'
    _owner_attr_name = 'absorption'
    _swap_method_name = '_swap_absorption'

    def __init__(self) -> None:
        super().__init__()

        type_info = getattr(type(self), 'type_info', None)
        default_tag = type_info.tag if type_info is not None else ''
        self._type: StringDescriptor = StringDescriptor(
            name='type',
            description='Active absorption type tag',
            value_spec=AttributeSpec(
                default=default_tag,
                validator=MembershipValidator(
                    allowed=[member.value for member in AbsorptionTypeEnum],
                ),
            ),
            cif_handler=CifHandler(
                names=['_absorption.type'],
                iucr_name='_easydiffraction_absorption.type',
            ),
        )

    @staticmethod
    def _supported_types(
        filters: dict[str, object],
    ) -> list[tuple[str, str]]:
        """Return absorption types supported for owner filters."""
        return [
            (klass.type_info.tag, klass.type_info.description)
            for klass in AbsorptionFactory.supported_for(
                calculator=filters.get('calculator'),
                sample_form=filters.get('sample_form'),
                scattering_type=filters.get('scattering_type'),
                beam_mode=filters.get('beam_mode'),
                radiation_probe=filters.get('radiation_probe'),
            )
        ]

    def from_cif(self, block: object, idx: int = 0) -> None:
        """
        Populate parameters from CIF, skipping the active-type selector.

        ``_absorption.type`` is restored with owner-context validation
        by ``_restore_switchable_types`` before parameters are loaded.
        Re-loading it through the generic descriptor path would set the
        public ``type`` selector even when the persisted tag was
        rejected for the experiment context (for example a CWL-only
        ``cylinder-hewat`` tag in a time-of-flight file), leaving the
        live category and its selector inconsistent. The type descriptor
        is therefore intentionally skipped here.

        Parameters
        ----------
        block : object
            Parsed CIF block to read parameter values from.
        idx : int, default=0
            Loop index for the parameter values.
        """
        for param in self.parameters:
            if param is self._type:
                continue
            param.from_cif(block, idx=idx)
