# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import gemmi


class _Parent:
    def __init__(self, calculator_category):
        self._calculator = None
        self._set_calls = []
        self.calculator = calculator_category

    def _swap_calculator(
        self,
        value: str,
        *,
        announce: bool = True,
        strict: bool = True,
    ) -> None:
        del announce, strict
        self._set_calls.append(value)
        self._calculator = object()
        self.calculator._type.value = value

    def _resolve_calculator(self) -> None:
        self._calculator = object()

    @staticmethod
    def _supported_calculator_tags() -> list[str]:
        return ['cryspy', 'crysfml']

    @staticmethod
    def _supported_filters_for(category: object) -> dict[str, object]:
        del category
        return {}


def test_calculator_defaults():
    from easydiffraction.datablocks.experiment.categories.calculator.default import Calculator

    calculator_category = Calculator(type='cryspy')

    assert calculator_category.type_info.tag == 'default'
    assert calculator_category._identity.category_code == 'calculator'
    assert calculator_category.type == 'cryspy'


def test_calculator_selector_delegates_to_parent():
    from easydiffraction.datablocks.experiment.categories.calculator.default import Calculator

    calculator_category = Calculator(type='cryspy')
    parent = _Parent(calculator_category)
    calculator_category._parent = parent

    calculator_category.type = 'crysfml'

    assert parent._set_calls == ['crysfml']
    assert calculator_category.type == 'crysfml'


def test_calculator_property_resolves_from_parent():
    from easydiffraction.datablocks.experiment.categories.calculator.default import Calculator

    calculator_category = Calculator(type='cryspy')
    parent = _Parent(calculator_category)
    calculator_category._parent = parent

    calculator = calculator_category.calculator

    assert calculator is parent._calculator
    assert calculator is not None


def test_show_supported_calculators_prints(capsys):
    from easydiffraction.datablocks.experiment.categories.calculator.default import Calculator

    calculator_category = Calculator(type='cryspy')
    parent = _Parent(calculator_category)
    calculator_category._parent = parent

    calculator_category.show_supported()
    out = capsys.readouterr().out

    assert 'Calculator types' in out
    assert 'cryspy' in out


def test_from_cif_restores_value_with_parent():
    from easydiffraction.datablocks.experiment.categories.calculator.default import Calculator

    calculator_category = Calculator(type='cryspy')
    parent = _Parent(calculator_category)
    calculator_category._parent = parent
    block = gemmi.cif.read_string(
        'data_test\n_calculator.type crysfml\n',
    ).sole_block()

    calculator_category.from_cif(block)

    assert parent._set_calls == ['crysfml']
    assert calculator_category.type == 'crysfml'
