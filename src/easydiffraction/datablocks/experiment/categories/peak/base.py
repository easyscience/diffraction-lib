# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Base class for peak profile categories."""

from __future__ import annotations

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import CifHandler


class PeakBase(CategoryItem):
    """Base class for peak profile categories."""

    def __init__(self) -> None:
        super().__init__()
        self._identity.category_code = 'peak'

        type_info = getattr(type(self), 'type_info', None)
        default_tag = type_info.tag if type_info is not None else ''
        self._profile_type: StringDescriptor = StringDescriptor(
            name='profile_type',
            description='Active peak profile type tag',
            value_spec=AttributeSpec(default=default_tag),
            cif_handler=CifHandler(names=['_peak.profile_type']),
        )

    @property
    def profile_type(self) -> StringDescriptor:
        """
        CIF identifier for the active peak profile type.

        Returns
        -------
        StringDescriptor
            The descriptor holding the profile type tag string.
        """
        return self._profile_type
