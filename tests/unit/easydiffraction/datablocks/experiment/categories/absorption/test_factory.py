# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause


def test_module_import():
    import easydiffraction.datablocks.experiment.categories.absorption.factory as MUT

    assert MUT.__name__.endswith('absorption.factory')


def test_factory_default_tag_is_none():
    from easydiffraction.datablocks.experiment.categories.absorption.factory import (
        AbsorptionFactory,
    )

    assert AbsorptionFactory.default_tag() == 'none'


def test_factory_supported_tags():
    from easydiffraction.datablocks.experiment.categories.absorption.factory import (
        AbsorptionFactory,
    )

    tags = AbsorptionFactory.supported_tags()
    assert 'none' in tags
    assert 'cylinder-hewat' in tags


def test_factory_create_returns_concrete_classes():
    from easydiffraction.datablocks.experiment.categories.absorption.cylinder_hewat import (
        CylinderHewatAbsorption,
    )
    from easydiffraction.datablocks.experiment.categories.absorption.factory import (
        AbsorptionFactory,
    )
    from easydiffraction.datablocks.experiment.categories.absorption.none import NoAbsorption

    assert isinstance(AbsorptionFactory.create('none'), NoAbsorption)
    assert isinstance(AbsorptionFactory.create('cylinder-hewat'), CylinderHewatAbsorption)


def test_supported_for_cwl_powder_bragg_offers_both():
    from easydiffraction.datablocks.experiment.categories.absorption.factory import (
        AbsorptionFactory,
    )

    supported = AbsorptionFactory.supported_for(
        calculator='cryspy',
        sample_form='powder',
        scattering_type='bragg',
        beam_mode='constant wavelength',
    )
    tags = {klass.type_info.tag for klass in supported}
    assert tags == {'none', 'cylinder-hewat'}


def test_supported_for_tof_excludes_cylinder_hewat():
    from easydiffraction.datablocks.experiment.categories.absorption.factory import (
        AbsorptionFactory,
    )

    supported = AbsorptionFactory.supported_for(
        calculator='cryspy',
        sample_form='powder',
        scattering_type='bragg',
        beam_mode='time-of-flight',
    )
    tags = {klass.type_info.tag for klass in supported}
    assert 'cylinder-hewat' not in tags
    assert 'none' in tags
