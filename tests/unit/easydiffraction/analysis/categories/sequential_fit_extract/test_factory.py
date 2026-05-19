# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for analysis/categories/sequential_fit_extract/factory.py."""


def test_sequential_fit_extract_factory_supported_tags():
    from easydiffraction.analysis.categories.sequential_fit_extract.factory import (
        SequentialFitExtractFactory,
    )

    assert 'default' in SequentialFitExtractFactory.supported_tags()


def test_sequential_fit_extract_factory_default_tag():
    from easydiffraction.analysis.categories.sequential_fit_extract.factory import (
        SequentialFitExtractFactory,
    )

    assert SequentialFitExtractFactory.default_tag() == 'default'


def test_sequential_fit_extract_factory_create():
    from easydiffraction.analysis.categories.sequential_fit_extract.default import (
        SequentialFitExtractCollection,
    )
    from easydiffraction.analysis.categories.sequential_fit_extract.factory import (
        SequentialFitExtractFactory,
    )

    collection = SequentialFitExtractFactory.create('default')

    assert isinstance(collection, SequentialFitExtractCollection)
