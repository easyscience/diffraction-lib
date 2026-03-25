# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import pytest


def test_peak_factory_default_and_combinations_and_errors():
    from easydiffraction.datablocks.experiment.categories.peak.factory import PeakFactory
    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum

    # Explicit valid combos by tag
    p = PeakFactory.create('pseudo-voigt')
    assert p._identity.category_code == 'peak'

    # Explicit valid combos by tag
    p1 = PeakFactory.create('pseudo-voigt')
    assert p1.__class__.__name__ == 'CwlPseudoVoigt'

    p2 = PeakFactory.create('pseudo-voigt * ikeda-carpenter')
    assert p2.__class__.__name__ == 'TofPseudoVoigtIkedaCarpenter'

    p3 = PeakFactory.create('gaussian-damped-sinc')
    assert p3.__class__.__name__ == 'TotalGaussianDampedSinc'

    # Context-dependent defaults
    tag_bragg_cwl = PeakFactory.default_tag(
        scattering_type=ScatteringTypeEnum.BRAGG,
        beam_mode=BeamModeEnum.CONSTANT_WAVELENGTH,
    )
    assert tag_bragg_cwl == 'pseudo-voigt'

    tag_bragg_tof = PeakFactory.default_tag(
        scattering_type=ScatteringTypeEnum.BRAGG,
        beam_mode=BeamModeEnum.TIME_OF_FLIGHT,
    )
    assert tag_bragg_tof == 'pseudo-voigt * ikeda-carpenter'

    tag_total = PeakFactory.default_tag(
        scattering_type=ScatteringTypeEnum.TOTAL,
    )
    assert tag_total == 'gaussian-damped-sinc'

    # supported_for filtering
    cwl_profiles = PeakFactory.supported_for(
        scattering_type=ScatteringTypeEnum.BRAGG,
        beam_mode=BeamModeEnum.CONSTANT_WAVELENGTH,
    )
    assert len(cwl_profiles) == 3
    assert all(k.type_info.tag for k in cwl_profiles)

    # Invalid tag
    with pytest.raises(ValueError):
        PeakFactory.create('nonexistent-profile')
