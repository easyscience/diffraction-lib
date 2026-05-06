# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import pytest


def test_data_factory_default_and_errors():
    # Ensure concrete classes are registered
    from easydiffraction.datablocks.experiment.categories.data.factory import DataFactory

    # Explicit type by tag
    obj = DataFactory.create('bragg-pd')
    assert obj.__class__.__name__ == 'PdCwlData'

    # Explicit type by tag
    obj2 = DataFactory.create('bragg-pd-tof')
    assert obj2.__class__.__name__ == 'PdTofData'

    obj3 = DataFactory.create('total-pd')
    assert obj3.__class__.__name__ == 'TotalData'

    # Unsupported tag should raise ValueError
    with pytest.raises(
        ValueError,
        match=r"Unsupported type: 'nonexistent'\. Supported: .*",
    ):
        DataFactory.create('nonexistent')


def test_data_factory_default_tag_resolution():
    # Ensure concrete classes are registered
    from easydiffraction.datablocks.experiment.categories.data.factory import DataFactory
    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
    from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum

    # Context-dependent default: Bragg powder CWL
    tag = DataFactory.default_tag(
        sample_form=SampleFormEnum.POWDER,
        scattering_type=ScatteringTypeEnum.BRAGG,
        beam_mode=BeamModeEnum.CONSTANT_WAVELENGTH,
    )
    assert tag == 'bragg-pd'

    # Context-dependent default: Bragg powder TOF
    tag = DataFactory.default_tag(
        sample_form=SampleFormEnum.POWDER,
        scattering_type=ScatteringTypeEnum.BRAGG,
        beam_mode=BeamModeEnum.TIME_OF_FLIGHT,
    )
    assert tag == 'bragg-pd-tof'

    # Context-dependent default: total scattering
    tag = DataFactory.default_tag(
        sample_form=SampleFormEnum.POWDER,
        scattering_type=ScatteringTypeEnum.TOTAL,
    )
    assert tag == 'total-pd'


def test_data_factory_supported_tags():
    # Ensure concrete classes are registered
    from easydiffraction.datablocks.experiment.categories.data.factory import DataFactory

    tags = DataFactory.supported_tags()
    assert 'bragg-pd' in tags
    assert 'bragg-pd-tof' in tags
    assert 'total-pd' in tags
