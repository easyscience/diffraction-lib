# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
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
    with pytest.raises(ValueError):
        BackgroundFactory.create('nonexistent')
