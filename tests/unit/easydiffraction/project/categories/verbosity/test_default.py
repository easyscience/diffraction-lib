# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import gemmi
import pytest


def test_verbosity_defaults_and_cif_output():
    from easydiffraction.project.categories.verbosity.default import Verbosity

    verbosity = Verbosity()

    assert verbosity.type_info.tag == 'default'
    assert verbosity._identity.category_code == 'verbosity'
    assert verbosity.fit.value == 'full'
    assert '_verbosity.fit full' in verbosity.as_cif


def test_verbosity_setter_validates_enum_values():
    from easydiffraction.project.categories.verbosity.default import Verbosity

    verbosity = Verbosity()

    verbosity.fit = 'short'
    assert verbosity.fit.value == 'short'

    verbosity.fit = 'silent'
    assert verbosity.fit.value == 'silent'

    with pytest.raises(ValueError, match="'verbose' is not a valid VerbosityEnum"):
        verbosity.fit = 'verbose'


def test_verbosity_from_cif_restores_fit_value():
    from easydiffraction.project.categories.verbosity.default import Verbosity

    verbosity = Verbosity()
    block = gemmi.cif.read_string('data_test\n_verbosity.fit short\n').sole_block()

    verbosity.from_cif(block)

    assert verbosity.fit.value == 'short'
