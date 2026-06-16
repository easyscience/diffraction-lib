# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for io/cif/parse.py."""


class TestDocumentFromString:
    def test_valid_cif(self):
        from easydiffraction.io.cif.parse import document_from_string

        cif = 'data_test\n_cell.length_a 5.0\n'
        doc = document_from_string(cif)
        assert len(doc) == 1

    def test_pick_sole_block(self):
        from easydiffraction.io.cif.parse import document_from_string
        from easydiffraction.io.cif.parse import pick_sole_block

        cif = 'data_myblock\n_cell.length_a 5.0\n'
        doc = document_from_string(cif)
        block = pick_sole_block(doc)
        assert block is not None

    def test_name_from_block(self):
        from easydiffraction.io.cif.parse import document_from_string
        from easydiffraction.io.cif.parse import name_from_block
        from easydiffraction.io.cif.parse import pick_sole_block

        cif = 'data_silicon\n_cell.length_a 5.43\n'
        doc = document_from_string(cif)
        block = pick_sole_block(doc)
        name = name_from_block(block)
        assert name == 'silicon'


class TestDocumentFromPath:
    def test_valid_file(self, tmp_path):
        from easydiffraction.io.cif.parse import document_from_path

        cif_file = tmp_path / 'test.cif'
        cif_file.write_text('data_fromfile\n_cell.length_a 3.0\n')
        doc = document_from_path(str(cif_file))
        assert len(doc) == 1


class TestReadCifStr:
    def _block(self, cif_body: str):
        from easydiffraction.io.cif.parse import document_from_string
        from easydiffraction.io.cif.parse import pick_sole_block

        return pick_sole_block(document_from_string(f'data_t\n{cif_body}'))

    def test_absent_tag_returns_none(self):
        from easydiffraction.io.cif.parse import read_cif_str

        block = self._block('_other.tag value\n')
        assert read_cif_str(block, '_missing.tag') is None

    def test_unknown_marker_returns_none(self):
        from easydiffraction.io.cif.parse import read_cif_str

        block = self._block('_peak.profile_type ?\n')
        assert read_cif_str(block, '_peak.profile_type') is None

    def test_inapplicable_marker_returns_none(self):
        from easydiffraction.io.cif.parse import read_cif_str

        block = self._block('_peak.profile_type .\n')
        assert read_cif_str(block, '_peak.profile_type') is None

    def test_unquoted_value(self):
        from easydiffraction.io.cif.parse import read_cif_str

        block = self._block('_peak.profile_type pseudo-voigt\n')
        assert read_cif_str(block, '_peak.profile_type') == 'pseudo-voigt'

    def test_double_quoted_value(self):
        from easydiffraction.io.cif.parse import read_cif_str

        block = self._block('_peak.profile_type "pseudo-voigt + berar-baldinozzi asymmetry"\n')
        assert read_cif_str(block, '_peak.profile_type') == 'pseudo-voigt + berar-baldinozzi asymmetry'

    def test_single_quoted_value(self):
        from easydiffraction.io.cif.parse import read_cif_str

        block = self._block("_peak.profile_type 'pseudo-voigt + berar-baldinozzi asymmetry'\n")
        assert read_cif_str(block, '_peak.profile_type') == 'pseudo-voigt + berar-baldinozzi asymmetry'
