# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for analysis/categories/sequential_fit_extract/default.py."""

import pytest


def test_sequential_fit_extract_item_defaults():
    from easydiffraction.analysis.categories.sequential_fit_extract.default import (
        SequentialFitExtractItem,
    )

    item = SequentialFitExtractItem()

    assert item.id.value == '_'
    assert item.target.value == 'diffrn._'
    assert item.pattern.value == '(.*)'
    assert item.required.value is False


def test_sequential_fit_extract_collection_create():
    from easydiffraction.analysis.categories.sequential_fit_extract.default import (
        SequentialFitExtractCollection,
    )

    collection = SequentialFitExtractCollection()
    collection.create(
        id='temperature',
        target='diffrn.ambient_temperature',
        pattern=r'temp_(\d+)',
        required=True,
    )

    assert collection.names == ['temperature']
    assert collection['temperature'].target.value == 'diffrn.ambient_temperature'
    assert collection['temperature'].required.value is True


def test_sequential_fit_extract_collection_rejects_invalid_target():
    from easydiffraction.analysis.categories.sequential_fit_extract.default import (
        SequentialFitExtractCollection,
    )

    collection = SequentialFitExtractCollection()

    with pytest.raises(ValueError, match='must use the form'):
        collection.create(
            id='temperature',
            target='experiment.ambient_temperature',
            pattern=r'temp_(\d+)',
        )


def test_sequential_fit_extract_collection_rejects_invalid_pattern():
    from easydiffraction.analysis.categories.sequential_fit_extract.default import (
        SequentialFitExtractCollection,
    )

    collection = SequentialFitExtractCollection()

    with pytest.raises(ValueError, match='must define exactly one capture group'):
        collection.create(
            id='temperature',
            target='diffrn.ambient_temperature',
            pattern=r'temp_\d+',
        )
