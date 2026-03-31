# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import pytest

from easydiffraction.datablocks.experiment.categories.experiment_type import ExperimentType
from easydiffraction.datablocks.experiment.item.bragg_sc import CwlScExperiment
from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import RadiationProbeEnum
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
from easydiffraction.utils.logging import Logger


def _mk_type_sc_bragg():
    et = ExperimentType()
    et._set_sample_form(SampleFormEnum.SINGLE_CRYSTAL.value)
    et._set_beam_mode(BeamModeEnum.CONSTANT_WAVELENGTH.value)
    et._set_radiation_probe(RadiationProbeEnum.NEUTRON.value)
    et._set_scattering_type(ScatteringTypeEnum.BRAGG.value)
    return et


class _ConcreteCwlSc(CwlScExperiment):
    def _load_ascii_data_to_experiment(self, data_path: str) -> int:
        # Not used in this test
        return 0


def test_init_and_placeholder_no_crash(monkeypatch: pytest.MonkeyPatch):
    # Prevent logger from raising on attribute errors inside __init__
    monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)
    expt = _ConcreteCwlSc(name='sc1', type=_mk_type_sc_bragg())
    # Verify that experiment was created successfully with expected properties
    assert expt.name == 'sc1'
    assert expt.type is not None
