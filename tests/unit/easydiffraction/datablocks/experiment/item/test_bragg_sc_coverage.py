# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Additional tests for single-crystal experiment classes."""

import numpy as np
import pytest

from easydiffraction.datablocks.experiment.categories.experiment_type import ExperimentType
from easydiffraction.datablocks.experiment.item.bragg_sc import CwlScExperiment
from easydiffraction.datablocks.experiment.item.bragg_sc import TofScExperiment
from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import RadiationProbeEnum
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
from easydiffraction.utils.logging import Logger


def _mk_type_sc_cwl():
    et = ExperimentType()
    et._set_sample_form(SampleFormEnum.SINGLE_CRYSTAL.value)
    et._set_beam_mode(BeamModeEnum.CONSTANT_WAVELENGTH.value)
    et._set_radiation_probe(RadiationProbeEnum.NEUTRON.value)
    et._set_scattering_type(ScatteringTypeEnum.BRAGG.value)
    return et


def _mk_type_sc_tof():
    et = ExperimentType()
    et._set_sample_form(SampleFormEnum.SINGLE_CRYSTAL.value)
    et._set_beam_mode(BeamModeEnum.TIME_OF_FLIGHT.value)
    et._set_radiation_probe(RadiationProbeEnum.NEUTRON.value)
    et._set_scattering_type(ScatteringTypeEnum.BRAGG.value)
    return et


class TestCwlScExperiment:
    def test_init(self):
        ex = CwlScExperiment(name='cwl_sc', type=_mk_type_sc_cwl())
        assert ex.name == 'cwl_sc'
        assert ex.type.sample_form.value == SampleFormEnum.SINGLE_CRYSTAL.value

    def test_type_info(self):
        assert CwlScExperiment.type_info.tag == 'bragg-sc-cwl'

    def test_load_ascii_5col(self, tmp_path):
        ex = CwlScExperiment(name='cwl_sc', type=_mk_type_sc_cwl())
        data = np.column_stack([
            np.array([1, 0, 0]),
            np.array([0, 1, 0]),
            np.array([0, 0, 1]),
            np.array([100.0, 200.0, 300.0]),
            np.array([10.0, 20.0, 30.0]),
        ])
        p = tmp_path / 'sc_data.dat'
        np.savetxt(p, data)
        n = ex._load_ascii_data_to_experiment(str(p))
        assert n == 3

    def test_load_ascii_too_few_columns(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.RAISE, raising=True)
        ex = CwlScExperiment(name='cwl_sc', type=_mk_type_sc_cwl())
        data = np.column_stack([np.array([1, 2, 3]), np.array([4, 5, 6])])
        p = tmp_path / 'bad.dat'
        np.savetxt(p, data)
        with pytest.raises(ValueError, match='at least 5 columns'):
            ex._load_ascii_data_to_experiment(str(p))

    def test_switchable_categories(self):
        ex = CwlScExperiment(name='cwl_sc', type=_mk_type_sc_cwl())
        # extinction
        assert ex.extinction is not None
        assert isinstance(ex.extinction_type, str)
        # linked crystal
        assert ex.linked_crystal is not None
        assert isinstance(ex.linked_crystal_type, str)
        # instrument
        assert ex.instrument is not None
        assert isinstance(ex.instrument_type, str)
        # data
        assert ex.data is not None
        assert isinstance(ex.data_type, str)

    def test_extinction_type_invalid(self):
        ex = CwlScExperiment(name='cwl_sc', type=_mk_type_sc_cwl())
        old = ex.extinction_type
        ex.extinction_type = 'bogus'
        assert ex.extinction_type == old

    def test_linked_crystal_type_invalid(self):
        ex = CwlScExperiment(name='cwl_sc', type=_mk_type_sc_cwl())
        old = ex.linked_crystal_type
        ex.linked_crystal_type = 'bogus'
        assert ex.linked_crystal_type == old

    def test_show_supported_extinction_types(self, capsys):
        ex = CwlScExperiment(name='cwl_sc', type=_mk_type_sc_cwl())
        ex.show_supported_extinction_types()
        out = capsys.readouterr().out
        assert len(out) > 0

    def test_show_current_extinction_type(self, capsys):
        ex = CwlScExperiment(name='cwl_sc', type=_mk_type_sc_cwl())
        ex.show_current_extinction_type()
        out = capsys.readouterr().out
        assert ex.extinction_type in out

    def test_show_supported_linked_crystal_types(self, capsys):
        ex = CwlScExperiment(name='cwl_sc', type=_mk_type_sc_cwl())
        ex.show_supported_linked_crystal_types()
        out = capsys.readouterr().out
        assert len(out) > 0

    def test_show_current_linked_crystal_type(self, capsys):
        ex = CwlScExperiment(name='cwl_sc', type=_mk_type_sc_cwl())
        ex.show_current_linked_crystal_type()
        out = capsys.readouterr().out
        assert ex.linked_crystal_type in out

    def test_show_supported_instrument_types(self, capsys):
        ex = CwlScExperiment(name='cwl_sc', type=_mk_type_sc_cwl())
        ex.show_supported_instrument_types()
        out = capsys.readouterr().out
        assert len(out) > 0

    def test_show_current_instrument_type(self, capsys):
        ex = CwlScExperiment(name='cwl_sc', type=_mk_type_sc_cwl())
        ex.show_current_instrument_type()
        out = capsys.readouterr().out
        assert ex.instrument_type in out

    def test_show_supported_data_types(self, capsys):
        ex = CwlScExperiment(name='cwl_sc', type=_mk_type_sc_cwl())
        ex.show_supported_data_types()
        out = capsys.readouterr().out
        assert len(out) > 0

    def test_show_current_data_type(self, capsys):
        ex = CwlScExperiment(name='cwl_sc', type=_mk_type_sc_cwl())
        ex.show_current_data_type()
        out = capsys.readouterr().out
        assert ex.data_type in out


