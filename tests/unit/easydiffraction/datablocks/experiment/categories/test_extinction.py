# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause


def test_module_import():
    import easydiffraction.datablocks.experiment.categories.extinction.shelx as MUT

    expected_module_name = 'easydiffraction.datablocks.experiment.categories.extinction.shelx'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_extinction_defaults():
    from easydiffraction.datablocks.experiment.categories.extinction.shelx import ShelxExtinction

    ext = ShelxExtinction()
    assert ext.mosaicity.value == 1.0
    assert ext.radius.value == 1.0
    assert ext._identity.category_code == 'extinction'


def test_extinction_property_setters():
    from easydiffraction.datablocks.experiment.categories.extinction.shelx import ShelxExtinction

    ext = ShelxExtinction()

    ext.mosaicity = 0.5
    assert ext.mosaicity.value == 0.5

    ext.radius = 10.0
    assert ext.radius.value == 10.0


def test_extinction_cif_handler_names():
    from easydiffraction.datablocks.experiment.categories.extinction.shelx import ShelxExtinction

    ext = ShelxExtinction()

    mosaicity_cif_names = ext._mosaicity._cif_handler.names
    assert '_extinction.mosaicity' in mosaicity_cif_names

    radius_cif_names = ext._radius._cif_handler.names
    assert '_extinction.radius' in radius_cif_names


def test_extinction_type_info():
    from easydiffraction.datablocks.experiment.categories.extinction.shelx import ShelxExtinction

    assert ShelxExtinction.type_info.tag == 'shelx'
    assert ShelxExtinction.type_info.description != ''


def test_extinction_factory_registration():
    from easydiffraction.datablocks.experiment.categories.extinction.factory import (
        ExtinctionFactory,
    )

    assert 'shelx' in ExtinctionFactory.supported_tags()


def test_extinction_factory_create():
    from easydiffraction.datablocks.experiment.categories.extinction.factory import (
        ExtinctionFactory,
    )
    from easydiffraction.datablocks.experiment.categories.extinction.shelx import ShelxExtinction

    ext = ExtinctionFactory.create('shelx')
    assert isinstance(ext, ShelxExtinction)


def test_extinction_factory_default_tag():
    from easydiffraction.datablocks.experiment.categories.extinction.factory import (
        ExtinctionFactory,
    )

    assert ExtinctionFactory.default_tag() == 'shelx'
