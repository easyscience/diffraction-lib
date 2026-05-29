# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import pytest


def test_refln_factory_default_and_errors():
    from easydiffraction.datablocks.experiment.categories.refln.factory import ReflnFactory

    obj = ReflnFactory.create('bragg-sc-cwl')
    assert obj.__class__.__name__ == 'CwlReflnData'

    obj_tof = ReflnFactory.create('bragg-sc-tof')
    assert obj_tof.__class__.__name__ == 'TofReflnData'

    obj2 = ReflnFactory.create('bragg-pd-refln')
    assert obj2.__class__.__name__ == 'PowderCwlReflnData'

    obj3 = ReflnFactory.create('bragg-pd-tof-refln')
    assert obj3.__class__.__name__ == 'PowderTofReflnData'

    with pytest.raises(
        ValueError,
        match=r"Unsupported type: 'nonexistent'\. Supported: .*",
    ):
        ReflnFactory.create('nonexistent')


def test_refln_factory_default_tag_resolution():
    from easydiffraction.datablocks.experiment.categories.refln.factory import ReflnFactory
    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
    from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum

    tag = ReflnFactory.default_tag(
        sample_form=SampleFormEnum.SINGLE_CRYSTAL,
        scattering_type=ScatteringTypeEnum.BRAGG,
        beam_mode=BeamModeEnum.CONSTANT_WAVELENGTH,
    )
    assert tag == 'bragg-sc-cwl'

    tag = ReflnFactory.default_tag(
        sample_form=SampleFormEnum.SINGLE_CRYSTAL,
        scattering_type=ScatteringTypeEnum.BRAGG,
        beam_mode=BeamModeEnum.TIME_OF_FLIGHT,
    )
    assert tag == 'bragg-sc-tof'

    tag = ReflnFactory.default_tag(
        sample_form=SampleFormEnum.POWDER,
        scattering_type=ScatteringTypeEnum.BRAGG,
        beam_mode=BeamModeEnum.CONSTANT_WAVELENGTH,
    )
    assert tag == 'bragg-pd-refln'

    tag = ReflnFactory.default_tag(
        sample_form=SampleFormEnum.POWDER,
        scattering_type=ScatteringTypeEnum.BRAGG,
        beam_mode=BeamModeEnum.TIME_OF_FLIGHT,
    )
    assert tag == 'bragg-pd-tof-refln'


def test_refln_factory_supported_tags():
    from easydiffraction.datablocks.experiment.categories.refln.factory import ReflnFactory

    tags = ReflnFactory.supported_tags()
    assert 'bragg-sc-cwl' in tags
    assert 'bragg-sc-tof' in tags
    assert 'bragg-pd-refln' in tags
    assert 'bragg-pd-tof-refln' in tags
