# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for diffrn category (default and factory)."""


def test_module_import():
    import easydiffraction.datablocks.experiment.categories.diffrn as MUT

    expected_module_name = 'easydiffraction.datablocks.experiment.categories.diffrn'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


class TestDiffrnFactory:
    def test_supported_tags(self):
        from easydiffraction.datablocks.experiment.categories.diffrn.factory import DiffrnFactory

        tags = DiffrnFactory.supported_tags()
        assert 'default' in tags

    def test_default_tag(self):
        from easydiffraction.datablocks.experiment.categories.diffrn.factory import DiffrnFactory

        assert DiffrnFactory.default_tag() == 'default'

    def test_create(self):
        from easydiffraction.datablocks.experiment.categories.diffrn.default import DefaultDiffrn
        from easydiffraction.datablocks.experiment.categories.diffrn.factory import DiffrnFactory

        obj = DiffrnFactory.create('default')
        assert isinstance(obj, DefaultDiffrn)


class TestDefaultDiffrn:
    def test_instantiation(self):
        from easydiffraction.datablocks.experiment.categories.diffrn.default import DefaultDiffrn

        d = DefaultDiffrn()
        assert d is not None

    def test_type_info(self):
        from easydiffraction.datablocks.experiment.categories.diffrn.default import DefaultDiffrn

        assert DefaultDiffrn.type_info.tag == 'default'

    def test_identity_category_code(self):
        from easydiffraction.datablocks.experiment.categories.diffrn.default import DefaultDiffrn

        d = DefaultDiffrn()
        assert d._identity.category_code == 'diffrn'

    def test_defaults_are_none(self):
        from easydiffraction.datablocks.experiment.categories.diffrn.default import DefaultDiffrn

        d = DefaultDiffrn()
        assert d.ambient_temperature.value is None
        assert d.ambient_pressure.value is None
        assert d.ambient_magnetic_field.value is None
        assert d.ambient_electric_field.value is None

    def test_setters(self):
        from easydiffraction.datablocks.experiment.categories.diffrn.default import DefaultDiffrn

        d = DefaultDiffrn()
        d.ambient_temperature = 300.0
        assert d.ambient_temperature.value == 300.0
        d.ambient_pressure = 101.325
        assert d.ambient_pressure.value == 101.325
        d.ambient_magnetic_field = 5.0
        assert d.ambient_magnetic_field.value == 5.0
        d.ambient_electric_field = 1000.0
        assert d.ambient_electric_field.value == 1000.0
