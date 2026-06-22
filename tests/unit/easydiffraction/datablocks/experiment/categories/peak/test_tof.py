# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.datablocks.experiment.categories.peak.tof import TofDoubleJorgensenVonDreele
from easydiffraction.datablocks.experiment.categories.peak.tof import TofJorgensen
from easydiffraction.datablocks.experiment.categories.peak.tof import TofJorgensenVonDreele
from easydiffraction.datablocks.experiment.item.enums import PeakProfileTypeEnum


def test_tof_jorgensen_has_broadening_and_bbe_params():
    peak = TofJorgensen()
    assert peak.broad_gauss_sigma_0.name == 'broad_gauss_sigma_0'
    peak.broad_gauss_sigma_2 = 1.23
    assert peak.broad_gauss_sigma_2.value == 1.23
    assert peak.rise_alpha_0.name == 'rise_alpha_0'
    assert peak.decay_beta_0.name == 'decay_beta_0'


def test_tof_jorgensen_von_dreele_has_lorentzian_broadening():
    peak = TofJorgensenVonDreele()
    assert peak.broad_lorentz_gamma_0.name == 'broad_lorentz_gamma_0'
    peak.rise_alpha_1 = 0.77
    assert peak.rise_alpha_1.value == 0.77


def test_tof_jorgensen_von_dreele_has_bbe_decay():
    peak = TofJorgensenVonDreele()
    assert peak.decay_beta_0.name == 'decay_beta_0'


def test_tof_double_jorgensen_von_dreele_has_double_bbe_params():
    peak = TofDoubleJorgensenVonDreele()
    # Gaussian + Lorentzian broadening
    assert peak.broad_gauss_sigma_0.name == 'broad_gauss_sigma_0'
    assert peak.broad_lorentz_gamma_0.name == 'broad_lorentz_gamma_0'
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


def test_tof_cutoff_fwhm_default_auto_rejects_negative():
    # cutoff_fwhm defaults to 0 (automatic, tail-aware window); 0 and
    # positive (literal cutoff) values are valid, negatives are not.
    import pytest

    peak = TofJorgensenVonDreele()
    assert peak.cutoff_fwhm.value == 0.0  # automatic by default
    with pytest.raises(TypeError, match='outside'):
        peak.cutoff_fwhm = -1.0
    peak.cutoff_fwhm = 0.0  # auto stays valid
    assert peak.cutoff_fwhm.value == 0.0
    peak.cutoff_fwhm = 7.5  # explicit literal cutoff
    assert peak.cutoff_fwhm.value == 7.5


def test_tof_cutoff_fwhm_auto_floor_default_and_bounds():
    # cutoff_fwhm_auto_floor is the peak-height fraction the automatic
    # window retains; defaults to 1e-6 and must lie in (0, 1).
    import pytest

    peak = TofJorgensenVonDreele()
    assert peak.cutoff_fwhm_auto_floor.value == 1.0e-6  # default
    with pytest.raises(TypeError, match='outside'):
        peak.cutoff_fwhm_auto_floor = 0.0  # must be > 0
    with pytest.raises(TypeError, match='outside'):
        peak.cutoff_fwhm_auto_floor = 1.0  # must be < 1
    peak.cutoff_fwhm_auto_floor = 1.0e-5  # looser (faster, broad-Lorentzian)
    assert peak.cutoff_fwhm_auto_floor.value == 1.0e-5
