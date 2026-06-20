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


def test_cwl_cutoff_fwhm_rejects_non_positive():
    # Review F3: non-positive cutoff_fwhm is invalid boundary input.
    import pytest

    from easydiffraction.datablocks.experiment.categories.peak.cwl import CwlPseudoVoigt

    peak = CwlPseudoVoigt()
    assert peak.cutoff_fwhm.value > 0
    for bad in (0.0, -3.0):
        with pytest.raises(TypeError, match='outside'):
            peak.cutoff_fwhm = bad
    peak.cutoff_fwhm = 25.0
    assert peak.cutoff_fwhm.value == 25.0
