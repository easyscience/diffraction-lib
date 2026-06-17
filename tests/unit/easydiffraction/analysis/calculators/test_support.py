# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for the calculator support matrix."""

from __future__ import annotations


def test_matrix_covers_every_registered_instrument():
    from easydiffraction.analysis.calculators.support import calculator_support_matrix
    from easydiffraction.datablocks.experiment.categories.instrument.factory import (
        InstrumentFactory,
    )

    entries = calculator_support_matrix()

    assert entries
    assert {e.instrument_tag for e in entries} == set(InstrumentFactory.supported_tags())


def test_matrix_entries_are_well_typed():
    from easydiffraction.analysis.calculators.support import calculator_support_matrix
    from easydiffraction.core.metadata import Compatibility
    from easydiffraction.datablocks.experiment.item.enums import CalculatorEnum

    for entry in calculator_support_matrix():
        assert isinstance(entry.compatibility, Compatibility)
        assert all(isinstance(c, CalculatorEnum) for c in entry.calculators)


def test_cwl_pd_bragg_instruments_support_bragg_engines_only():
    from easydiffraction.analysis.calculators.support import calculator_support_matrix
    from easydiffraction.datablocks.experiment.item.enums import CalculatorEnum

    by_tag = {e.instrument_tag: e for e in calculator_support_matrix()}

    expected = frozenset({CalculatorEnum.CRYSPY, CalculatorEnum.CRYSFML})
    assert by_tag['cwl-pd-neutron'].calculators == expected
    assert by_tag['cwl-pd-xray'].calculators == expected


def test_cwl_sc_supports_cryspy_only():
    from easydiffraction.analysis.calculators.support import calculator_support_matrix
    from easydiffraction.datablocks.experiment.item.enums import CalculatorEnum

    by_tag = {e.instrument_tag: e for e in calculator_support_matrix()}

    assert by_tag['cwl-sc'].calculators == frozenset({CalculatorEnum.CRYSPY})
