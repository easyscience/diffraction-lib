# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import pytest


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


def test_reciprocal_cell_lengths_orthorhombic():
    from easydiffraction.crystallography.crystallography import reciprocal_cell_lengths

    # For 90-degree angles the reciprocal edges are simply 1/a, 1/b, 1/c.
    a_star, b_star, c_star = reciprocal_cell_lengths(5.0, 6.0, 8.0, 90.0, 90.0, 90.0)

    assert a_star == pytest.approx(1.0 / 5.0)
    assert b_star == pytest.approx(1.0 / 6.0)
    assert c_star == pytest.approx(1.0 / 8.0)


def test_reciprocal_cell_lengths_cubic_isotropic():
    from easydiffraction.crystallography.crystallography import reciprocal_cell_lengths

    a_star, b_star, c_star = reciprocal_cell_lengths(10.13, 10.13, 10.13, 90.0, 90.0, 90.0)

    assert a_star == pytest.approx(1.0 / 10.13)
    assert a_star == pytest.approx(b_star)
    assert b_star == pytest.approx(c_star)


def test_reciprocal_cell_lengths_monoclinic_matches_volume_formula():
    import numpy as np

    from easydiffraction.crystallography.crystallography import reciprocal_cell_lengths

    a, b, c, alpha, beta, gamma = 5.0, 6.0, 7.0, 90.0, 100.0, 90.0
    a_star, b_star, c_star = reciprocal_cell_lengths(a, b, c, alpha, beta, gamma)

    # a* = b*c*sin(alpha) / V, with V the direct-cell volume.
    al, be, ga = np.radians([alpha, beta, gamma])
    omega = np.sqrt(
        1.0
        - np.cos(al) ** 2
        - np.cos(be) ** 2
        - np.cos(ga) ** 2
        + 2.0 * np.cos(al) * np.cos(be) * np.cos(ga)
    )
    volume = a * b * c * omega
    assert a_star == pytest.approx(b * c * np.sin(al) / volume)
    assert c_star == pytest.approx(a * b * np.sin(ga) / volume)


def test_reciprocal_cell_lengths_rejects_non_positive_edge():
    from easydiffraction.crystallography.crystallography import reciprocal_cell_lengths

    with pytest.raises(ValueError, match='Non-positive cell edge'):
        reciprocal_cell_lengths(0.0, 6.0, 8.0, 90.0, 90.0, 90.0)


def test_reciprocal_cell_lengths_rejects_degenerate_angles():
    from easydiffraction.crystallography.crystallography import reciprocal_cell_lengths

    with pytest.raises(ValueError, match='Degenerate cell angles'):
        reciprocal_cell_lengths(5.0, 6.0, 8.0, 150.0, 150.0, 150.0)
