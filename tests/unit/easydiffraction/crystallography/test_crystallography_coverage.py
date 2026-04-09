# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for crystallographic symmetry constraint functions."""

from easydiffraction.crystallography.crystallography import apply_cell_symmetry_constraints


# ------------------------------------------------------------------
# apply_cell_symmetry_constraints
# ------------------------------------------------------------------


def _make_cell(a=5.0, b=6.0, c=7.0, alpha=80.0, beta=85.0, gamma=75.0):
    return {
        'lattice_a': a,
        'lattice_b': b,
        'lattice_c': c,
        'angle_alpha': alpha,
        'angle_beta': beta,
        'angle_gamma': gamma,
    }


class TestApplyCellSymmetryConstraints:
    def test_cubic(self):
        cell = _make_cell(a=4.0, b=5.0, c=6.0)
        result = apply_cell_symmetry_constraints(cell, 'F m -3 m')  # IT 225
        assert result['lattice_a'] == 4.0
        assert result['lattice_b'] == 4.0
        assert result['lattice_c'] == 4.0
        assert result['angle_alpha'] == 90.0
        assert result['angle_beta'] == 90.0
        assert result['angle_gamma'] == 90.0

    def test_tetragonal(self):
        cell = _make_cell(a=4.0, b=5.0, c=6.0)
        result = apply_cell_symmetry_constraints(cell, 'P 4/m m m')  # IT 123
        assert result['lattice_a'] == 4.0
        assert result['lattice_b'] == 4.0
        assert result['lattice_c'] == 6.0  # c remains unchanged
        assert result['angle_alpha'] == 90.0
        assert result['angle_beta'] == 90.0
        assert result['angle_gamma'] == 90.0

    def test_orthorhombic(self):
        cell = _make_cell(a=4.0, b=5.0, c=6.0)
        result = apply_cell_symmetry_constraints(cell, 'P m m m')  # IT 47
        assert result['lattice_a'] == 4.0
        assert result['lattice_b'] == 5.0
        assert result['lattice_c'] == 6.0
        assert result['angle_alpha'] == 90.0
        assert result['angle_beta'] == 90.0
        assert result['angle_gamma'] == 90.0

    def test_hexagonal(self):
        cell = _make_cell(a=4.0, b=5.0, c=6.0)
        result = apply_cell_symmetry_constraints(cell, 'P 63/m m c')  # IT 194
        assert result['lattice_a'] == 4.0
        assert result['lattice_b'] == 4.0
        assert result['lattice_c'] == 6.0
        assert result['angle_alpha'] == 90.0
        assert result['angle_beta'] == 90.0
        assert result['angle_gamma'] == 120.0

    def test_trigonal(self):
        cell = _make_cell(a=4.0, b=5.0, c=6.0)
        result = apply_cell_symmetry_constraints(cell, 'R -3 m')  # IT 166
        assert result['lattice_a'] == 4.0
        assert result['lattice_b'] == 4.0
        assert result['angle_alpha'] == 90.0
        assert result['angle_beta'] == 90.0
        assert result['angle_gamma'] == 120.0

    def test_monoclinic(self):
        cell = _make_cell(a=4.0, b=5.0, c=6.0, beta=100.0)
        result = apply_cell_symmetry_constraints(cell, 'P 21/c')  # IT 14
        assert result['lattice_a'] == 4.0
        assert result['lattice_b'] == 5.0
        assert result['lattice_c'] == 6.0
        assert result['angle_alpha'] == 90.0
        assert result['angle_beta'] == 100.0  # beta unconstrained
        assert result['angle_gamma'] == 90.0

    def test_triclinic(self):
        cell = _make_cell(a=4.0, b=5.0, c=6.0, alpha=80.0, beta=85.0, gamma=75.0)
        result = apply_cell_symmetry_constraints(cell, 'P 1')  # IT 1
        assert result['lattice_a'] == 4.0
        assert result['lattice_b'] == 5.0
        assert result['lattice_c'] == 6.0
        assert result['angle_alpha'] == 80.0
        assert result['angle_beta'] == 85.0
        assert result['angle_gamma'] == 75.0

    def test_invalid_name_hm_returns_cell_unchanged(self):
        cell = _make_cell()
        original = dict(cell)
        result = apply_cell_symmetry_constraints(cell, 'NOT A REAL SG')
        assert result == original
