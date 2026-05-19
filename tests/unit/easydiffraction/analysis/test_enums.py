# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for analysis/enums.py."""

from easydiffraction.analysis.enums import FitCorrelationSourceEnum
from easydiffraction.analysis.enums import FitResultKindEnum
from easydiffraction.analysis.enums import FitModeEnum


def test_fit_mode_enum_members():
    assert FitModeEnum.SINGLE == 'single'
    assert FitModeEnum.JOINT == 'joint'
    assert FitModeEnum.SEQUENTIAL == 'sequential'


def test_fit_mode_enum_default():
    assert FitModeEnum.default() is FitModeEnum.SINGLE


def test_fit_mode_enum_descriptions():
    for member in FitModeEnum:
        description = member.description()
        assert isinstance(description, str)
        assert description


def test_fit_result_kind_enum_members_and_default():
    assert FitResultKindEnum.DETERMINISTIC == 'deterministic'
    assert FitResultKindEnum.BAYESIAN == 'bayesian'
    assert FitResultKindEnum.default() is FitResultKindEnum.DETERMINISTIC


def test_fit_correlation_source_enum_members_and_default():
    assert FitCorrelationSourceEnum.DETERMINISTIC == 'deterministic'
    assert FitCorrelationSourceEnum.POSTERIOR == 'posterior'
    assert FitCorrelationSourceEnum.default() is FitCorrelationSourceEnum.DETERMINISTIC
