# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for cell category (default and factory)."""


def test_module_import():
    import easydiffraction.datablocks.structure.categories.cell as MUT

    expected_module_name = 'easydiffraction.datablocks.structure.categories.cell'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


class TestCellFactory:
    def test_supported_tags(self):
        from easydiffraction.datablocks.structure.categories.cell.factory import CellFactory

        tags = CellFactory.supported_tags()
        assert 'default' in tags

    def test_default_tag(self):
        from easydiffraction.datablocks.structure.categories.cell.factory import CellFactory

        assert CellFactory.default_tag() == 'default'

    def test_create(self):
        from easydiffraction.datablocks.structure.categories.cell.default import Cell
        from easydiffraction.datablocks.structure.categories.cell.factory import CellFactory

        obj = CellFactory.create('default')
        assert isinstance(obj, Cell)


class TestCell:
    def test_instantiation(self):
        from easydiffraction.datablocks.structure.categories.cell.default import Cell

        cell = Cell()
        assert cell is not None

    def test_type_info(self):
        from easydiffraction.datablocks.structure.categories.cell.default import Cell

        assert Cell.type_info.tag == 'default'

    def test_identity_category_code(self):
        from easydiffraction.datablocks.structure.categories.cell.default import Cell

        cell = Cell()
        assert cell._identity.category_code == 'cell'

    def test_defaults(self):
        from easydiffraction.datablocks.structure.categories.cell.default import Cell

        cell = Cell()
        assert cell.length_a.value == 10.0
        assert cell.length_b.value == 10.0
        assert cell.length_c.value == 10.0
        assert cell.angle_alpha.value == 90.0
        assert cell.angle_beta.value == 90.0
        assert cell.angle_gamma.value == 90.0

    def test_length_setters(self):
        from easydiffraction.datablocks.structure.categories.cell.default import Cell

        cell = Cell()
        cell.length_a = 5.0
        cell.length_b = 6.0
        cell.length_c = 7.0
        assert cell.length_a.value == 5.0
        assert cell.length_b.value == 6.0
        assert cell.length_c.value == 7.0

    def test_angle_setters(self):
        from easydiffraction.datablocks.structure.categories.cell.default import Cell

        cell = Cell()
        cell.angle_alpha = 80.0
        cell.angle_beta = 85.0
        cell.angle_gamma = 95.0
        assert cell.angle_alpha.value == 80.0
        assert cell.angle_beta.value == 85.0
        assert cell.angle_gamma.value == 95.0
