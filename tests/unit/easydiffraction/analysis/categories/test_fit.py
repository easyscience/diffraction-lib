# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for the fit category."""


def test_module_import():
    import easydiffraction.analysis.categories.fit as MUT

    expected_module_name = 'easydiffraction.analysis.categories.fit'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


class TestFitModeEnum:
    def test_members(self):
        from easydiffraction.analysis.categories.fit.enums import FitModeEnum

        assert FitModeEnum.SINGLE == 'single'
        assert FitModeEnum.JOINT == 'joint'
        assert FitModeEnum.SEQUENTIAL == 'sequential'

    def test_default(self):
        from easydiffraction.analysis.categories.fit.enums import FitModeEnum

        assert FitModeEnum.default() is FitModeEnum.SINGLE

    def test_descriptions(self):
        from easydiffraction.analysis.categories.fit.enums import FitModeEnum

        for member in FitModeEnum:
            desc = member.description()
            assert isinstance(desc, str)
            assert len(desc) > 0


class TestFitFactory:
    def test_supported_tags(self):
        from easydiffraction.analysis.categories.fit.factory import FitFactory

        tags = FitFactory.supported_tags()
        assert 'default' in tags

    def test_default_tag(self):
        from easydiffraction.analysis.categories.fit.factory import FitFactory

        assert FitFactory.default_tag() == 'default'

    def test_create(self):
        from easydiffraction.analysis.categories.fit.default import Fit
        from easydiffraction.analysis.categories.fit.factory import FitFactory

        obj = FitFactory.create('default')
        assert isinstance(obj, Fit)


class TestFit:
    def test_instantiation(self):
        from easydiffraction.analysis.categories.fit.default import Fit

        fit = Fit()
        assert fit is not None

    def test_type_info(self):
        from easydiffraction.analysis.categories.fit.default import Fit

        assert Fit.type_info.tag == 'default'

    def test_identity_category_code(self):
        from easydiffraction.analysis.categories.fit.default import Fit

        fit = Fit()
        assert fit._identity.category_code == 'fit'

    def test_mode_default(self):
        from easydiffraction.analysis.categories.fit.default import Fit
        from easydiffraction.analysis.categories.fit.enums import FitModeEnum

        fit = Fit()
        assert fit.mode.value == FitModeEnum.default().value

    def test_mode_setter(self):
        from easydiffraction.analysis.categories.fit.default import Fit

        fit = Fit()
        fit.mode = 'joint'
        assert fit.mode.value == 'joint'

    def test_minimizer_default(self):
        from easydiffraction.analysis.categories.fit.default import Fit

        fit = Fit()
        assert fit.minimizer_type.value == 'lmfit (leastsq)'
