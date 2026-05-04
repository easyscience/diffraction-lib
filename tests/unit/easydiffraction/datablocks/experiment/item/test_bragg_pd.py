# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np
import pytest

from easydiffraction.analysis.calculators.base import PowderReflnRecord
from easydiffraction.datablocks.experiment.categories.background.factory import BackgroundFactory
from easydiffraction.datablocks.experiment.categories.data.refln_pd import PowderCwlReflnData
from easydiffraction.datablocks.experiment.categories.data.refln_pd import PowderTofReflnData
from easydiffraction.datablocks.experiment.categories.experiment_type import ExperimentType
from easydiffraction.datablocks.experiment.item.bragg_pd import BraggPdExperiment
from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import RadiationProbeEnum
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum


def _mk_type_powder_cwl_bragg():
    et = ExperimentType()
    et._set_sample_form(SampleFormEnum.POWDER.value)
    et._set_beam_mode(BeamModeEnum.CONSTANT_WAVELENGTH.value)
    et._set_radiation_probe(RadiationProbeEnum.NEUTRON.value)
    et._set_scattering_type(ScatteringTypeEnum.BRAGG.value)
    return et


def _mk_type_powder_tof_bragg():
    et = ExperimentType()
    et._set_sample_form(SampleFormEnum.POWDER.value)
    et._set_beam_mode(BeamModeEnum.TIME_OF_FLIGHT.value)
    et._set_radiation_probe(RadiationProbeEnum.NEUTRON.value)
    et._set_scattering_type(ScatteringTypeEnum.BRAGG.value)
    return et


def test_background_defaults_and_change():
    expt = BraggPdExperiment(name='e1', type=_mk_type_powder_cwl_bragg())
    # default background type
    assert expt.background_type == BackgroundFactory.default_tag()

    # change to a supported type
    expt.background_type = 'chebyshev'
    assert expt.background_type == 'chebyshev'

    # unknown type keeps previous type and prints warnings (no raise)
    expt.background_type = 'not-a-type'  # invalid string
    assert expt.background_type == 'chebyshev'


def test_load_ascii_data_rounds_and_defaults_sy(tmp_path: pytest.TempPathFactory):
    expt = BraggPdExperiment(name='e1', type=_mk_type_powder_cwl_bragg())

    # Case 1: provide only two columns -> sy defaults to sqrt(y) and min clipped to 1.0
    p = tmp_path / 'data2col.dat'
    x = np.array([1.123456, 2.987654, 3.5])
    y = np.array([0.0, 4.0, 9.0])
    data = np.column_stack([x, y])
    np.savetxt(p, data)

    expt._load_ascii_data_to_experiment(str(p))

    # x rounded to 4 decimals
    assert np.allclose(expt.data.x, np.round(x, 4))
    # sy = sqrt(y) with values < 1e-4 replaced by 1.0
    expected_sy = np.sqrt(y)
    expected_sy = np.where(expected_sy < 1e-4, 1.0, expected_sy)
    assert np.allclose(expt.data.intensity_meas_su, expected_sy)
    # Check that data array shapes match
    assert len(expt.data.x) == len(x)

    # Case 2: three columns provided -> sy taken from file and clipped
    p3 = tmp_path / 'data3col.dat'
    sy = np.array([0.0, 1e-5, 0.2])  # first two should clip to 1.0
    data3 = np.column_stack([x, y, sy])
    np.savetxt(p3, data3)
    expt._load_ascii_data_to_experiment(str(p3))
    expected_sy3 = np.where(sy < 1e-4, 1.0, sy)
    assert np.allclose(expt.data.intensity_meas_su, expected_sy3)

    # Case 3: invalid shape -> currently triggers an IndexError on shape[1]
    pinv = tmp_path / 'invalid.dat'
    np.savetxt(pinv, np.ones((5, 1)))
    with pytest.raises(IndexError, match='tuple index out of range'):
        expt._load_ascii_data_to_experiment(str(pinv))


def test_bragg_pd_experiment_creates_beam_mode_specific_refln_collection():
    cwl_experiment = BraggPdExperiment(name='cwl', type=_mk_type_powder_cwl_bragg())
    tof_experiment = BraggPdExperiment(name='tof', type=_mk_type_powder_tof_bragg())

    assert isinstance(cwl_experiment.refln, PowderCwlReflnData)
    assert isinstance(tof_experiment.refln, PowderTofReflnData)


def test_pd_data_update_populates_and_clears_refln():
    from collections import UserDict

    class FakeStructures(UserDict):
        @property
        def names(self):
            return list(self.data.keys())

    class FakeCalculator:
        name = 'fake'

        def __init__(self):
            self.return_records = True

        def calculate_pattern(self, structure, experiment, *, called_by_minimizer=False):
            del experiment, called_by_minimizer
            return structure.pattern

        def last_powder_refln_records(self, structure, experiment, *, phase_id):
            del experiment, phase_id
            if not self.return_records:
                return None
            return structure.records

    class FakeStructure:
        def __init__(self, name, pattern, records):
            self.name = name
            self.pattern = pattern
            self.records = records

    experiment = BraggPdExperiment(name='powder', type=_mk_type_powder_cwl_bragg())
    experiment.linked_phases.create(id='phase_a', scale=2.0)
    experiment.linked_phases.create(id='phase_b', scale=3.0)
    experiment.data._create_items_set_xcoord_and_id(np.array([10.0, 20.0, 30.0]))
    experiment.data._set_intensity_meas(np.array([100.0, 110.0, 120.0]))

    structures = FakeStructures({
        'phase_a': FakeStructure(
            'phase_a',
            np.array([1.0, 2.0, 3.0]),
            [
                PowderReflnRecord(
                    phase_id='phase_a',
                    d_spacing=2.1,
                    sin_theta_over_lambda=0.25,
                    index_h=1,
                    index_k=0,
                    index_l=1,
                    f_calc=3.0,
                    f_squared_calc=9.0,
                    two_theta=14.5,
                )
            ],
        ),
        'phase_b': FakeStructure(
            'phase_b',
            np.array([4.0, 5.0, 6.0]),
            [
                PowderReflnRecord(
                    phase_id='phase_b',
                    d_spacing=1.8,
                    sin_theta_over_lambda=0.28,
                    index_h=2,
                    index_k=1,
                    index_l=0,
                    f_calc=4.0,
                    f_squared_calc=16.0,
                    two_theta=18.5,
                )
            ],
        ),
    })
    project = type('Project', (), {'structures': structures})()
    experiments = type('Experiments', (), {'_parent': project})()
    experiment._parent = experiments
    experiment._calculator = FakeCalculator()

    experiment.data._update()

    np.testing.assert_allclose(experiment.data.intensity_calc, np.array([14.0, 19.0, 24.0]))
    np.testing.assert_array_equal(experiment.refln.phase_id, np.array(['phase_a', 'phase_b']))
    np.testing.assert_allclose(experiment.refln.two_theta, np.array([14.5, 18.5]))

    experiment._calculator.return_records = False
    experiment.data._update()

    assert len(experiment.refln._items) == 0
