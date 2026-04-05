# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Calculator factory — delegates to ``FactoryBase``.

Overrides ``_supported_map`` to filter out calculators whose engines are
not importable in the current environment.
"""

from __future__ import annotations

from typing import ClassVar

from easydiffraction.core.factory import FactoryBase
from easydiffraction.datablocks.experiment.item.enums import CalculatorEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum


class CalculatorFactory(FactoryBase):
    """
    Factory for creating calculation engine instances.

    Only calculators whose ``engine_imported`` flag is ``True`` are
    available for creation.
    """

    _default_rules: ClassVar[dict] = {
        frozenset({
            ('scattering_type', ScatteringTypeEnum.BRAGG),
        }): CalculatorEnum.CRYSPY,
        frozenset({
            ('scattering_type', ScatteringTypeEnum.TOTAL),
        }): CalculatorEnum.PDFFIT,
    }

    @classmethod
    def _supported_map(cls) -> dict[str, type]:
        """Only include calculators whose engines are importable."""
        return {klass.type_info.tag: klass for klass in cls._registry if klass.engine_imported}
