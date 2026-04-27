# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import gemmi


class _Parent:
    def __init__(self, calculation):
        self._calculator = None
        self._set_calls = []
        self.calculation = calculation

    def _set_calculator_type(self, value: str, *, announce: bool = True) -> None:
        del announce
        self._set_calls.append(value)
        self._calculator = object()
        self.calculation._calculator_type.value = value

    def _resolve_calculation(self) -> None:
        self._calculator = object()

    @staticmethod
    def _supported_calculator_tags() -> list[str]:
        return ['cryspy', 'crysfml']


def test_calculation_defaults():
    from easydiffraction.datablocks.experiment.categories.calculation.default import Calculation

    calculation = Calculation(calculator_type='cryspy')

    assert calculation.type_info.tag == 'default'
    assert calculation._identity.category_code == 'calculation'
    assert calculation.calculator_type.value == 'cryspy'


def test_calculation_setter_delegates_to_parent():
    from easydiffraction.datablocks.experiment.categories.calculation.default import Calculation

    calculation = Calculation(calculator_type='cryspy')
    parent = _Parent(calculation)
    calculation._parent = parent

    calculation.calculator_type = 'crysfml'

    assert parent._set_calls == ['crysfml']
    assert calculation.calculator_type.value == 'crysfml'


def test_calculator_property_resolves_from_parent():
    from easydiffraction.datablocks.experiment.categories.calculation.default import Calculation

    calculation = Calculation(calculator_type='cryspy')
    parent = _Parent(calculation)
    calculation._parent = parent

    calculator = calculation.calculator

    assert calculator is parent._calculator
    assert calculator is not None


def test_show_calculator_types_prints(capsys):
    from easydiffraction.datablocks.experiment.categories.calculation.default import Calculation

    calculation = Calculation(calculator_type='cryspy')
    parent = _Parent(calculation)
    calculation._parent = parent

    calculation.show_calculator_types()
    out = capsys.readouterr().out

    assert 'Calculator types' in out
    assert 'cryspy' in out


def test_from_cif_restores_value_with_parent():
    from easydiffraction.datablocks.experiment.categories.calculation.default import Calculation

    calculation = Calculation(calculator_type='cryspy')
    parent = _Parent(calculation)
    calculation._parent = parent
    block = gemmi.cif.read_string(
        'data_test\n_calculation.calculator_type crysfml\n',
    ).sole_block()

    calculation.from_cif(block)

    assert parent._set_calls == ['crysfml']
    assert calculation.calculator_type.value == 'crysfml'
