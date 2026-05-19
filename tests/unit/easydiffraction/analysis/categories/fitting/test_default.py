# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for analysis/categories/fitting/default.py."""

from types import SimpleNamespace


def test_fitting_defaults():
    from easydiffraction.analysis.categories.fitting.default import Fitting

    fitting = Fitting()

    assert fitting.minimizer_type.value == 'lmfit (leastsq)'
    assert fitting._identity.category_code == 'fitting'
    assert Fitting.type_info.tag == 'default'


def test_fitting_setter_updates_parent_fitter():
    from easydiffraction.analysis.categories.fitting.default import Fitting

    fitting = Fitting()
    parent = SimpleNamespace(fitter=None)
    fitting._parent = parent

    fitting.minimizer_type = 'lmfit'

    assert fitting.minimizer_type.value == 'lmfit'
    assert parent.fitter is not None


def test_fitting_as_cif_uses_fitting_prefix():
    from easydiffraction.analysis.categories.fitting.default import Fitting

    fitting = Fitting()
    fitting.minimizer_type = 'lmfit'

    assert '_fitting.minimizer_type' in fitting.as_cif
