# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Calculator support matrix.

Aggregates the per-instrument ``Compatibility`` and
``CalculatorSupport`` metadata declared on the registered instrument
categories into a single queryable matrix: which calculation engines can
compute which experiment conditions. Used by the Verification
documentation to enumerate comparable engine x condition combinations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

# Importing the instrument package registers every concrete instrument
# category, so the support matrix below is complete regardless of import
# order.
import easydiffraction.datablocks.experiment.categories.instrument  # noqa: F401
from easydiffraction.datablocks.experiment.categories.instrument.factory import InstrumentFactory

if TYPE_CHECKING:
    from easydiffraction.core.metadata import Compatibility


@dataclass(frozen=True)
class SupportEntry:
    """
    One instrument condition and the engines that can compute it.

    Attributes
    ----------
    instrument_tag : str
        The instrument category tag (for example ``'cwl-pd'``).
    description : str
        One-line human-readable description of the instrument.
    compatibility : Compatibility
        The experimental conditions (sample_form x scattering_type x
        beam_mode x radiation_probe) the instrument supports.
    calculators : frozenset
        The ``CalculatorEnum`` engines declared able to handle it.
    """

    instrument_tag: str
    description: str
    compatibility: Compatibility
    calculators: frozenset


def calculator_support_matrix() -> list[SupportEntry]:
    """
    Return the engine x experiment-condition support matrix.

    One entry per registered instrument category, pairing its
    ``Compatibility`` with the calculators declared able to handle it.

    Returns
    -------
    list[SupportEntry]
        One entry per registered instrument category.
    """
    return [
        SupportEntry(
            instrument_tag=klass.type_info.tag,
            description=klass.type_info.description,
            compatibility=klass.compatibility,
            calculators=frozenset(klass.calculator_support.calculators),
        )
        for klass in InstrumentFactory._supported_map().values()
    ]
