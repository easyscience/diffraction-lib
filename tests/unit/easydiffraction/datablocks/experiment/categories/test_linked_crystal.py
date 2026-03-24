# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause


def test_module_import():
    import easydiffraction.datablocks.experiment.categories.linked_crystal as MUT

    expected_module_name = 'easydiffraction.datablocks.experiment.categories.linked_crystal'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_linked_crystal_defaults():
    from easydiffraction.datablocks.experiment.categories.linked_crystal import LinkedCrystal

    lc = LinkedCrystal()
    assert lc.id.value == 'Si'
    assert lc.scale.value == 1.0
    assert lc._identity.category_code == 'linked_crystal'


def test_linked_crystal_property_setters():
    from easydiffraction.datablocks.experiment.categories.linked_crystal import LinkedCrystal

    lc = LinkedCrystal()

    lc.id = 'Ge'
    assert lc.id.value == 'Ge'

    lc.scale = 2.5
    assert lc.scale.value == 2.5


def test_linked_crystal_cif_handler_names():
    from easydiffraction.datablocks.experiment.categories.linked_crystal import LinkedCrystal

    lc = LinkedCrystal()

    id_cif_names = lc._id._cif_handler.names
    assert '_sc_crystal_block.id' in id_cif_names

    scale_cif_names = lc._scale._cif_handler.names
    assert '_sc_crystal_block.scale' in scale_cif_names

