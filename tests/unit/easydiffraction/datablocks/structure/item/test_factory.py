# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import pytest

from easydiffraction.datablocks.structure.item.factory import StructureFactory


def test_create_minimal_by_name():
    m = StructureFactory.create(name='abc')
    assert m.name == 'abc'


def test_invalid_arg_combo_raises():
    with pytest.raises(ValueError):
        StructureFactory.create(name=None, cif_path=None)
