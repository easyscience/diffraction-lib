# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.datablocks.experiment.categories.peak.tof import TofJorgensen
from easydiffraction.datablocks.experiment.categories.peak.tof import TofJorgensenVonDreele


def test_tof_jorgensen_has_broadening_and_bbe_params():
    peak = TofJorgensen()
    assert peak.broad_gauss_sigma_0.name == 'gauss_sigma_0'
    peak.broad_gauss_sigma_2 = 1.23
    assert peak.broad_gauss_sigma_2.value == 1.23
    assert peak.exp_rise_alpha_0.name == 'rise_alpha_0'
    assert peak.exp_decay_beta_0.name == 'decay_beta_0'


def test_tof_jorgensen_von_dreele_has_lorentzian_broadening():
    peak = TofJorgensenVonDreele()
    assert peak.broad_lorentz_gamma_0.name == 'lorentz_gamma_0'
    peak.exp_rise_alpha_1 = 0.77
    assert peak.exp_rise_alpha_1.value == 0.77


def test_tof_jorgensen_von_dreele_has_bbe_decay():
    peak = TofJorgensenVonDreele()
    assert peak.exp_decay_beta_0.name == 'decay_beta_0'
