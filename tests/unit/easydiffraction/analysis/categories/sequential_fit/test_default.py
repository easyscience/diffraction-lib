# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for analysis/categories/sequential_fit/default.py."""


def test_sequential_fit_defaults():
    from easydiffraction.analysis.categories.sequential_fit.default import SequentialFit

    sequential_fit = SequentialFit()

    assert sequential_fit.data_dir.value == ''
    assert sequential_fit.file_pattern.value == '*'
    assert sequential_fit.max_workers.value == '1'
    assert sequential_fit.chunk_size.value == '.'
    assert sequential_fit.reverse.value is False
    assert sequential_fit._identity.category_code == 'sequential_fit'


def test_sequential_fit_as_cif_serializes_all_fields():
    from easydiffraction.analysis.categories.sequential_fit.default import SequentialFit

    sequential_fit = SequentialFit()
    sequential_fit.data_dir = 'scans'
    sequential_fit.file_pattern = '*.xye'
    sequential_fit.max_workers = 'auto'
    sequential_fit.chunk_size = '4'
    sequential_fit.reverse = True

    as_cif = sequential_fit.as_cif

    assert '_sequential_fit.data_dir scans' in as_cif
    assert '_sequential_fit.file_pattern *.xye' in as_cif
    assert '_sequential_fit.max_workers auto' in as_cif
    assert '_sequential_fit.chunk_size 4' in as_cif
    assert '_sequential_fit.reverse true' in as_cif.lower()
