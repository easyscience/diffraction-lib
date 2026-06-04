# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import pytest


def test_calculator_factory_default_and_create():
    from easydiffraction.datablocks.experiment.categories.calculator.default import Calculator
    from easydiffraction.datablocks.experiment.categories.calculator.factory import (
        CalculatorCategoryFactory,
    )

    assert CalculatorCategoryFactory.default_tag() == 'default'
    assert 'default' in CalculatorCategoryFactory.supported_tags()

    calculator_category = CalculatorCategoryFactory.create('default', type='cryspy')

    assert isinstance(calculator_category, Calculator)


def test_calculator_factory_rejects_unknown_tag():
    from easydiffraction.datablocks.experiment.categories.calculator.factory import (
        CalculatorCategoryFactory,
    )

    with pytest.raises(ValueError, match=r"Unsupported type: 'missing'"):
        CalculatorCategoryFactory.create('missing', type='cryspy')
