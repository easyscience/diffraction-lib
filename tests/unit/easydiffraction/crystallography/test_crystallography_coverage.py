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

    def test_invalid_name_hm_returns_cell_unchanged(self, monkeypatch):
        from easydiffraction.utils.logging import Logger

        cell = _make_cell()
        original = dict(cell)
        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)
        result = apply_cell_symmetry_constraints(cell, 'NOT A REAL SG')
        assert result == original
        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.RAISE, raising=True)


# ------------------------------------------------------------------
# cell_symmetry_constrained_flags
# ------------------------------------------------------------------


class TestCellSymmetryConstrainedFlags:
    def test_cubic_only_a_is_free(self):
        from easydiffraction.crystallography.crystallography import cell_symmetry_constrained_flags

        flags = cell_symmetry_constrained_flags('F m -3 m')
        assert flags == {
            'lattice_a': False,
            'lattice_b': True,
            'lattice_c': True,
            'angle_alpha': True,
            'angle_beta': True,
            'angle_gamma': True,
        }

    def test_monoclinic_b_and_beta_free(self):
        from easydiffraction.crystallography.crystallography import cell_symmetry_constrained_flags

        flags = cell_symmetry_constrained_flags('P 21/c')
        assert flags['lattice_a'] is False
        assert flags['lattice_b'] is False
        assert flags['lattice_c'] is False
        assert flags['angle_alpha'] is True
        assert flags['angle_beta'] is False
        assert flags['angle_gamma'] is True

    def test_triclinic_all_free(self):
        from easydiffraction.crystallography.crystallography import cell_symmetry_constrained_flags

        flags = cell_symmetry_constrained_flags('P 1')
        assert all(v is False for v in flags.values())

    def test_invalid_returns_all_false(self, monkeypatch):
        from easydiffraction.crystallography.crystallography import cell_symmetry_constrained_flags
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)
        flags = cell_symmetry_constrained_flags('NOT A REAL SG')
        assert all(v is False for v in flags.values())
        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.RAISE, raising=True)
