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

    def test_none_coord_code_resolves_triclinic(self):
        from easydiffraction.crystallography.crystallography import _get_wyckoff_exprs

        # Triclinic groups are keyed ``(IT_number, None)``: P 1 (IT 1)
        # resolves through the ``None`` coordinate code to its general
        # position (x, y, z) rather than being treated as unset.
        result = _get_wyckoff_exprs('P 1', None, 'a')
        assert result is not None
        assert len(result) == 3

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

    def test_coupled_special_position_slaves_dependent_axis(self):
        from easydiffraction.crystallography.crystallography import (
            apply_atom_site_symmetry_constraints,
        )

        # R -3 m (IT 166), coord_code='h', Wyckoff 'h' = (x,-x,z): editing
        # fract_x slaves fract_y to -fract_x while fract_x/fract_z stay free
        # (the ed-6 coupled-position regression).
        atom = {'fract_x': 0.3, 'fract_y': 0.0, 'fract_z': 0.5}
        result = apply_atom_site_symmetry_constraints(atom, 'R -3 m', 'h', 'h')
        assert result['fract_x'] == 0.3
        assert result['fract_y'] == -0.3
        assert result['fract_z'] == 0.5


class TestAtomSiteSymmetryConstrainedFlags:
    def test_special_position_all_fixed(self):
        from easydiffraction.crystallography.crystallography import (
            atom_site_symmetry_constrained_flags,
        )

        # P m -3 m (IT 221), Wyckoff 'a' = (0,0,0): all three axes fixed
        flags = atom_site_symmetry_constrained_flags('P m -3 m', '1', 'a')
        assert flags == {'fract_x': True, 'fract_y': True, 'fract_z': True}

    def test_general_position_all_free(self):
        from easydiffraction.crystallography.crystallography import (
            atom_site_symmetry_constrained_flags,
        )

        # P 1 (IT 1), Wyckoff 'a' is the general position
        flags = atom_site_symmetry_constrained_flags('P 1', '1', 'a')
        assert flags == {'fract_x': False, 'fract_y': False, 'fract_z': False}

    def test_coupled_special_position_constrains_dependent_axis(self):
        from easydiffraction.crystallography.crystallography import (
            atom_site_symmetry_constrained_flags,
        )

        # R -3 m (IT 166), Wyckoff 'h' = (x,-x,z): fract_y is slaved to -x,
        # so only fract_y is constrained. Operator-form coords_xyz would
        # wrongly mark fract_y free (the canonical-templates regression).
        flags = atom_site_symmetry_constrained_flags('R -3 m', 'h', 'h')
        assert flags == {'fract_x': False, 'fract_y': True, 'fract_z': False}

    def test_invalid_returns_all_false(self, monkeypatch):
        from easydiffraction.crystallography.crystallography import (
            atom_site_symmetry_constrained_flags,
        )
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)
        flags = atom_site_symmetry_constrained_flags('NOT REAL', None, 'a')
        assert flags == {'fract_x': False, 'fract_y': False, 'fract_z': False}
        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.RAISE, raising=True)


class TestDetectWyckoffPosition:
    def test_general_position(self):
        from easydiffraction.crystallography.crystallography import detect_wyckoff_position

        # A generic point in P m -3 m is the general position 'n' (48).
        position = detect_wyckoff_position('P m -3 m', '1', (0.12, 0.23, 0.34))
        assert position.letter == 'n'
        assert position.multiplicity == 48

    def test_special_position(self):
        from easydiffraction.crystallography.crystallography import detect_wyckoff_position

        position = detect_wyckoff_position('P m -3 m', '1', (0.0, 0.0, 0.0))
        assert position.letter == 'a'
        assert position.multiplicity == 1

    def test_multiplicity_tie_break_prefers_most_special(self):
        from easydiffraction.crystallography.crystallography import detect_wyckoff_position

        # (1/2,0,0) lies on both 'e' = (x,0,0) (mult 6) and the more
        # special 'd' = (1/2,0,0) (mult 3); detection prefers 'd'.
        position = detect_wyckoff_position('P m -3 m', '1', (0.5, 0.0, 0.0))
        assert position.letter == 'd'
        assert position.multiplicity == 3

    def test_non_first_orbit_representative(self):
        from easydiffraction.crystallography.crystallography import detect_wyckoff_position

        # (0,y,0) is on the 'e' orbit via a non-first representative
        # ((0,x,0), not the tabulated first rep (x,0,0)).
        position = detect_wyckoff_position('P m -3 m', '1', (0.0, 0.3, 0.0))
        assert position.letter == 'e'

    def test_rounded_input_matches_within_tolerance(self):
        from easydiffraction.crystallography.crystallography import detect_wyckoff_position

        # x = 0.3333 ~ 1/3 is still on 'e' = (x,0,0) at the 1e-3 tolerance.
        position = detect_wyckoff_position('P m -3 m', '1', (0.3333, 0.0, 0.0))
        assert position.letter == 'e'

    def test_empty_coord_code_normalises_to_none(self):
        from easydiffraction.crystallography.crystallography import detect_wyckoff_position

        # P 1 is keyed (1, None); an empty coordinate code resolves there.
        position = detect_wyckoff_position('P 1', '', (0.1, 0.2, 0.3))
        assert position is not None
        assert position.letter == 'a'

    def test_absent_group_returns_none(self, monkeypatch):
        from easydiffraction.crystallography.crystallography import detect_wyckoff_position

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)
        assert detect_wyckoff_position('NOT A REAL SG', None, (0.1, 0.2, 0.3)) is None
        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.RAISE, raising=True)


class TestWyckoffPositionInfo:
    def test_without_coords_has_no_template(self):
        from easydiffraction.crystallography.crystallography import wyckoff_position_info

        position = wyckoff_position_info('P m -3 m', '1', 'e')
        assert position.letter == 'e'
        assert position.multiplicity == 6
        assert position.coord_template is None

    def test_selects_nearest_representative_not_first(self):
        from easydiffraction.crystallography.crystallography import snap_to_wyckoff_template
        from easydiffraction.crystallography.crystallography import wyckoff_position_info

        # 'e' first rep is (x,0,0); for a point near the (0,x,0) member the
        # nearest representative must be chosen so the snap keeps fract_y
        # free near 0.3 instead of collapsing onto (x,0,0) -> (0,0,0).
        position = wyckoff_position_info('P m -3 m', '1', 'e', fract_xyz=(0.0, 0.3, 0.0))
        assert position.coord_template is not None
        snapped, _flags = snap_to_wyckoff_template(position.coord_template, (0.0, 0.3, 0.0))
        assert abs(snapped[0]) < 1e-6
        assert abs(snapped[1] - 0.3) < 1e-6
        assert abs(snapped[2]) < 1e-6

    def test_absent_letter_returns_none(self):
        from easydiffraction.crystallography.crystallography import wyckoff_position_info

        # P m -3 m has no Wyckoff letter 'z'.
        assert wyckoff_position_info('P m -3 m', '1', 'z') is None
