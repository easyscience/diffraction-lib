# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import pytest


def test_calculation_factory_default_and_create():
    from easydiffraction.datablocks.experiment.categories.calculation.default import Calculation
    from easydiffraction.datablocks.experiment.categories.calculation.factory import (
        CalculationFactory,
    )

    assert CalculationFactory.default_tag() == 'default'
    assert 'default' in CalculationFactory.supported_tags()

    calculation = CalculationFactory.create('default', calculator_type='cryspy')

    assert isinstance(calculation, Calculation)


def test_calculation_factory_rejects_unknown_tag():
    from easydiffraction.datablocks.experiment.categories.calculation.factory import (
        CalculationFactory,
    )

    with pytest.raises(ValueError, match=r"Unsupported type: 'missing'"):
        CalculationFactory.create('missing', calculator_type='cryspy')
