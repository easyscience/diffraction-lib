# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause


def test_module_import():
    import easydiffraction.datablocks.experiment.categories.linked_structure.default as MUT

    expected_module_name = (
        'easydiffraction.datablocks.experiment.categories.linked_structure.default'
    )
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_linked_structure_defaults():
    from easydiffraction.datablocks.experiment.categories.linked_structure.default import (
        LinkedStructure,
    )

    lc = LinkedStructure()
    assert lc.structure_id.value == 'Si'
    assert lc.scale.value == 1.0
    assert lc._identity.category_code == 'linked_structure'


def test_linked_structure_property_setters():
    from easydiffraction.datablocks.experiment.categories.linked_structure.default import (
        LinkedStructure,
    )

    lc = LinkedStructure()

    lc.structure_id = 'Ge'
    assert lc.structure_id.value == 'Ge'

    lc.scale = 2.5
    assert lc.scale.value == 2.5


def test_linked_structure_cif_handler_names():
    from easydiffraction.datablocks.experiment.categories.linked_structure.default import (
        LinkedStructure,
    )

    lc = LinkedStructure()

    id_cif_names = lc._structure_id._cif_handler.names
    assert '_linked_structure.structure_id' in id_cif_names

    scale_cif_names = lc._scale._cif_handler.names
    assert '_linked_structure.scale' in scale_cif_names


def test_linked_structure_type_info():
    from easydiffraction.datablocks.experiment.categories.linked_structure.default import (
        LinkedStructure,
    )

    assert LinkedStructure.type_info.tag == 'default'
    assert LinkedStructure.type_info.description != ''


def test_linked_structure_factory_registration():
    from easydiffraction.datablocks.experiment.categories.linked_structure.factory import (
        LinkedStructureFactory,
    )

    assert 'default' in LinkedStructureFactory.supported_tags()


def test_linked_structure_factory_create():
    from easydiffraction.datablocks.experiment.categories.linked_structure.default import (
        LinkedStructure,
    )
    from easydiffraction.datablocks.experiment.categories.linked_structure.factory import (
        LinkedStructureFactory,
    )

    lc = LinkedStructureFactory.create('default')
    assert isinstance(lc, LinkedStructure)


def test_linked_structure_factory_default_tag():
    from easydiffraction.datablocks.experiment.categories.linked_structure.factory import (
        LinkedStructureFactory,
    )

    assert LinkedStructureFactory.default_tag() == 'default'
