# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause


def test_module_import():
    import easydiffraction.datablocks.experiment.categories.extinction.becker_coppens as MUT

    expected_module_name = (
        'easydiffraction.datablocks.experiment.categories.extinction.becker_coppens'
    )
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_extinction_defaults():
    from easydiffraction.datablocks.experiment.categories.extinction.becker_coppens import (
        BeckerCoppensExtinction,
    )

    ext = BeckerCoppensExtinction()
    assert ext.model.value == 'gauss'
    assert ext.mosaicity.value == 1.0
    assert ext.radius.value == 1.0
    assert ext._identity.category_code == 'extinction'


def test_extinction_model_setter():
    from easydiffraction.datablocks.experiment.categories.extinction.becker_coppens import (
        BeckerCoppensExtinction,
    )

    ext = BeckerCoppensExtinction()

    ext.model = 'lorentz'
    assert ext.model.value == 'lorentz'

    ext.model = 'gauss'
    assert ext.model.value == 'gauss'


def test_extinction_model_invalid(monkeypatch):
    from easydiffraction.datablocks.experiment.categories.extinction.becker_coppens import (
        BeckerCoppensExtinction,
    )
    from easydiffraction.utils.logging import Logger

    # Invalid input is rejected by fallback (keep current) under WARN mode.
    monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

    ext = BeckerCoppensExtinction()

    ext.model = 'invalid'
    assert ext.model.value == 'gauss'  # keeps previous value


def test_extinction_property_setters():
    from easydiffraction.datablocks.experiment.categories.extinction.becker_coppens import (
        BeckerCoppensExtinction,
    )

    ext = BeckerCoppensExtinction()

    ext.mosaicity = 0.5
    assert ext.mosaicity.value == 0.5

    ext.radius = 10.0
    assert ext.radius.value == 10.0


def test_extinction_cif_handler_names():
    from easydiffraction.datablocks.experiment.categories.extinction.becker_coppens import (
        BeckerCoppensExtinction,
    )

    ext = BeckerCoppensExtinction()

    model_cif_names = ext._model._cif_handler.names
    assert '_extinction.model' in model_cif_names

    mosaicity_cif_names = ext._mosaicity._cif_handler.names
    assert '_extinction.mosaicity' in mosaicity_cif_names

    radius_cif_names = ext._radius._cif_handler.names
    assert '_extinction.radius' in radius_cif_names


def test_extinction_type_info():
    from easydiffraction.datablocks.experiment.categories.extinction.becker_coppens import (
        BeckerCoppensExtinction,
    )

    assert BeckerCoppensExtinction.type_info.tag == 'becker-coppens'
    assert BeckerCoppensExtinction.type_info.description != ''


def test_extinction_factory_registration():
    from easydiffraction.datablocks.experiment.categories.extinction.factory import (
        ExtinctionFactory,
    )

    assert 'becker-coppens' in ExtinctionFactory.supported_tags()


def test_extinction_factory_create():
    from easydiffraction.datablocks.experiment.categories.extinction.becker_coppens import (
        BeckerCoppensExtinction,
    )
    from easydiffraction.datablocks.experiment.categories.extinction.factory import (
        ExtinctionFactory,
    )

    ext = ExtinctionFactory.create('becker-coppens')
    assert isinstance(ext, BeckerCoppensExtinction)


def test_extinction_factory_default_tag():
    from easydiffraction.datablocks.experiment.categories.extinction.factory import (
        ExtinctionFactory,
    )

    assert ExtinctionFactory.default_tag() == 'becker-coppens'
