# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import pytest


def test_data_factory_default_and_errors():
    from easydiffraction.datablocks.experiment.categories.data.factory import DataFactory

    # Ensure concrete classes are registered
    from easydiffraction.datablocks.experiment.categories.data import bragg_pd  # noqa: F401
    from easydiffraction.datablocks.experiment.categories.data import bragg_sc  # noqa: F401
    from easydiffraction.datablocks.experiment.categories.data import total_pd  # noqa: F401

    # Explicit type by tag
    obj = DataFactory.create('bragg-pd')
    assert obj.__class__.__name__ == 'PdCwlData'

    # Explicit type by tag
    obj2 = DataFactory.create('bragg-pd-tof')
    assert obj2.__class__.__name__ == 'PdTofData'

    obj3 = DataFactory.create('bragg-sc')
    assert obj3.__class__.__name__ == 'ReflnData'

    obj4 = DataFactory.create('total-pd')
    assert obj4.__class__.__name__ == 'TotalData'

    # Unsupported tag should raise ValueError
    with pytest.raises(ValueError):
        DataFactory.create('nonexistent')


def test_data_factory_default_tag_resolution():
    from easydiffraction.datablocks.experiment.categories.data.factory import DataFactory
    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
    from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum

    # Ensure concrete classes are registered
    from easydiffraction.datablocks.experiment.categories.data import bragg_pd  # noqa: F401
    from easydiffraction.datablocks.experiment.categories.data import bragg_sc  # noqa: F401
    from easydiffraction.datablocks.experiment.categories.data import total_pd  # noqa: F401

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

    # Context-dependent default: single crystal
    tag = DataFactory.default_tag(
        sample_form=SampleFormEnum.SINGLE_CRYSTAL,
        scattering_type=ScatteringTypeEnum.BRAGG,
    )
    assert tag == 'bragg-sc'


def test_data_factory_supported_tags():
    from easydiffraction.datablocks.experiment.categories.data.factory import DataFactory

    # Ensure concrete classes are registered
    from easydiffraction.datablocks.experiment.categories.data import bragg_pd  # noqa: F401
    from easydiffraction.datablocks.experiment.categories.data import bragg_sc  # noqa: F401
    from easydiffraction.datablocks.experiment.categories.data import total_pd  # noqa: F401

    tags = DataFactory.supported_tags()
    assert 'bragg-pd' in tags
    assert 'bragg-pd-tof' in tags
    assert 'bragg-sc' in tags
    assert 'total-pd' in tags

