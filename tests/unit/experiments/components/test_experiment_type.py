from easydiffraction.core.objects import Descriptor
from easydiffraction.experiments.components.experiment_type import ExperimentType


def test_experiment_type_initialization():
    experiment_type = ExperimentType(
        sample_form='powder',
        beam_mode='constant wavelength',
        radiation_probe='neutron',
        scattering_type='bragg',
    )

    assert isinstance(experiment_type.sample_form, Descriptor)
    assert experiment_type.sample_form.value == 'powder'
    assert experiment_type.sample_form.name == 'sample_form'
    assert experiment_type.sample_form.full_cif_names == ['_expt_type.sample_form']

    assert isinstance(experiment_type.beam_mode, Descriptor)
    assert experiment_type.beam_mode.value == 'constant wavelength'
    assert experiment_type.beam_mode.name == 'beam_mode'
    assert experiment_type.beam_mode.full_cif_names == ['_expt_type.beam_mode']

    assert isinstance(experiment_type.radiation_probe, Descriptor)
    assert experiment_type.radiation_probe.value == 'neutron'
    assert experiment_type.radiation_probe.name == 'radiation_probe'
    assert experiment_type.radiation_probe.full_cif_names == ['_expt_type.radiation_probe']


def test_experiment_type_properties():
    experiment_type = ExperimentType(
        sample_form='single crystal',
        beam_mode='time-of-flight',
        radiation_probe='xray',
        scattering_type='bragg',
    )

    assert experiment_type.category_key == 'expt_type'
    # Removed legacy attributes: cif_category_key, datablock_id, entry_id, and internal _locked
    # Just validate category_key and basic descriptor integrity
    assert experiment_type.sample_form.full_cif_names[0].startswith('_expt_type.')


def no_test_experiment_type_locking_attributes():
    # TODO: hmm this doesn't work as expected.
    experiment_type = ExperimentType(
        sample_form='powder',
        beam_mode='constant wavelength',
        radiation_probe='neutron',
        scattering_type='bragg',
    )
    experiment_type._locked = True  # Disallow adding new attributes
    experiment_type.new_attribute = 'value'
    assert not hasattr(experiment_type, 'new_attribute')
