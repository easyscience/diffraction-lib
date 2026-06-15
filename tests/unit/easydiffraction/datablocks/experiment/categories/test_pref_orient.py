# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause


def test_module_import():
    import easydiffraction.datablocks.experiment.categories.pref_orient as MUT

    assert MUT.__name__.endswith('pref_orient')


def test_pref_orient_defaults_are_noop():
    from easydiffraction.datablocks.experiment.categories.pref_orient import PrefOrient

    po = PrefOrient()
    assert po.march_r.value == 1.0  # March coefficient: no texture
    assert po.march_random_fract.value == 0.0  # pure March-Dollase
    assert (po.index_h.value, po.index_k.value, po.index_l.value) == (0, 0, 1)
    assert po.structure_id.value == 'Si'


def test_pref_orient_property_setters():
    from easydiffraction.datablocks.experiment.categories.pref_orient import PrefOrient

    po = PrefOrient()
    po.structure_id = 'lbco'
    po.march_r = 0.75
    po.march_random_fract = 0.2
    po.index_h = 1
    po.index_k = 0
    po.index_l = 2

    assert po.structure_id.value == 'lbco'
    assert po.march_r.value == 0.75
    assert po.march_random_fract.value == 0.2
    assert (po.index_h.value, po.index_k.value, po.index_l.value) == (1, 0, 2)


def test_pref_orient_r_must_be_positive(monkeypatch):
    from easydiffraction.datablocks.experiment.categories.pref_orient import PrefOrient
    from easydiffraction.utils.logging import Logger

    monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

    po = PrefOrient()
    po.march_r = 0.0  # gt=0 -> rejected, keeps default
    assert po.march_r.value == 1.0
    po.march_r = -0.5
    assert po.march_r.value == 1.0


def test_pref_orient_fraction_within_unit_interval(monkeypatch):
    from easydiffraction.datablocks.experiment.categories.pref_orient import PrefOrient
    from easydiffraction.utils.logging import Logger

    monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

    po = PrefOrient()
    po.march_random_fract = 1.5  # le=1 -> rejected
    assert po.march_random_fract.value == 0.0
    po.march_random_fract = -0.1  # ge=0 -> rejected
    assert po.march_random_fract.value == 0.0
    po.march_random_fract = 0.5  # valid
    assert po.march_random_fract.value == 0.5


def test_pref_orients_create_and_default_cif():
    from easydiffraction.datablocks.experiment.categories.pref_orient import PrefOrients

    coll = PrefOrients()
    coll.create(structure_id='lbco', march_r=0.8, index_h=0, index_k=0, index_l=1)

    cif = coll.as_cif
    assert 'loop_' in cif
    for tag in (
        '_preferred_orientation.structure_id',
        '_preferred_orientation.march_r',
        '_preferred_orientation.index_h',
        '_preferred_orientation.index_k',
        '_preferred_orientation.index_l',
        '_preferred_orientation.march_random_fract',
    ):
        assert tag in cif


def test_pref_orient_factory_and_metadata():
    from easydiffraction.datablocks.experiment.categories.pref_orient import PrefOrients
    from easydiffraction.datablocks.experiment.categories.pref_orient.factory import (
        PrefOrientFactory,
    )
    from easydiffraction.datablocks.experiment.item.enums import CalculatorEnum
    from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
    from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum

    coll = PrefOrientFactory.create(PrefOrientFactory.default_tag())
    assert isinstance(coll, PrefOrients)
    assert PrefOrients.type_info.tag == 'default'
    assert SampleFormEnum.POWDER in PrefOrients.compatibility.sample_form
    assert ScatteringTypeEnum.BRAGG in PrefOrients.compatibility.scattering_type
    assert PrefOrients.calculator_support.supports(CalculatorEnum.CRYSPY)
    assert not PrefOrients.calculator_support.supports(CalculatorEnum.PDFFIT)


def test_preferred_orientation_exposed_on_bragg_powder_only():
    from easydiffraction import ExperimentFactory

    bragg = ExperimentFactory.from_scratch(
        name='bragg',
        sample_form='powder',
        beam_mode='constant wavelength',
        radiation_probe='neutron',
        scattering_type='bragg',
    )
    assert hasattr(bragg, 'preferred_orientation')
    bragg.preferred_orientation.create(
        structure_id='bragg', march_r=0.5, index_h=0, index_k=0, index_l=1
    )
    # The collection is parent-linked to the experiment, enabling dirty
    # tracking on row changes.
    assert bragg.preferred_orientation._parent is bragg

    total = ExperimentFactory.from_scratch(
        name='total',
        sample_form='powder',
        beam_mode='constant wavelength',
        radiation_probe='neutron',
        scattering_type='total',
    )
    assert not hasattr(total, 'preferred_orientation')


def test_pref_orient_cif_round_trip():
    from easydiffraction import ExperimentFactory

    experiment = ExperimentFactory.from_scratch(
        name='lbco',
        sample_form='powder',
        beam_mode='constant wavelength',
        radiation_probe='neutron',
        scattering_type='bragg',
    )
    experiment.preferred_orientation.create(
        structure_id='lbco',
        march_r=0.75,
        march_random_fract=0.2,
        index_h=1,
        index_k=0,
        index_l=2,
    )

    restored = ExperimentFactory.from_cif_str(experiment.as_cif)

    row = restored.preferred_orientation['lbco']
    assert row.march_r.value == 0.75
    assert row.march_random_fract.value == 0.2
    assert (row.index_h.value, row.index_k.value, row.index_l.value) == (1, 0, 2)
