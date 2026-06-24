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
        'broad_gauss_sigma_0',
        'broad_gauss_sigma_1',
        'broad_gauss_sigma_2',
    }.issubset(names)
    # Lorentzian broadening
    assert {
        'broad_lorentz_gamma_0',
        'broad_lorentz_gamma_1',
        'broad_lorentz_gamma_2',
    }.issubset(names)
    # BBE rise and decay
    assert {'rise_alpha_0', 'rise_alpha_1'}.issubset(names)
    assert {'decay_beta_0', 'decay_beta_1'}.issubset(names)

    # Verify setters update values
    p.broad_gauss_sigma_0 = 1.0
    p.rise_alpha_1 = 0.5
    assert np.isclose(p.broad_gauss_sigma_0.value, 1.0)
    assert np.isclose(p.rise_alpha_1.value, 0.5)


def test_tof_double_exponential_mixin():
    from easydiffraction.datablocks.experiment.categories.peak.base import PeakBase
    from easydiffraction.datablocks.experiment.categories.peak.tof_mixins import (
        TofDoubleExponentialMixin,
    )
    from easydiffraction.datablocks.experiment.categories.peak.tof_mixins import (
        TofGaussianBroadeningMixin,
    )
    from easydiffraction.datablocks.experiment.categories.peak.tof_mixins import (
        TofLorentzianBroadeningMixin,
    )

    class DoublePeak(
        PeakBase,
        TofGaussianBroadeningMixin,
        TofLorentzianBroadeningMixin,
        TofDoubleExponentialMixin,
    ):
        def __init__(self):
            super().__init__()

    p = DoublePeak()
    names = {param.name for param in p.parameters}
    # Gaussian + Lorentzian broadening from existing mixins
    assert {'broad_gauss_sigma_0', 'broad_gauss_sigma_1', 'broad_gauss_sigma_2'}.issubset(names)
    assert {'broad_lorentz_gamma_0', 'broad_lorentz_gamma_1', 'broad_lorentz_gamma_2'}.issubset(
        names
    )
    # Double-exp rise
    assert {'dexp_rise_alpha_1', 'dexp_rise_alpha_2'}.issubset(names)
    # Double-exp decay
    assert {'dexp_decay_beta_00', 'dexp_decay_beta_01', 'dexp_decay_beta_10'}.issubset(names)
    # Switching function
    assert {'dexp_switch_r_01', 'dexp_switch_r_02', 'dexp_switch_r_03'}.issubset(names)

    # Verify setters update values
    p.dexp_rise_alpha_1 = 0.42
    p.dexp_switch_r_03 = 1.5
    assert np.isclose(p.dexp_rise_alpha_1.value, 0.42)
    assert np.isclose(p.dexp_switch_r_03.value, 1.5)
