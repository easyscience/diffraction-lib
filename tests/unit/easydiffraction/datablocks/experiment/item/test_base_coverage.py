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
        assert isinstance(ex.diffrn_type, str)

    def test_diffrn_type_invalid(self):
        ex = ConcreteBase(name='ex1', type=_mk_type_powder_cwl_bragg())
        old_type = ex.diffrn_type
        ex.diffrn_type = 'nonexistent'
        assert ex.diffrn_type == old_type

    def test_show_supported_diffrn_types(self, capsys):
        ex = ConcreteBase(name='ex1', type=_mk_type_powder_cwl_bragg())
        ex.show_supported_diffrn_types()
        out = capsys.readouterr().out
        assert len(out) > 0

    def test_show_current_diffrn_type(self, capsys):
        ex = ConcreteBase(name='ex1', type=_mk_type_powder_cwl_bragg())
        ex.show_current_diffrn_type()
        out = capsys.readouterr().out
        assert ex.diffrn_type in out


class TestExperimentBaseCalculator:
    def test_calculator_auto_resolves(self):
        ex = ConcreteBase(name='ex1', type=_mk_type_powder_cwl_bragg())
        # calculator should auto-resolve on first access
        assert ex.calculator is not None

    def test_calculator_type_auto_resolves(self):
        ex = ConcreteBase(name='ex1', type=_mk_type_powder_cwl_bragg())
        ct = ex.calculator_type
        assert isinstance(ct, str)
        assert len(ct) > 0

    def test_calculator_type_invalid(self):
        ex = ConcreteBase(name='ex1', type=_mk_type_powder_cwl_bragg())
        _ = ex.calculator_type  # trigger resolve
        old = ex.calculator_type
        ex.calculator_type = 'bogus-engine'
        assert ex.calculator_type == old

    def test_show_supported_calculator_types(self, capsys):
        ex = ConcreteBase(name='ex1', type=_mk_type_powder_cwl_bragg())
        ex.show_supported_calculator_types()
        out = capsys.readouterr().out
        assert len(out) > 0

    def test_show_current_calculator_type(self, capsys):
        ex = ConcreteBase(name='ex1', type=_mk_type_powder_cwl_bragg())
        ex.show_current_calculator_type()
        out = capsys.readouterr().out
        assert ex.calculator_type in out


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
        assert isinstance(ex.linked_phases_type, str)

    def test_linked_phases_type_invalid(self):
        ex = ConcretePd(name='pd1', type=_mk_type_powder_cwl_bragg())
        old_type = ex.linked_phases_type
        ex.linked_phases_type = 'nonexistent'
        assert ex.linked_phases_type == old_type

    def test_show_supported_linked_phases_types(self, capsys):
        ex = ConcretePd(name='pd1', type=_mk_type_powder_cwl_bragg())
        ex.show_supported_linked_phases_types()
        out = capsys.readouterr().out
        assert len(out) > 0

    def test_show_current_linked_phases_type(self, capsys):
        ex = ConcretePd(name='pd1', type=_mk_type_powder_cwl_bragg())
        ex.show_current_linked_phases_type()
        out = capsys.readouterr().out
        assert ex.linked_phases_type in out


class TestPdExperimentExcludedRegions:
    def test_excluded_regions_defaults(self):
        ex = ConcretePd(name='pd1', type=_mk_type_powder_cwl_bragg())
        assert ex.excluded_regions is not None
        assert isinstance(ex.excluded_regions_type, str)

    def test_excluded_regions_type_invalid(self):
        ex = ConcretePd(name='pd1', type=_mk_type_powder_cwl_bragg())
        old_type = ex.excluded_regions_type
        ex.excluded_regions_type = 'nonexistent'
        assert ex.excluded_regions_type == old_type

    def test_show_supported_excluded_regions_types(self, capsys):
        ex = ConcretePd(name='pd1', type=_mk_type_powder_cwl_bragg())
        ex.show_supported_excluded_regions_types()
        out = capsys.readouterr().out
        assert len(out) > 0

    def test_show_current_excluded_regions_type(self, capsys):
        ex = ConcretePd(name='pd1', type=_mk_type_powder_cwl_bragg())
        ex.show_current_excluded_regions_type()
        out = capsys.readouterr().out
        assert ex.excluded_regions_type in out


class TestPdExperimentData:
    def test_data_defaults(self):
        ex = ConcretePd(name='pd1', type=_mk_type_powder_cwl_bragg())
        assert ex.data is not None
        assert isinstance(ex.data_type, str)

    def test_data_type_invalid(self):
        ex = ConcretePd(name='pd1', type=_mk_type_powder_cwl_bragg())
        old_type = ex.data_type
        ex.data_type = 'nonexistent'
        assert ex.data_type == old_type

    def test_show_supported_data_types(self, capsys):
        ex = ConcretePd(name='pd1', type=_mk_type_powder_cwl_bragg())
        ex.show_supported_data_types()
        out = capsys.readouterr().out
        assert len(out) > 0

    def test_show_current_data_type(self, capsys):
        ex = ConcretePd(name='pd1', type=_mk_type_powder_cwl_bragg())
        ex.show_current_data_type()
        out = capsys.readouterr().out
        assert ex.data_type in out


class TestPdExperimentPeak:
    def test_peak_defaults(self):
        ex = ConcretePd(name='pd1', type=_mk_type_powder_cwl_bragg())
        assert ex.peak is not None
        assert ex.peak_profile_type is not None

    def test_show_supported_peak_profile_types(self, capsys):
        ex = ConcretePd(name='pd1', type=_mk_type_powder_cwl_bragg())
        ex.show_supported_peak_profile_types()
        out = capsys.readouterr().out
        assert len(out) > 0

    def test_show_current_peak_profile_type(self, capsys):
        ex = ConcretePd(name='pd1', type=_mk_type_powder_cwl_bragg())
        ex.show_current_peak_profile_type()
        out = capsys.readouterr().out
        assert str(ex.peak_profile_type) in out
