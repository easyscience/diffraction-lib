# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for analysis/enums.py."""

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
