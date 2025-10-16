# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np


def test_chebyshev_background_calculate_and_cif():
    from easydiffraction.experiments.categories.background.chebyshev import (
        ChebyshevPolynomialBackground,
    )
    from easydiffraction.experiments.categories.background.chebyshev import PolynomialTerm

    cb = ChebyshevPolynomialBackground()
    x = np.linspace(0.0, 1.0, 5)

    # Empty background -> zeros
    y0 = cb.calculate(x)
    assert np.allclose(y0, 0.0)

    # Add two terms and verify CIF contains expected tags
    t0 = PolynomialTerm(order=0, coef=1.0)
    t1 = PolynomialTerm(order=1, coef=0.5)
    cb.add(t0)
    cb.add(t1)
    cif = cb.as_cif
    assert '_pd_background.Chebyshev_order' in cif and '_pd_background.Chebyshev_coef' in cif
