# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np


def test_update_pattern_d_spacing_branches(monkeypatch, capsys):
    # Arrange minimal experiment/collection using real Experiments
    from easydiffraction.experiments.experiment.base import PdExperimentBase
    from easydiffraction.experiments.experiment.instrument_mixin import InstrumentMixin
    from easydiffraction.experiments.experiments import Experiments

    class DS:
        def __init__(self, x):
            self.x = x
            self.d = None

    class Instr:
        def __init__(self):
            self.calib_d_to_tof_offset = type('P', (), {'value': 1.0})
            self.calib_d_to_tof_linear = type('P', (), {'value': 2.0})
            self.calib_d_to_tof_quad = type('P', (), {'value': 0.0})
            self.setup_wavelength = type('P', (), {'value': 1.54})

    class TypeObj:
        def __init__(self, beam_mode_value):
            self.beam_mode = type('E', (), {'value': beam_mode_value})
            self.sample_form = type('E', (), {'value': 'powder'})
            self.scattering_type = type('E', (), {'value': 'bragg'})

    class DummyExp(InstrumentMixin, PdExperimentBase):
        def __init__(self, name, beam_mode_value):
            super().__init__(name=name, type=TypeObj(beam_mode_value))
            # Replace with controlled datastore/instrument for test
            self._datastore = DS(x=np.array([1.0, 2.0, 3.0]))

        def _load_ascii_data_to_experiment(self, data_path: str) -> None:
            pass

    exps = Experiments()
    tof_exp = DummyExp('e_tof', 'time-of-flight')
    cwl_exp = DummyExp('e_cwl', 'constant wavelength')
    exps.add(experiment=tof_exp)
    exps.add(experiment=cwl_exp)

    from easydiffraction.project.project import Project

    proj = Project()
    proj.experiments = exps

    # Act TOF
    proj.update_pattern_d_spacing('e_tof')
    # Act CWL
    proj.update_pattern_d_spacing('e_cwl')

    # Assert: d arrays were computed
    assert isinstance(tof_exp.datastore.d, np.ndarray)
    assert isinstance(cwl_exp.datastore.d, np.ndarray)


def test_update_pattern_d_spacing_unsupported_prints(monkeypatch, capsys):
    # Use real Experiments and flip the mode to unsupported post-init
    from easydiffraction.experiments.experiment.base import PdExperimentBase
    from easydiffraction.experiments.experiment.instrument_mixin import InstrumentMixin
    from easydiffraction.experiments.experiments import Experiments

    class DS:
        def __init__(self):
            self.x = np.array([1.0])
            self.d = None

    class TypeObj:
        def __init__(self, beam_mode_value):
            self.beam_mode = type('E', (), {'value': beam_mode_value})
            self.sample_form = type('E', (), {'value': 'powder'})
            self.scattering_type = type('E', (), {'value': 'bragg'})

    class DummyExp(InstrumentMixin, PdExperimentBase):
        def __init__(self, name, beam_mode_value):
            super().__init__(name=name, type=TypeObj(beam_mode_value))
            self._datastore = DS()

        def _load_ascii_data_to_experiment(self, data_path: str) -> None:
            pass

    exps = Experiments()
    exp = DummyExp('e1', 'constant wavelength')
    # Flip to unsupported value after init to avoid factory issues
    exp.type.beam_mode = type('E', (), {'value': 'unsupported'})
    exps.add(experiment=exp)

    from easydiffraction.project.project import Project

    p = Project()
    p.experiments = exps

    # Act
    p.update_pattern_d_spacing('e1')

    # Assert error is reported via console/logging in the new API
    out = capsys.readouterr().out
    assert 'Unsupported beam mode' in out
