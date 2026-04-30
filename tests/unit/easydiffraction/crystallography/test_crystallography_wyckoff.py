# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Additional tests for crystallography.py to cover _get_wyckoff_exprs error paths."""

from easydiffraction.utils.logging import Logger


class TestGetWyckoffExprs:
    def test_invalid_name_hm_returns_none(self, monkeypatch):
        from easydiffraction.crystallography.crystallography import _get_wyckoff_exprs

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)
        result = _get_wyckoff_exprs('NOT A REAL SG', 1, 'a')
        assert result is None
        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.RAISE, raising=True)

    def test_none_coord_code_returns_none(self, monkeypatch):
        from easydiffraction.crystallography.crystallography import _get_wyckoff_exprs

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)
        result = _get_wyckoff_exprs('P 1', None, 'a')
        assert result is None
        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.RAISE, raising=True)

    def test_valid_returns_three_expressions(self):
        from easydiffraction.crystallography.crystallography import _get_wyckoff_exprs

        # P m -3 m (IT 221) uses coord_code='1'
        result = _get_wyckoff_exprs('P m -3 m', '1', 'a')
        assert result is not None
        assert len(result) == 3


class TestApplyAtomSiteSymmetryConstraints:
    def test_invalid_name_hm_returns_unchanged(self, monkeypatch):
        from easydiffraction.crystallography.crystallography import (
            apply_atom_site_symmetry_constraints,
        )

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)
        atom = {'fract_x': 0.1, 'fract_y': 0.2, 'fract_z': 0.3}
        original = dict(atom)
        result = apply_atom_site_symmetry_constraints(atom, 'NOT REAL', None, 'a')
        assert result == original
        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.RAISE, raising=True)

    def test_valid_applies_constraints(self):
        from easydiffraction.crystallography.crystallography import (
            apply_atom_site_symmetry_constraints,
        )

        # P m -3 m (IT 221), coord_code='1', Wyckoff 'a' has fixed coordinates
        atom = {'fract_x': 0.0, 'fract_y': 0.0, 'fract_z': 0.0}
        result = apply_atom_site_symmetry_constraints(atom, 'P m -3 m', '1', 'a')
        assert result is not None


class TestAtomSiteSymmetryFixedFlags:
    def test_special_position_all_fixed(self):
        from easydiffraction.crystallography.crystallography import (
            atom_site_symmetry_fixed_flags,
        )

        # P m -3 m (IT 221), Wyckoff 'a' = (0,0,0): all three axes fixed
        flags = atom_site_symmetry_fixed_flags('P m -3 m', '1', 'a')
        assert flags == {'fract_x': True, 'fract_y': True, 'fract_z': True}

    def test_general_position_all_free(self):
        from easydiffraction.crystallography.crystallography import (
            atom_site_symmetry_fixed_flags,
        )

        # P 1 (IT 1), Wyckoff 'a' is the general position
        flags = atom_site_symmetry_fixed_flags('P 1', '1', 'a')
        assert flags == {'fract_x': False, 'fract_y': False, 'fract_z': False}

    def test_invalid_returns_all_false(self, monkeypatch):
        from easydiffraction.crystallography.crystallography import (
            atom_site_symmetry_fixed_flags,
        )
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)
        flags = atom_site_symmetry_fixed_flags('NOT REAL', None, 'a')
        assert flags == {'fract_x': False, 'fract_y': False, 'fract_z': False}
        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.RAISE, raising=True)
