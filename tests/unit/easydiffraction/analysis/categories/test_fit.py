# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for the fitting category."""


def test_module_import():
    import easydiffraction.analysis.categories.fitting as MUT

    expected_module_name = 'easydiffraction.analysis.categories.fitting'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


class TestFitModeEnum:
    def test_members(self):
        from easydiffraction.analysis.enums import FitModeEnum

        assert FitModeEnum.SINGLE == 'single'
        assert FitModeEnum.JOINT == 'joint'
        assert FitModeEnum.SEQUENTIAL == 'sequential'

    def test_default(self):
        from easydiffraction.analysis.enums import FitModeEnum

        assert FitModeEnum.default() is FitModeEnum.SINGLE

    def test_descriptions(self):
        from easydiffraction.analysis.enums import FitModeEnum

        for member in FitModeEnum:
            desc = member.description()
            assert isinstance(desc, str)
            assert len(desc) > 0


class TestFittingFactory:
    def test_supported_tags(self):
        from easydiffraction.analysis.categories.fitting.factory import FittingFactory

        tags = FittingFactory.supported_tags()
        assert 'default' in tags

    def test_default_tag(self):
        from easydiffraction.analysis.categories.fitting.factory import FittingFactory

        assert FittingFactory.default_tag() == 'default'

    def test_create(self):
        from easydiffraction.analysis.categories.fitting.default import Fitting
        from easydiffraction.analysis.categories.fitting.factory import FittingFactory

        obj = FittingFactory.create('default')
        assert isinstance(obj, Fitting)


class TestFitting:
    def test_instantiation(self):
        from easydiffraction.analysis.categories.fitting.default import Fitting

        fitting = Fitting()
        assert fitting is not None

    def test_type_info(self):
        from easydiffraction.analysis.categories.fitting.default import Fitting

        assert Fitting.type_info.tag == 'default'

    def test_identity_category_code(self):
        from easydiffraction.analysis.categories.fitting.default import Fitting

        fitting = Fitting()
        assert fitting._identity.category_code == 'fitting'

    def test_minimizer_default(self):
        from easydiffraction.analysis.categories.fitting.default import Fitting

        fitting = Fitting()
        assert fitting.minimizer_type.value == 'lmfit (leastsq)'

    def test_minimizer_type_setter(self):
        from easydiffraction.analysis.categories.fitting.default import Fitting

        fitting = Fitting()
        fitting.minimizer_type = 'lmfit'
        assert fitting.minimizer_type.value == 'lmfit'
