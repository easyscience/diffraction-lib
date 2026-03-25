# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np


def test_chebyshev_background_calculate_and_cif():
    from types import SimpleNamespace

    from easydiffraction.datablocks.experiment.categories.background.chebyshev import (
        ChebyshevPolynomialBackground,
    )

    # Create mock parent with data
    x = np.linspace(0.0, 1.0, 5)
    mock_data = SimpleNamespace(x=x, _bkg=None)
    mock_data._set_intensity_bkg = lambda y: setattr(mock_data, '_bkg', y)
    mock_parent = SimpleNamespace(data=mock_data)

    cb = ChebyshevPolynomialBackground()
    object.__setattr__(cb, '_parent', mock_parent)

    # Empty background -> zeros
    cb._update()
    assert np.allclose(mock_data._bkg, 0.0)

    # Add two terms and verify CIF contains expected tags
    cb.create(order=0, coef=1.0)
    cb.create(order=1, coef=0.5)
    cif = cb.as_cif
    assert '_pd_background.Chebyshev_order' in cif and '_pd_background.Chebyshev_coef' in cif
