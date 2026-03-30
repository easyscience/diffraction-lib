# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import pytest

from easydiffraction.utils.enums import VerbosityEnum


def test_verbosity_enum_members():
    assert VerbosityEnum.FULL == 'full'
    assert VerbosityEnum.SHORT == 'short'
    assert VerbosityEnum.SILENT == 'silent'


def test_verbosity_enum_from_string():
    assert VerbosityEnum('full') is VerbosityEnum.FULL
    assert VerbosityEnum('short') is VerbosityEnum.SHORT
    assert VerbosityEnum('silent') is VerbosityEnum.SILENT


def test_verbosity_enum_invalid_string():
    with pytest.raises(ValueError):
        VerbosityEnum('verbose')


def test_verbosity_enum_default():
    assert VerbosityEnum.default() is VerbosityEnum.FULL
