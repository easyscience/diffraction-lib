# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause


def test_cwl_peak_classes_expose_expected_parameters_and_category():
    from easydiffraction.datablocks.experiment.categories.peak.cwl import CwlPseudoVoigt
    from easydiffraction.datablocks.experiment.categories.peak.cwl import (
        CwlPseudoVoigtBerarBaldinozziAsymmetry,
    )
    from easydiffraction.datablocks.experiment.categories.peak.cwl import CwlThompsonCoxHastings

    pv = CwlPseudoVoigt()
    spv = CwlPseudoVoigtBerarBaldinozziAsymmetry()
    tch = CwlThompsonCoxHastings()

    # Category code set by PeakBase
    for obj in (pv, spv, tch):
        assert obj._identity.category_code == 'peak'

    # Broadening parameters added by CwlBroadeningMixin
    for obj in (pv, spv, tch):
        names = {p.name for p in obj.parameters}
        assert {
            'broad_gauss_u',
            'broad_gauss_v',
            'broad_gauss_w',
            'broad_lorentz_x',
            'broad_lorentz_y',
        }.issubset(names)

    # BerarBaldinozziAsymmetry added only for split PV
    names_spv = {p.name for p in spv.parameters}
    assert {'asym_beba_a0', 'asym_beba_b0', 'asym_beba_a1', 'asym_beba_b1'}.issubset(names_spv)

    # FCJ asymmetry for TCH
    names_tch = {p.name for p in tch.parameters}
    assert {'asym_fcj_1', 'asym_fcj_2'}.issubset(names_tch)


def test_cwl_cutoff_fwhm_default_auto_rejects_negative():
    # cutoff_fwhm defaults to 0 (automatic, tail-aware window); 0 and
    # positive (literal cutoff) values are valid, negatives are not.
    import pytest

    from easydiffraction.datablocks.experiment.categories.peak.cwl import CwlPseudoVoigt

    peak = CwlPseudoVoigt()
    assert peak.cutoff_fwhm.value == 0.0  # automatic by default
    with pytest.raises(TypeError, match='outside'):
        peak.cutoff_fwhm = -3.0
    peak.cutoff_fwhm = 0.0  # auto stays valid
    assert peak.cutoff_fwhm.value == 0.0
    peak.cutoff_fwhm = 25.0  # explicit literal cutoff
    assert peak.cutoff_fwhm.value == 25.0


def test_cwl_cutoff_fwhm_auto_floor_default_and_bounds():
    # cutoff_fwhm_auto_floor is the peak-height fraction the automatic
    # window retains; defaults to 1e-6 and must lie in (0, 1).
    import pytest

    from easydiffraction.datablocks.experiment.categories.peak.cwl import CwlPseudoVoigt

    peak = CwlPseudoVoigt()
    assert peak.cutoff_fwhm_auto_floor.value == 1.0e-6  # default
    with pytest.raises(TypeError, match='outside'):
        peak.cutoff_fwhm_auto_floor = 0.0  # must be > 0
    with pytest.raises(TypeError, match='outside'):
        peak.cutoff_fwhm_auto_floor = 1.0  # must be < 1
    peak.cutoff_fwhm_auto_floor = 1.0e-5  # looser (faster, broad-Lorentzian)
    assert peak.cutoff_fwhm_auto_floor.value == 1.0e-5
