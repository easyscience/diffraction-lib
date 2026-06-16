# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import pytest


def test_peak_factory_default_and_combinations_and_errors():
    from easydiffraction.datablocks.experiment.categories.peak.factory import PeakFactory
    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import PeakProfileTypeEnum
    from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum

    supported_tags = PeakFactory.supported_tags()
    assert len(supported_tags) == len(set(supported_tags))

    # Explicit valid combos by canonical tag
    p = PeakFactory.create(PeakProfileTypeEnum.CWL_PSEUDO_VOIGT)
    assert p._identity.category_code == 'peak'

    p1 = PeakFactory.create(PeakProfileTypeEnum.CWL_PSEUDO_VOIGT)
    assert p1.__class__.__name__ == 'CwlPseudoVoigt'

    p_tof = PeakFactory.create(PeakProfileTypeEnum.TOF_PSEUDO_VOIGT)
    assert p_tof.__class__.__name__ == 'TofPseudoVoigt'

    p2 = PeakFactory.create(PeakProfileTypeEnum.TOF_JORGENSEN)
    assert p2.__class__.__name__ == 'TofJorgensen'

    p3 = PeakFactory.create(PeakProfileTypeEnum.TOTAL_GAUSSIAN_DAMPED_SINC)
    assert p3.__class__.__name__ == 'TotalGaussianDampedSinc'

    # Context-dependent defaults
    tag_bragg_cwl = PeakFactory.default_tag(
        scattering_type=ScatteringTypeEnum.BRAGG,
        beam_mode=BeamModeEnum.CONSTANT_WAVELENGTH,
    )
    assert tag_bragg_cwl is PeakProfileTypeEnum.CWL_PSEUDO_VOIGT

    tag_bragg_tof = PeakFactory.default_tag(
        scattering_type=ScatteringTypeEnum.BRAGG,
        beam_mode=BeamModeEnum.TIME_OF_FLIGHT,
    )
    assert tag_bragg_tof is PeakProfileTypeEnum.TOF_JORGENSEN

    tag_total = PeakFactory.default_tag(
        scattering_type=ScatteringTypeEnum.TOTAL,
    )
    assert tag_total is PeakProfileTypeEnum.TOTAL_GAUSSIAN_DAMPED_SINC

    cwl_alias = PeakFactory._canonical_tag_for(
        'pseudo-voigt',
        scattering_type=ScatteringTypeEnum.BRAGG,
        beam_mode=BeamModeEnum.CONSTANT_WAVELENGTH,
    )
    assert cwl_alias == PeakProfileTypeEnum.CWL_PSEUDO_VOIGT

    # The Berar-Baldinozzi user type string resolves to the renamed tag
    # and class in the constant-wavelength Bragg context.
    beba_alias = PeakFactory._canonical_tag_for(
        'pseudo-voigt + berar-baldinozzi asymmetry',
        scattering_type=ScatteringTypeEnum.BRAGG,
        beam_mode=BeamModeEnum.CONSTANT_WAVELENGTH,
    )
    assert beba_alias == PeakProfileTypeEnum.CWL_PSEUDO_VOIGT_BERAR_BALDINOZZI_ASYMMETRY
    beba_peak = PeakFactory.create(beba_alias)
    assert beba_peak.__class__.__name__ == 'CwlPseudoVoigtBerarBaldinozziAsymmetry'

    tof_alias = PeakFactory._canonical_tag_for(
        'pseudo-voigt',
        scattering_type=ScatteringTypeEnum.BRAGG,
        beam_mode=BeamModeEnum.TIME_OF_FLIGHT,
    )
    assert tof_alias == PeakProfileTypeEnum.TOF_PSEUDO_VOIGT

    # supported_for filtering
    cwl_profiles = PeakFactory.supported_for(
        scattering_type=ScatteringTypeEnum.BRAGG,
        beam_mode=BeamModeEnum.CONSTANT_WAVELENGTH,
    )
    assert len(cwl_profiles) == 3
    assert all(k.type_info.tag for k in cwl_profiles)
    assert [k.__name__ for k in cwl_profiles] == [
        'CwlPseudoVoigt',
        'CwlPseudoVoigtBerarBaldinozziAsymmetry',
        'CwlThompsonCoxHastings',
    ]

    # Local aliases are context-dependent and not accepted by bare create().
    with pytest.raises(
        ValueError,
        match=r"Unsupported type: 'pseudo-voigt'\. Supported: .*",
    ):
        PeakFactory.create('pseudo-voigt')

    # Invalid tag
    with pytest.raises(
        ValueError,
        match=r"Unsupported type: 'nonexistent-profile'\. Supported: .*",
    ):
        PeakFactory.create('nonexistent-profile')
