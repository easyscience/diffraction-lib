# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.datablocks.experiment.categories.peak.tof import TofDoubleJorgensenVonDreele
from easydiffraction.datablocks.experiment.categories.peak.tof import TofJorgensen
from easydiffraction.datablocks.experiment.categories.peak.tof import TofJorgensenVonDreele
from easydiffraction.datablocks.experiment.item.enums import PeakProfileTypeEnum


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


def test_tof_double_jorgensen_von_dreele_has_double_bbe_params():
    peak = TofDoubleJorgensenVonDreele()
    # Gaussian + Lorentzian broadening
    assert peak.broad_gauss_sigma_0.name == 'gauss_sigma_0'
    assert peak.broad_lorentz_gamma_0.name == 'lorentz_gamma_0'
    # Double-exp parameters
    assert peak.dexp_rise_alpha_1.name == 'dexp_rise_alpha_1'
    assert peak.dexp_decay_beta_00.name == 'dexp_decay_beta_00'
    assert peak.dexp_switch_r_01.name == 'dexp_switch_r_01'
    peak.dexp_decay_beta_10 = 0.33
    assert peak.dexp_decay_beta_10.value == 0.33


def test_tof_jorgensen_descriptions_match_peak_profile_enum():
    assert TofJorgensen.type_info.description == PeakProfileTypeEnum.TOF_JORGENSEN.description()
    assert (
        TofJorgensenVonDreele.type_info.description
        == PeakProfileTypeEnum.TOF_JORGENSEN_VON_DREELE.description()
    )
    assert (
        TofDoubleJorgensenVonDreele.type_info.description
        == PeakProfileTypeEnum.TOF_DOUBLE_JORGENSEN_VON_DREELE.description()
    )
