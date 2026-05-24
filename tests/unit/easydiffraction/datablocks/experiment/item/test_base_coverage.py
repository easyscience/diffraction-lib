# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for ExperimentBase and PdExperimentBase switchable categories."""

from easydiffraction.datablocks.experiment.categories.experiment_type import ExperimentType
from easydiffraction.datablocks.experiment.item.base import ExperimentBase
from easydiffraction.datablocks.experiment.item.base import PdExperimentBase
from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import RadiationProbeEnum
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _mk_type_powder_cwl_bragg():
    et = ExperimentType()
    et._set_sample_form(SampleFormEnum.POWDER.value)
    et._set_beam_mode(BeamModeEnum.CONSTANT_WAVELENGTH.value)
    et._set_radiation_probe(RadiationProbeEnum.NEUTRON.value)
    et._set_scattering_type(ScatteringTypeEnum.BRAGG.value)
    return et


class ConcretePd(PdExperimentBase):
    def _load_ascii_data_to_experiment(self, data_path: str) -> int:
        return 0


class ConcreteBase(ExperimentBase):
    def _load_ascii_data_to_experiment(self, data_path: str) -> int:
        return 0


# ------------------------------------------------------------------
# ExperimentBase
# ------------------------------------------------------------------


class TestExperimentBaseName:
    def test_name_getter(self):
        ex = ConcreteBase(name='ex1', type=_mk_type_powder_cwl_bragg())
        assert ex.name == 'ex1'

    def test_name_setter(self):
        ex = ConcreteBase(name='ex1', type=_mk_type_powder_cwl_bragg())
        ex.name = 'ex2'
        assert ex.name == 'ex2'

    def test_type_property(self):
        et = _mk_type_powder_cwl_bragg()
        ex = ConcreteBase(name='ex1', type=et)
        assert ex.type is et


class TestExperimentBaseDiffrn:
    def test_diffrn_defaults(self):
        ex = ConcreteBase(name='ex1', type=_mk_type_powder_cwl_bragg())
        assert ex.diffrn is not None


class TestExperimentBaseCalculator:
    def test_calculator_auto_resolves(self):
        ex = ConcreteBase(name='ex1', type=_mk_type_powder_cwl_bragg())
        # calculator should auto-resolve on first access
        assert ex.calculator.calculator is not None

    def test_calculator_type_auto_resolves(self):
        ex = ConcreteBase(name='ex1', type=_mk_type_powder_cwl_bragg())
        ct = ex.calculator.type
        assert isinstance(ct, str)
        assert len(ct) > 0

    def test_calculator_type_invalid(self):
        import pytest

        ex = ConcreteBase(name='ex1', type=_mk_type_powder_cwl_bragg())
        _ = ex.calculator.calculator  # trigger resolve
        old = ex.calculator.type
        with pytest.raises(ValueError, match='Unsupported calculator'):
            ex.calculator.type = 'bogus-engine'
        assert ex.calculator.type == old

    def test_show_calculator_types(self, capsys):
        ex = ConcreteBase(name='ex1', type=_mk_type_powder_cwl_bragg())
        ex.calculator.show_supported()
        out = capsys.readouterr().out
        assert len(out) > 0

    def test_show_calculator_types_includes_current(self, capsys):
        ex = ConcreteBase(name='ex1', type=_mk_type_powder_cwl_bragg())
        ex.calculator.show_supported()
        out = capsys.readouterr().out
        assert ex.calculator.type in out


class TestExperimentBaseAsCif:
    def test_as_cif_returns_str(self):
        ex = ConcreteBase(name='ex1', type=_mk_type_powder_cwl_bragg())
        cif = ex.as_cif
        assert isinstance(cif, str)

    def test_show_as_cif(self, capsys):
        ex = ConcreteBase(name='ex1', type=_mk_type_powder_cwl_bragg())
        ex.show_as_cif()
        out = capsys.readouterr().out
        assert 'ex1' in out


# ------------------------------------------------------------------
# PdExperimentBase
# ------------------------------------------------------------------


class TestPdExperimentLinkedPhases:
    def test_linked_phases_defaults(self):
        ex = ConcretePd(name='pd1', type=_mk_type_powder_cwl_bragg())
        assert ex.linked_phases is not None


class TestPdExperimentExcludedRegions:
    def test_excluded_regions_defaults(self):
        ex = ConcretePd(name='pd1', type=_mk_type_powder_cwl_bragg())
        assert ex.excluded_regions is not None


class TestPdExperimentData:
    def test_data_defaults(self):
        ex = ConcretePd(name='pd1', type=_mk_type_powder_cwl_bragg())
        assert ex.data is not None


class TestPdExperimentPeak:
    def test_peak_defaults(self):
        ex = ConcretePd(name='pd1', type=_mk_type_powder_cwl_bragg())
        assert ex.peak is not None
        assert ex.peak.type is not None

    def test_show_peak_profile_types(self, capsys):
        ex = ConcretePd(name='pd1', type=_mk_type_powder_cwl_bragg())
        ex.peak.show_supported()
        out = capsys.readouterr().out
        assert len(out) > 0

    def test_show_peak_profile_types_includes_current(self, capsys):
        ex = ConcretePd(name='pd1', type=_mk_type_powder_cwl_bragg())
        ex.peak.show_supported()
        out = capsys.readouterr().out
        assert str(ex.peak.type) in out
