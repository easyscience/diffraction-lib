# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Additional tests for ExperimentFactory creation paths."""

import pytest

from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import RadiationProbeEnum
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
from easydiffraction.datablocks.experiment.item.factory import ExperimentFactory
from easydiffraction.utils.logging import Logger


class TestExperimentFactoryFromScratch:
    def test_powder_bragg_cwl(self):
        ex = ExperimentFactory.from_scratch(
            name='test_pd',
            sample_form='powder',
            beam_mode='constant wavelength',
            radiation_probe='neutron',
            scattering_type='bragg',
        )
        assert ex.name == 'test_pd'
        assert ex.type.sample_form.value == SampleFormEnum.POWDER.value
        assert ex.type.beam_mode.value == BeamModeEnum.CONSTANT_WAVELENGTH.value
        assert ex.type.scattering_type.value == ScatteringTypeEnum.BRAGG.value

    def test_powder_bragg_tof(self):
        ex = ExperimentFactory.from_scratch(
            name='test_tof',
            sample_form='powder',
            beam_mode='time-of-flight',
            radiation_probe='neutron',
            scattering_type='bragg',
        )
        assert ex.name == 'test_tof'
        assert ex.type.beam_mode.value == BeamModeEnum.TIME_OF_FLIGHT.value

    def test_single_crystal_cwl(self):
        ex = ExperimentFactory.from_scratch(
            name='test_sc',
            sample_form='single crystal',
            beam_mode='constant wavelength',
            radiation_probe='neutron',
            scattering_type='bragg',
        )
        assert ex.name == 'test_sc'
        assert ex.type.sample_form.value == SampleFormEnum.SINGLE_CRYSTAL.value

    def test_single_crystal_tof(self):
        ex = ExperimentFactory.from_scratch(
            name='test_sc_tof',
            sample_form='single crystal',
            beam_mode='time-of-flight',
            radiation_probe='neutron',
            scattering_type='bragg',
        )
        assert ex.name == 'test_sc_tof'
        assert ex.type.beam_mode.value == BeamModeEnum.TIME_OF_FLIGHT.value

    def test_total_scattering(self):
        ex = ExperimentFactory.from_scratch(
            name='test_total',
            sample_form='powder',
            scattering_type='total',
        )
        assert ex.type.scattering_type.value == ScatteringTypeEnum.TOTAL.value

    def test_defaults_used_when_none(self):
        ex = ExperimentFactory.from_scratch(name='defaults')
        assert ex.type.sample_form.value == SampleFormEnum.default().value
        assert ex.type.beam_mode.value == BeamModeEnum.default().value
        assert ex.type.scattering_type.value == ScatteringTypeEnum.default().value
        assert ex.type.radiation_probe.value == RadiationProbeEnum.default().value


class TestExperimentFactoryInstantiationBlocked:
    def test_direct_instantiation_raises(self, monkeypatch):
        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.RAISE, raising=True)
        with pytest.raises(AttributeError, match='class methods'):
            ExperimentFactory()


class TestExperimentFactoryCreateExperimentType:
    def test_partial_overrides(self):
        et = ExperimentFactory._create_experiment_type(
            sample_form='single crystal',
        )
        assert et.sample_form.value == SampleFormEnum.SINGLE_CRYSTAL.value
        # others get defaults
        assert et.beam_mode.value == BeamModeEnum.default().value
