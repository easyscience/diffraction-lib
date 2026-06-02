# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.datablocks.experiment.categories.peak.cwl import CwlPseudoVoigt
from easydiffraction.datablocks.experiment.categories.peak.cwl import (
    CwlPseudoVoigtEmpiricalAsymmetry,
)
from easydiffraction.datablocks.experiment.categories.peak.cwl import CwlThompsonCoxHastings


def test_cwl_pseudo_voigt_params_exist_and_settable():
    peak = CwlPseudoVoigt()
    # CwlBroadening parameters
    assert peak.broad_gauss_u.name == 'broad_gauss_u'
    peak.broad_gauss_u = 0.123
    assert peak.broad_gauss_u.value == 0.123
    # Squared-degree units render with a Unicode superscript.
    assert peak.broad_gauss_u.resolve_display_units('gui') == 'deg²'


def test_cwl_split_pseudo_voigt_adds_empirical_asymmetry():
    peak = CwlPseudoVoigtEmpiricalAsymmetry()
    # Has broadening and empirical asymmetry params
    assert peak.broad_gauss_w.name == 'broad_gauss_w'
    assert peak.asym_empir_1.name == 'asym_empir_1'
    peak.asym_empir_2 = 0.345
    assert peak.asym_empir_2.value == 0.345


def test_cwl_tch_adds_fcj_asymmetry():
    peak = CwlThompsonCoxHastings()
    assert peak.asym_fcj_1.name == 'asym_fcj_1'
    peak.asym_fcj_2 = 0.456
    assert peak.asym_fcj_2.value == 0.456
