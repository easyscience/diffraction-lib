# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Enumeration for ADP type values."""

from __future__ import annotations

from enum import StrEnum


class AdpTypeEnum(StrEnum):
    """Atomic displacement parameter type."""

    BISO = 'Biso'
    UISO = 'Uiso'
    BANI = 'Bani'
    UANI = 'Uani'

    @classmethod
    def default(cls) -> AdpTypeEnum:
        """Return the default ADP type (BISO)."""
        return cls.BISO

    def description(self) -> str:
        """Return a human-readable description of this ADP type."""
        descriptions = {
            AdpTypeEnum.BISO: 'Isotropic B-factor (Debye-Waller)',
            AdpTypeEnum.UISO: 'Isotropic mean-square displacement',
            AdpTypeEnum.BANI: 'Anisotropic B-factor tensor',
            AdpTypeEnum.UANI: 'Anisotropic mean-square displacement tensor',
        }
        return descriptions[self]
