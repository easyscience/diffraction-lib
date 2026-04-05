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
