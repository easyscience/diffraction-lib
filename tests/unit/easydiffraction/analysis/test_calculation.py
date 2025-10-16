# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause


def test_module_import():
    import easydiffraction.analysis.calculation as MUT

    expected_module_name = 'easydiffraction.analysis.calculation'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_calculator_wrapper_set_and_calls(monkeypatch):
    from easydiffraction.analysis.calculation import Calculator

    calls = {}

    class DummyCalc:
        def calculate_structure_factors(self, sm, exps):
            calls['sf'] = True
            return ['hkl']

        def calculate_pattern(self, sm, expt):
            calls['pat'] = True

    class DummyFactory:
        def create_calculator(self, engine):
            calls['engine'] = engine
            return DummyCalc()

    c = Calculator(engine='cryspy')
    # Inject dummy factory
    c.calculator_factory = DummyFactory()
    c.set_calculator('pdffit')
    assert calls['engine'] == 'pdffit'

    # Call delegates
    assert c.calculate_structure_factors('sm', 'exps') == ['hkl']
    c.calculate_pattern('sm', 'expt')
    assert calls['sf'] and calls['pat']
