# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for fit_mode category (enums, factory, fit_mode)."""


def test_module_import():
    import easydiffraction.analysis.categories.fit_mode as MUT

    expected_module_name = 'easydiffraction.analysis.categories.fit_mode'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


class TestFitModeEnum:
    def test_members(self):
        from easydiffraction.analysis.categories.fit_mode.enums import FitModeEnum

        assert FitModeEnum.SINGLE == 'single'
        assert FitModeEnum.JOINT == 'joint'

    def test_default(self):
        from easydiffraction.analysis.categories.fit_mode.enums import FitModeEnum

        assert FitModeEnum.default() is FitModeEnum.SINGLE

    def test_descriptions(self):
        from easydiffraction.analysis.categories.fit_mode.enums import FitModeEnum

        for member in FitModeEnum:
            desc = member.description()
            assert isinstance(desc, str)
            assert len(desc) > 0


class TestFitModeFactory:
    def test_supported_tags(self):
        from easydiffraction.analysis.categories.fit_mode.factory import FitModeFactory

        tags = FitModeFactory.supported_tags()
        assert 'default' in tags

    def test_default_tag(self):
        from easydiffraction.analysis.categories.fit_mode.factory import FitModeFactory

        assert FitModeFactory.default_tag() == 'default'

    def test_create(self):
        from easydiffraction.analysis.categories.fit_mode.factory import FitModeFactory
        from easydiffraction.analysis.categories.fit_mode.fit_mode import FitMode

        obj = FitModeFactory.create('default')
        assert isinstance(obj, FitMode)


class TestFitMode:
    def test_instantiation(self):
        from easydiffraction.analysis.categories.fit_mode.fit_mode import FitMode

        fm = FitMode()
        assert fm is not None

    def test_type_info(self):
        from easydiffraction.analysis.categories.fit_mode.fit_mode import FitMode

        assert FitMode.type_info.tag == 'default'

    def test_identity_category_code(self):
        from easydiffraction.analysis.categories.fit_mode.fit_mode import FitMode

        fm = FitMode()
        assert fm._identity.category_code == 'fit_mode'

    def test_mode_default(self):
        from easydiffraction.analysis.categories.fit_mode.enums import FitModeEnum
        from easydiffraction.analysis.categories.fit_mode.fit_mode import FitMode

        fm = FitMode()
        assert fm.mode.value == FitModeEnum.default().value

    def test_mode_setter(self):
        from easydiffraction.analysis.categories.fit_mode.fit_mode import FitMode

        fm = FitMode()
        fm.mode = 'joint'
        assert fm.mode.value == 'joint'
