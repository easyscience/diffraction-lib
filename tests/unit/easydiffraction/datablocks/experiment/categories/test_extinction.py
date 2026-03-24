# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause


def test_module_import():
    import easydiffraction.datablocks.experiment.categories.extinction as MUT

    expected_module_name = 'easydiffraction.datablocks.experiment.categories.extinction'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_extinction_defaults():
    from easydiffraction.datablocks.experiment.categories.extinction import Extinction

    ext = Extinction()
    assert ext.mosaicity.value == 1.0
    assert ext.radius.value == 1.0
    assert ext._identity.category_code == 'extinction'


def test_extinction_property_setters():
    from easydiffraction.datablocks.experiment.categories.extinction import Extinction

    ext = Extinction()

    ext.mosaicity = 0.5
    assert ext.mosaicity.value == 0.5

    ext.radius = 10.0
    assert ext.radius.value == 10.0


def test_extinction_cif_handler_names():
    from easydiffraction.datablocks.experiment.categories.extinction import Extinction

    ext = Extinction()

    mosaicity_cif_names = ext._mosaicity._cif_handler.names
    assert '_extinction.mosaicity' in mosaicity_cif_names

    radius_cif_names = ext._radius._cif_handler.names
    assert '_extinction.radius' in radius_cif_names

