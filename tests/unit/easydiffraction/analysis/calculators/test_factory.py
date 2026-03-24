# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import pytest


def test_supported_tags_and_show_supported(capsys):
    from easydiffraction.analysis.calculators.factory import CalculatorFactory

    tags = CalculatorFactory.supported_tags()
    assert isinstance(tags, list)

    CalculatorFactory.show_supported()
    out = capsys.readouterr().out
    assert 'Supported types' in out


def test_create_unknown_raises():
    from easydiffraction.analysis.calculators.factory import CalculatorFactory

    with pytest.raises(ValueError):
        CalculatorFactory.create('this_is_unknown')
