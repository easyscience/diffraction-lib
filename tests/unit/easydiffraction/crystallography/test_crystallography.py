# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause


def test_module_import():
    import easydiffraction.crystallography.crystallography as MUT

    expected_module_name = 'easydiffraction.crystallography.crystallography'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_symmetry_operators_falls_back_to_identity_for_unlisted_group():
    import numpy as np

    from easydiffraction.crystallography.crystallography import symmetry_operators

    # P 1 is absent from the local SPACE_GROUPS table (the default-structure
    # case that previously raised while building a structure scene).
    ops = symmetry_operators('P 1', '')

    assert len(ops) == 1
    rotation, translation = ops[0]
    assert np.array_equal(rotation, np.eye(3, dtype=int))
    assert np.array_equal(translation, np.zeros(3))
