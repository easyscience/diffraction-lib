# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import pytest


def test_background_factory_default_and_errors():
    from easydiffraction.datablocks.experiment.categories.background.factory import (
        BackgroundFactory,
    )

    # Default via default_tag()
    obj = BackgroundFactory.create(BackgroundFactory.default_tag())
    assert obj.__class__.__name__.endswith('LineSegmentBackground')

    # Explicit type by tag
    obj2 = BackgroundFactory.create('chebyshev')
    assert obj2.__class__.__name__.endswith('ChebyshevPolynomialBackground')

    # Unsupported tag should raise ValueError
    with pytest.raises(
        ValueError,
        match=r"Unsupported type: 'nonexistent'\. Supported: .*",
    ):
        BackgroundFactory.create('nonexistent')


def test_background_factory_includes_chebyshev_for_crysfml():
    from easydiffraction.datablocks.experiment.categories.background.factory import (
        BackgroundFactory,
    )
    from easydiffraction.datablocks.experiment.item.enums import CalculatorEnum

    tags = [
        klass.type_info.tag
        for klass in BackgroundFactory.supported_for(calculator=CalculatorEnum.CRYSFML)
    ]

    assert 'line-segment' in tags
    assert 'chebyshev' in tags
