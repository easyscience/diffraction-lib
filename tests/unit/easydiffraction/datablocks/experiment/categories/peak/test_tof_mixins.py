# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np


def test_tof_gaussian_lorentzian_and_bbe_mixins():
    from easydiffraction.datablocks.experiment.categories.peak.base import PeakBase
    from easydiffraction.datablocks.experiment.categories.peak.tof_mixins import (
        TofBackToBackExponentialMixin,
    )
    from easydiffraction.datablocks.experiment.categories.peak.tof_mixins import (
        TofGaussianBroadeningMixin,
    )
    from easydiffraction.datablocks.experiment.categories.peak.tof_mixins import (
        TofLorentzianBroadeningMixin,
    )

    class TofPeak(
        PeakBase,
        TofGaussianBroadeningMixin,
        TofLorentzianBroadeningMixin,
        TofBackToBackExponentialMixin,
    ):
        def __init__(self):
            super().__init__()

    p = TofPeak()
    names = {param.name for param in p.parameters}
    # Gaussian broadening
    assert {
        'gauss_sigma_0',
        'gauss_sigma_1',
        'gauss_sigma_2',
    }.issubset(names)
    # Lorentzian broadening
    assert {
        'lorentz_gamma_0',
        'lorentz_gamma_1',
        'lorentz_gamma_2',
    }.issubset(names)
    # BBE rise and decay
    assert {'rise_alpha_0', 'rise_alpha_1'}.issubset(names)
    assert {'decay_beta_0', 'decay_beta_1'}.issubset(names)

    # Verify setters update values
    p.broad_gauss_sigma_0 = 1.0
    p.exp_rise_alpha_1 = 0.5
    assert np.isclose(p.broad_gauss_sigma_0.value, 1.0)
    assert np.isclose(p.exp_rise_alpha_1.value, 0.5)
