# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for analysis/categories/sequential_fit/factory.py."""


def test_sequential_fit_factory_supported_tags():
    from easydiffraction.analysis.categories.sequential_fit.factory import SequentialFitFactory

    assert 'default' in SequentialFitFactory.supported_tags()


def test_sequential_fit_factory_default_tag():
    from easydiffraction.analysis.categories.sequential_fit.factory import SequentialFitFactory

    assert SequentialFitFactory.default_tag() == 'default'


def test_sequential_fit_factory_create():
    from easydiffraction.analysis.categories.sequential_fit.default import SequentialFit
    from easydiffraction.analysis.categories.sequential_fit.factory import SequentialFitFactory

    sequential_fit = SequentialFitFactory.create('default')

    assert isinstance(sequential_fit, SequentialFit)
