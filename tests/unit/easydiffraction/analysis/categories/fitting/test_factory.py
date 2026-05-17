# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for analysis/categories/fitting/factory.py."""


def test_fitting_factory_supported_tags():
    from easydiffraction.analysis.categories.fitting.factory import FittingFactory

    assert 'default' in FittingFactory.supported_tags()


def test_fitting_factory_default_tag():
    from easydiffraction.analysis.categories.fitting.factory import FittingFactory

    assert FittingFactory.default_tag() == 'default'


def test_fitting_factory_create():
    from easydiffraction.analysis.categories.fitting.default import Fitting
    from easydiffraction.analysis.categories.fitting.factory import FittingFactory

    fitting = FittingFactory.create('default')

    assert isinstance(fitting, Fitting)
