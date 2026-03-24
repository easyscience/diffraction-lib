# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np
import pytest

from easydiffraction.datablocks.experiment.categories.background.factory import BackgroundFactory
from easydiffraction.datablocks.experiment.categories.experiment_type import ExperimentType
from easydiffraction.datablocks.experiment.item.bragg_pd import BraggPdExperiment
from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import RadiationProbeEnum
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum


def _mk_type_powder_cwl_bragg():
    et = ExperimentType()
    et.sample_form = SampleFormEnum.POWDER.value
    et.beam_mode = BeamModeEnum.CONSTANT_WAVELENGTH.value
    et.radiation_probe = RadiationProbeEnum.NEUTRON.value
    et.scattering_type = ScatteringTypeEnum.BRAGG.value
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

    # Case 3: invalid shape -> currently triggers an exception (IndexError on shape[1])
    pinv = tmp_path / 'invalid.dat'
    np.savetxt(pinv, np.ones((5, 1)))
    with pytest.raises(Exception):
        expt._load_ascii_data_to_experiment(str(pinv))