class TestTofScExperiment:
    def test_init(self):
        ex = TofScExperiment(name='tof_sc', type=_mk_type_sc_tof())
        assert ex.name == 'tof_sc'
        assert ex.type.beam_mode.value == BeamModeEnum.TIME_OF_FLIGHT.value

    def test_type_info(self):
        assert TofScExperiment.type_info.tag == 'bragg-sc-tof'

    def test_load_ascii_6col(self, tmp_path):
        ex = TofScExperiment(name='tof_sc', type=_mk_type_sc_tof())
        data = np.column_stack([
            np.array([1, 0, 0]),
            np.array([0, 1, 0]),
            np.array([0, 0, 1]),
            np.array([100.0, 200.0, 300.0]),
            np.array([10.0, 20.0, 30.0]),
            np.array([1.54, 1.54, 1.54]),
        ])
        p = tmp_path / 'tof_sc_data.dat'
        np.savetxt(p, data)
        n = ex._load_ascii_data_to_experiment(str(p))
        assert n == 3

    def test_load_ascii_too_few_columns(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.RAISE, raising=True)
        ex = TofScExperiment(name='tof_sc', type=_mk_type_sc_tof())
        data = np.column_stack([
            np.array([1, 2]),
            np.array([0, 1]),
            np.array([0, 0]),
            np.array([100.0, 200.0]),
            np.array([10.0, 20.0]),
        ])
        p = tmp_path / 'bad.dat'
        np.savetxt(p, data)
        with pytest.raises(ValueError, match='at least 6 columns'):
            ex._load_ascii_data_to_experiment(str(p))

    def test_load_ascii_nonexistent_file(self, monkeypatch):
        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.RAISE, raising=True)
        ex = TofScExperiment(name='tof_sc', type=_mk_type_sc_tof())
        with pytest.raises(OSError, match='No such file'):
            ex._load_ascii_data_to_experiment('/no/such/file.dat')
