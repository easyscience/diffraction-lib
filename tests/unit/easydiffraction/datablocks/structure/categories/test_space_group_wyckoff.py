# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for the derived space_group_wyckoff category (default + factory)."""

import pytest

from easydiffraction.crystallography import crystallography as ecr
from easydiffraction.datablocks.structure.item.base import Structure


def _cubic_structure():
    """Return a structure on the tabulated cubic group P m -3 m."""
    structure = Structure(name='s')
    structure.space_group.name_h_m = 'P m -3 m'
    structure._update_categories()
    return structure


class TestSpaceGroupWyckoffFactory:
    def test_supported_tags(self):
        from easydiffraction.datablocks.structure.categories.space_group_wyckoff.factory import (
            SpaceGroupWyckoffFactory,
        )

        assert 'default' in SpaceGroupWyckoffFactory.supported_tags()

    def test_create_default(self):
        from easydiffraction.datablocks.structure.categories.space_group_wyckoff.default import (
            SpaceGroupWyckoffCollection,
        )
        from easydiffraction.datablocks.structure.categories.space_group_wyckoff.factory import (
            SpaceGroupWyckoffFactory,
        )

        obj = SpaceGroupWyckoffFactory.create('default')
        assert isinstance(obj, SpaceGroupWyckoffCollection)


class TestDerivedRows:
    def test_auto_populates_from_space_group(self):
        structure = _cubic_structure()
        table = ecr.space_group_wyckoff_table('P m -3 m', '1')
        assert len(structure.space_group_wyckoff) == len(table)
        for row in structure.space_group_wyckoff:
            entry = table[row.letter.value]
            assert row.multiplicity.value == entry['multiplicity']
            assert row.site_symmetry.value == str(entry['site_symmetry'])

    def test_uses_id_keys_of_multiplicity_plus_letter(self):
        structure = _cubic_structure()
        row = structure.space_group_wyckoff['1a']
        assert row.id.value == '1a'
        assert row.letter.value == 'a'
        assert row.multiplicity.value == 1

    def test_preserves_site_symmetry_verbatim(self):
        # Site-symmetry strings (including any dots) are stored exactly
        # as the bundled table provides them, not normalised.
        structure = _cubic_structure()
        table = ecr.space_group_wyckoff_table('P m -3 m', '1')
        for row in structure.space_group_wyckoff:
            assert row.site_symmetry.value == str(table[row.letter.value]['site_symmetry'])

    def test_rebuilds_on_space_group_change(self):
        structure = _cubic_structure()
        assert '1a' in {r.id.value for r in structure.space_group_wyckoff}
        structure.space_group.name_h_m = 'F m -3 m'
        structure._update_categories()
        ids = {r.id.value for r in structure.space_group_wyckoff}
        # Fm-3m has no multiplicity-1 'a'; the stale Pm-3m key is gone.
        assert '1a' not in ids
        assert '4a' in ids
        with pytest.raises(KeyError):
            _ = structure.space_group_wyckoff['1a']

    def test_empty_for_absent_group(self, monkeypatch):
        structure = _cubic_structure()
        assert len(structure.space_group_wyckoff) > 0
        monkeypatch.setattr(ecr, 'space_group_wyckoff_table', lambda *a, **k: None)
        structure.space_group_wyckoff._replace_from_space_group()
        assert len(structure.space_group_wyckoff) == 0


class TestReadOnly:
    def test_rejects_all_public_mutation(self):
        structure = _cubic_structure()
        wy = structure.space_group_wyckoff
        row = wy['1a']
        with pytest.raises(ValueError):
            wy.add(row)
        with pytest.raises(ValueError):
            wy.create()
        with pytest.raises(ValueError):
            wy.remove('1a')
        with pytest.raises(ValueError):
            wy['1a'] = row
        with pytest.raises(ValueError):
            del wy['1a']

    def test_from_cif_ignores_incoming_loop(self):
        # A hand-edited _space_group_Wyckoff loop must be discarded; the
        # table is derived from the space group, not read from CIF.
        from easydiffraction.datablocks.structure.item.factory import StructureFactory

        cif = (
            "data_x\n"
            "_space_group.name_H-M_alt 'P m -3 m'\n"
            '_space_group.IT_coordinate_system_code 1\n'
            'loop_\n'
            '_space_group_Wyckoff.id\n'
            '_space_group_Wyckoff.letter\n'
            '_space_group_Wyckoff.multiplicity\n'
            '_space_group_Wyckoff.site_symmetry\n'
            '_space_group_Wyckoff.coords_xyz\n'
            '  BOGUS bogus 999 zzz (9,9,9)\n'
        )
        structure = StructureFactory.from_cif_str(cif)
        assert all(r.id.value != 'BOGUS' for r in structure.space_group_wyckoff)


class TestSerialization:
    def test_omitted_from_project_cif(self):
        structure = _cubic_structure()
        assert '_space_group_Wyckoff' not in structure.as_cif

    def test_appears_in_report_output(self):
        from easydiffraction.io.cif import iucr_writer

        structure = _cubic_structure()
        lines: list[str] = []
        iucr_writer._write_space_group_wyckoff_section(lines, structure)
        body = '\n'.join(lines)
        assert '_space_group_Wyckoff.id' in body
        assert '_space_group_Wyckoff.coords_xyz' in body
        # Representative coordinate only (compact), never the full orbit.
        assert max(len(line) for line in lines) < 80
