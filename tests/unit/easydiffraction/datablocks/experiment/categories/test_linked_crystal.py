# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause


def test_module_import():
    import easydiffraction.datablocks.experiment.categories.linked_crystal.default as MUT

    expected_module_name = (
        'easydiffraction.datablocks.experiment.categories.linked_crystal.default'
    )
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_linked_crystal_defaults():
    from easydiffraction.datablocks.experiment.categories.linked_crystal.default import (
        LinkedCrystal,
    )

    lc = LinkedCrystal()
    assert lc.id.value == 'Si'
    assert lc.scale.value == 1.0
    assert lc._identity.category_code == 'linked_crystal'


def test_linked_crystal_property_setters():
    from easydiffraction.datablocks.experiment.categories.linked_crystal.default import (
        LinkedCrystal,
    )

    lc = LinkedCrystal()

    lc.id = 'Ge'
    assert lc.id.value == 'Ge'

    lc.scale = 2.5
    assert lc.scale.value == 2.5


def test_linked_crystal_cif_handler_names():
    from easydiffraction.datablocks.experiment.categories.linked_crystal.default import (
        LinkedCrystal,
    )

    lc = LinkedCrystal()

    id_cif_names = lc._id._cif_handler.names
    assert '_sc_crystal_block.id' in id_cif_names

    scale_cif_names = lc._scale._cif_handler.names
    assert '_sc_crystal_block.scale' in scale_cif_names


def test_linked_crystal_type_info():
    from easydiffraction.datablocks.experiment.categories.linked_crystal.default import (
        LinkedCrystal,
    )

    assert LinkedCrystal.type_info.tag == 'default'
    assert LinkedCrystal.type_info.description != ''


def test_linked_crystal_factory_registration():
    from easydiffraction.datablocks.experiment.categories.linked_crystal.factory import (
        LinkedCrystalFactory,
    )

    assert 'default' in LinkedCrystalFactory.supported_tags()


def test_linked_crystal_factory_create():
    from easydiffraction.datablocks.experiment.categories.linked_crystal.default import (
        LinkedCrystal,
    )
    from easydiffraction.datablocks.experiment.categories.linked_crystal.factory import (
        LinkedCrystalFactory,
    )

    lc = LinkedCrystalFactory.create('default')
    assert isinstance(lc, LinkedCrystal)


def test_linked_crystal_factory_default_tag():
    from easydiffraction.datablocks.experiment.categories.linked_crystal.factory import (
        LinkedCrystalFactory,
    )

    assert LinkedCrystalFactory.default_tag() == 'default'
