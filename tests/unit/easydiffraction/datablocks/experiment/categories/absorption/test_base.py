# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import gemmi
import pytest


def test_module_import():
    import easydiffraction.datablocks.experiment.categories.absorption.base as MUT

    assert MUT.__name__.endswith('absorption.base')


def test_type_descriptor_tag_names():
    from easydiffraction.datablocks.experiment.categories.absorption.none import NoAbsorption

    absorption = NoAbsorption()
    assert '_absorption.type' in absorption._type._tags.edi_names
    assert absorption._type._tags.cif_name == '_easydiffraction_absorption.type'


def test_absorption_exposed_on_bragg_powder_only():
    from easydiffraction import ExperimentFactory

    bragg = ExperimentFactory.from_scratch(
        name='bragg',
        sample_form='powder',
        beam_mode='constant wavelength',
        radiation_probe='neutron',
        scattering_type='bragg',
    )
    assert hasattr(bragg, 'absorption')
    assert bragg.absorption.type == 'none'
    assert bragg.absorption._parent is bragg

    total = ExperimentFactory.from_scratch(
        name='total',
        sample_form='powder',
        beam_mode='constant wavelength',
        radiation_probe='neutron',
        scattering_type='total',
    )
    assert not hasattr(total, 'absorption')


def test_switch_to_cylinder_hewat():
    from easydiffraction import ExperimentFactory
    from easydiffraction.datablocks.experiment.categories.absorption.cylinder_hewat import (
        CylinderHewatAbsorption,
    )

    experiment = ExperimentFactory.from_scratch(
        name='cwl',
        sample_form='powder',
        beam_mode='constant wavelength',
        radiation_probe='neutron',
        scattering_type='bragg',
    )
    experiment.absorption.type = 'cylinder-hewat'
    assert experiment.absorption.type == 'cylinder-hewat'
    assert isinstance(experiment.absorption, CylinderHewatAbsorption)

    experiment.absorption.mu_r = 0.7
    assert experiment.absorption.mu_r.value == 0.7


def test_cylinder_hewat_rejected_on_time_of_flight():
    from easydiffraction import ExperimentFactory

    experiment = ExperimentFactory.from_scratch(
        name='tof',
        sample_form='powder',
        beam_mode='time-of-flight',
        radiation_probe='neutron',
        scattering_type='bragg',
    )
    with pytest.raises(ValueError, match='absorption'):
        experiment.absorption.type = 'cylinder-hewat'
    assert experiment.absorption.type == 'none'


def test_from_cif_skips_type_descriptor():
    # The active type is restored by the owner's context-validated
    # ``_restore_switchable_types``; the generic ``from_cif`` must not
    # reapply ``_absorption.type``, or a rejected tag would desync the
    # live category from its public selector.
    from easydiffraction.datablocks.experiment.categories.absorption.cylinder_hewat import (
        CylinderHewatAbsorption,
    )

    doc = gemmi.cif.Document()
    block = doc.add_new_block('test')
    block.set_pair('_absorption.type', 'none')
    block.set_pair('_absorption.mu_r', '0.5')

    absorption = CylinderHewatAbsorption()
    absorption.from_cif(block)

    assert absorption.mu_r.value == 0.5  # non-type parameter is loaded
    assert absorption.type == 'cylinder-hewat'  # type descriptor skipped


def test_cif_round_trip_cylinder_hewat():
    from easydiffraction import ExperimentFactory

    experiment = ExperimentFactory.from_scratch(
        name='lab6',
        sample_form='powder',
        beam_mode='constant wavelength',
        radiation_probe='neutron',
        scattering_type='bragg',
    )
    experiment.absorption.type = 'cylinder-hewat'
    experiment.absorption.mu_r = 0.7

    restored = ExperimentFactory.from_cif_str(experiment.as_cif)

    assert restored.absorption.type == 'cylinder-hewat'
    assert restored.absorption.mu_r.value == 0.7
