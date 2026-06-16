# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for ExperimentBase and PdExperimentBase switchable categories."""

from easydiffraction.datablocks.experiment.categories.experiment_type import ExperimentType
from easydiffraction.datablocks.experiment.item.base import ExperimentBase
from easydiffraction.datablocks.experiment.item.base import PdExperimentBase
from easydiffraction.datablocks.experiment.item.base import ScExperimentBase
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
        ex = ConcreteBase(name='ex1', experiment_type=_mk_type_powder_cwl_bragg())
        assert ex.name == 'ex1'

    def test_name_setter(self):
        ex = ConcreteBase(name='ex1', experiment_type=_mk_type_powder_cwl_bragg())
        ex.name = 'ex2'
        assert ex.name == 'ex2'

    def test_type_property(self):
        et = _mk_type_powder_cwl_bragg()
        ex = ConcreteBase(name='ex1', experiment_type=et)
        assert ex.experiment_type is et


class TestExperimentBaseDiffrn:
    def test_diffrn_defaults(self):
        ex = ConcreteBase(name='ex1', experiment_type=_mk_type_powder_cwl_bragg())
        assert ex.diffrn is not None


class TestExperimentBaseCalculator:
    def test_calculator_auto_resolves(self):
        ex = ConcreteBase(name='ex1', experiment_type=_mk_type_powder_cwl_bragg())
        # calculator should auto-resolve on first access
        assert ex.calculator.calculator is not None

    def test_calculator_type_auto_resolves(self):
        ex = ConcreteBase(name='ex1', experiment_type=_mk_type_powder_cwl_bragg())
        ct = ex.calculator.type
        assert isinstance(ct, str)
        assert len(ct) > 0

    def test_calculator_type_invalid(self):
        import pytest

        ex = ConcreteBase(name='ex1', experiment_type=_mk_type_powder_cwl_bragg())
        _ = ex.calculator.calculator  # trigger resolve
        old = ex.calculator.type
        with pytest.raises(ValueError, match='Unsupported calculator'):
            ex.calculator.type = 'bogus-engine'
        assert ex.calculator.type == old

    def test_show_calculator_types(self, capsys):
        ex = ConcreteBase(name='ex1', experiment_type=_mk_type_powder_cwl_bragg())
        ex.calculator.show_supported()
        out = capsys.readouterr().out
        assert len(out) > 0

    def test_show_calculator_types_includes_current(self, capsys):
        ex = ConcreteBase(name='ex1', experiment_type=_mk_type_powder_cwl_bragg())
        ex.calculator.show_supported()
        out = capsys.readouterr().out
        assert ex.calculator.type in out


class TestExperimentBaseAsCif:
    def test_as_cif_returns_str(self):
        ex = ConcreteBase(name='ex1', experiment_type=_mk_type_powder_cwl_bragg())
        cif = ex.as_cif
        assert isinstance(cif, str)

    def test_show_as_text(self, capsys):
        ex = ConcreteBase(name='ex1', experiment_type=_mk_type_powder_cwl_bragg())
        ex.show_as_text()
        out = capsys.readouterr().out
        assert 'ex1' in out


# ------------------------------------------------------------------
# PdExperimentBase
# ------------------------------------------------------------------


class TestPdExperimentLinkedStructures:
    def test_linked_structures_defaults(self):
        ex = ConcretePd(name='pd1', experiment_type=_mk_type_powder_cwl_bragg())
        assert ex.linked_structures is not None


class TestPdExperimentExcludedRegions:
    def test_excluded_regions_defaults(self):
        ex = ConcretePd(name='pd1', experiment_type=_mk_type_powder_cwl_bragg())
        assert ex.excluded_regions is not None


class TestPdExperimentData:
    def test_data_defaults(self):
        ex = ConcretePd(name='pd1', experiment_type=_mk_type_powder_cwl_bragg())
        assert ex.data is not None


class TestPdExperimentPeak:
    def test_peak_defaults(self):
        ex = ConcretePd(name='pd1', experiment_type=_mk_type_powder_cwl_bragg())
        assert ex.peak is not None
        assert ex.peak.type is not None

    def test_show_peak_profile_types(self, capsys):
        ex = ConcretePd(name='pd1', experiment_type=_mk_type_powder_cwl_bragg())
        ex.peak.show_supported()
        out = capsys.readouterr().out
        assert len(out) > 0

    def test_show_peak_profile_types_uses_context_aliases(self, capsys):
        ex = ConcretePd(name='pd1', experiment_type=_mk_type_powder_cwl_bragg())
        ex.peak.show_supported()
        out = capsys.readouterr().out
        assert 'Alias' not in out
        assert 'cwl-pseudo-voigt' not in out
        assert 'pseudo-voigt' in out
        assert 'pseudo-voigt + berar-baldinozzi asymmetry' in out


# ------------------------------------------------------------------
# Additional coverage helpers
# ------------------------------------------------------------------


def _mk_type_sc_cwl_bragg():
    et = ExperimentType()
    et._set_sample_form(SampleFormEnum.SINGLE_CRYSTAL.value)
    et._set_beam_mode(BeamModeEnum.CONSTANT_WAVELENGTH.value)
    et._set_radiation_probe(RadiationProbeEnum.NEUTRON.value)
    et._set_scattering_type(ScatteringTypeEnum.BRAGG.value)
    return et


class ConcreteSc(ScExperimentBase):
    def _load_ascii_data_to_experiment(self, data_path: str) -> int:
        return 0


def _mk_bragg_pd(name='bpd1'):
    # Concrete Bragg powder experiment; exposes the background category
    # whose replacement logic lives on ExperimentBase.
    from easydiffraction.datablocks.experiment.item.bragg_pd import BraggPdExperiment

    return BraggPdExperiment(name=name, experiment_type=_mk_type_powder_cwl_bragg())


# ------------------------------------------------------------------
# Module-level helper: intensity_category_for
# ------------------------------------------------------------------


class TestIntensityCategoryFor:
    def test_uses_resolver_method_when_present(self):
        from easydiffraction.datablocks.experiment.item.base import intensity_category_for

        sentinel = object()

        class WithResolver:
            def _intensity_category(self):
                return sentinel

        assert intensity_category_for(WithResolver()) is sentinel

    def test_falls_back_to_data_attribute(self):
        from easydiffraction.datablocks.experiment.item.base import intensity_category_for

        data = object()

        class WithData:
            pass

        obj = WithData()
        obj.data = data
        assert intensity_category_for(obj) is data

    def test_falls_back_to_refln_attribute(self):
        from easydiffraction.datablocks.experiment.item.base import intensity_category_for

        refln = object()

        class WithRefln:
            pass

        obj = WithRefln()
        obj.refln = refln
        assert intensity_category_for(obj) is refln

    def test_raises_attribute_error_when_no_category(self):
        import pytest

        from easydiffraction.datablocks.experiment.item.base import intensity_category_for

        class Bare:
            name = 'bare-exp'

        with pytest.raises(AttributeError, match="'bare-exp' has no intensity category"):
            intensity_category_for(Bare())

    def test_raises_uses_class_name_when_name_missing(self):
        import pytest

        from easydiffraction.datablocks.experiment.item.base import intensity_category_for

        class Nameless:
            pass

        with pytest.raises(AttributeError, match='Nameless'):
            intensity_category_for(Nameless())


# ------------------------------------------------------------------
# measured_range (backed by data_range)
# ------------------------------------------------------------------


class TestMeasuredRange:
    def test_calc_range_is_nan_without_data_or_wavelength(self):
        # measured_range now reflects data_range: with no measured scan
        # and no wavelength to project a default, the calc bounds are the
        # unset NaN sentinel rather than None. (Grid-axis helpers moved to
        # the data_range category; see its own unit tests.)
        import math

        ex = ConcretePd(name='pd1', experiment_type=_mk_type_powder_cwl_bragg())
        range_min, range_max, increment = ex.measured_range
        assert math.isnan(range_min)
        assert math.isnan(range_max)
        assert math.isnan(increment)

    def test_uniform_grid_reports_increment(self):
        import numpy as np

        ex = ConcretePd(name='pd1', experiment_type=_mk_type_powder_cwl_bragg())
        ex.data._create_items_set_xcoord_and_id(np.array([10.0, 20.0, 30.0, 40.0]))

        range_min, range_max, increment = ex.measured_range
        assert range_min == 10.0
        assert range_max == 40.0
        assert increment == 10.0

    def test_single_point_has_no_increment(self):
        import numpy as np

        ex = ConcretePd(name='pd1', experiment_type=_mk_type_powder_cwl_bragg())
        ex.data._create_items_set_xcoord_and_id(np.array([15.0]))

        assert ex.measured_range == (15.0, 15.0, None)

    def test_non_uniform_grid_drops_increment(self):
        import numpy as np

        ex = ConcretePd(name='pd1', experiment_type=_mk_type_powder_cwl_bragg())
        ex.data._create_items_set_xcoord_and_id(np.array([0.0, 1.0, 9.0, 10.0]))

        range_min, range_max, increment = ex.measured_range
        assert range_min == 0.0
        assert range_max == 10.0
        assert increment is None


# ------------------------------------------------------------------
# ExperimentBase._intensity_category and abstract data loader
# ------------------------------------------------------------------


class TestExperimentBaseIntensityCategory:
    def test_base_intensity_category_raises(self):
        import pytest

        ex = ConcreteBase(name='ex1', experiment_type=_mk_type_powder_cwl_bragg())
        with pytest.raises(AttributeError, match="'ex1' has no intensity category"):
            ex._intensity_category()

    def test_abstract_loader_raises_not_implemented(self):
        import pytest

        from easydiffraction.datablocks.experiment.item.base import ExperimentBase

        ex = ConcreteBase(name='ex1', experiment_type=_mk_type_powder_cwl_bragg())
        with pytest.raises(NotImplementedError):
            ExperimentBase._load_ascii_data_to_experiment(ex, 'some/path')


# ------------------------------------------------------------------
# Calculator swap paths
# ------------------------------------------------------------------


class TestSwapCalculator:
    def test_unsupported_strict_false_warns_and_keeps(self, monkeypatch):
        from easydiffraction.datablocks.experiment.item import base as item_base

        ex = ConcreteBase(name='ex1', experiment_type=_mk_type_powder_cwl_bragg())
        _ = ex.calculator.calculator  # resolve
        current = ex.calculator.type

        warnings: list[str] = []
        monkeypatch.setattr(item_base.log, 'warning', warnings.append)
        ex._swap_calculator('bogus-engine', announce=False, strict=False)

        assert len(warnings) == 1
        assert 'Unsupported calculator' in warnings[0]
        assert ex.calculator.type == current

    def test_already_set_announces(self, capsys):
        ex = ConcreteBase(name='ex1', experiment_type=_mk_type_powder_cwl_bragg())
        _ = ex.calculator.calculator  # resolve
        current = ex.calculator.type
        capsys.readouterr()

        ex._swap_calculator(current, announce=True)

        out = capsys.readouterr().out
        assert 'already set to' in out
        assert ex.calculator.type == current

    def test_already_set_silent_when_announce_false(self, capsys):
        ex = ConcreteBase(name='ex1', experiment_type=_mk_type_powder_cwl_bragg())
        _ = ex.calculator.calculator  # resolve
        current = ex.calculator.type
        capsys.readouterr()

        ex._swap_calculator(current, announce=False)

        assert capsys.readouterr().out == ''


# ------------------------------------------------------------------
# _resolve_calculator fallback and _supported_calculator_tags
# ------------------------------------------------------------------


class TestResolveCalculatorFallback:
    def test_falls_back_to_first_supported_when_default_unsupported(self, monkeypatch):
        ex = ConcreteBase(name='ex1', experiment_type=_mk_type_powder_cwl_bragg())

        # Force the default tag to be unsupported so the fallback to the
        # first supported tag is exercised.
        supported = ex._supported_calculator_tags()
        assert supported  # sanity: at least one importable engine
        monkeypatch.setattr(ex, '_default_calculator_tag', lambda: 'not-a-real-engine')

        ex._calculator = None
        ex._resolve_calculator()

        assert ex.calculator.type == supported[0]

    def test_supported_tags_returns_all_when_no_support_constraint(self, monkeypatch):
        from easydiffraction.analysis.calculators.factory import CalculatorFactory

        ex = ConcreteBase(name='ex1', experiment_type=_mk_type_powder_cwl_bragg())
        # ConcreteBase has neither _data nor _refln, so support category
        # is None and all importable tags are returned unfiltered.
        assert ex._calculator_support_category() is None
        assert ex._supported_calculator_tags() == CalculatorFactory.supported_tags()

    def test_supported_tags_returns_all_when_support_lacks_calculators(self, monkeypatch):
        from easydiffraction.analysis.calculators.factory import CalculatorFactory

        ex = ConcretePd(name='pd1', experiment_type=_mk_type_powder_cwl_bragg())

        class NoSupport:
            calculator_support = None

        # Support category present but without a calculator constraint:
        # the filter branch is skipped and all available tags returned.
        support = NoSupport()
        monkeypatch.setattr(ex, '_calculator_support_category', lambda: support)
        assert ex._supported_calculator_tags() == CalculatorFactory.supported_tags()


# ------------------------------------------------------------------
# Background replacement paths
# ------------------------------------------------------------------


class TestReplaceBackground:
    def test_unsupported_strict_false_warns_and_keeps(self, monkeypatch):
        from easydiffraction.datablocks.experiment.item import base as item_base

        ex = _mk_bragg_pd()
        original = ex.background.type

        warnings: list[str] = []
        monkeypatch.setattr(item_base.log, 'warning', warnings.append)
        ex._replace_background('bogus-background', announce=False, strict=False)

        assert any('Unsupported background type' in w for w in warnings)
        assert ex.background.type == original

    def test_unsupported_strict_raises(self):
        import pytest

        ex = _mk_bragg_pd()
        with pytest.raises(ValueError, match='Unsupported background type'):
            ex._replace_background('bogus-background', announce=False, strict=True)

    def test_same_type_announces_already_set(self, capsys):
        ex = _mk_bragg_pd()
        current = ex.background.type
        capsys.readouterr()

        ex._replace_background(current, announce=True)

        out = capsys.readouterr().out
        assert 'already set to' in out

    def test_switch_warns_about_discarded_points(self, monkeypatch):
        from easydiffraction.datablocks.experiment.categories.background.factory import (
            BackgroundFactory,
        )
        from easydiffraction.datablocks.experiment.item import base as item_base

        ex = _mk_bragg_pd()
        tags = [
            k.type_info.tag
            for k in BackgroundFactory.supported_for(
                **ex._supported_filters_for(ex.background),
            )
        ]
        other = next(t for t in tags if t != ex.background.type)

        # Put an existing background point in so the discard branch runs.
        ex.background.create(id='1', position=10.0, intensity=1.0)
        assert len(ex.background) > 0

        warnings: list[str] = []
        monkeypatch.setattr(item_base.log, 'warning', warnings.append)
        ex._replace_background(other, announce=True)

        assert any('discards' in w for w in warnings)
        assert ex.background.type == other

    def test_silent_switch_emits_no_output_or_warning(self, monkeypatch, capsys):
        from easydiffraction.datablocks.experiment.categories.background.factory import (
            BackgroundFactory,
        )
        from easydiffraction.datablocks.experiment.item import base as item_base

        ex = _mk_bragg_pd()
        tags = [
            k.type_info.tag
            for k in BackgroundFactory.supported_for(
                **ex._supported_filters_for(ex.background),
            )
        ]
        other = next(t for t in tags if t != ex.background.type)

        ex.background.create(id='1', position=10.0, intensity=1.0)
        capsys.readouterr()

        warnings: list[str] = []
        monkeypatch.setattr(item_base.log, 'warning', warnings.append)
        ex._replace_background(other, announce=False)

        assert warnings == []
        assert capsys.readouterr().out == ''
        assert ex.background.type == other


# ------------------------------------------------------------------
# Extinction replacement (single-crystal)
# ------------------------------------------------------------------


class TestReplaceExtinction:
    def test_replace_extinction_same_type_succeeds(self, capsys):
        ex = ConcreteSc(name='sc1', experiment_type=_mk_type_sc_cwl_bragg())
        current = ex.extinction.type

        ex._replace_extinction(current, announce=True)

        out = capsys.readouterr().out
        assert 'Extinction type changed to' in out
        assert ex.extinction.type == current
        assert ex.extinction._parent is ex

    def test_replace_extinction_unsupported_strict_false_warns(self, monkeypatch):
        from easydiffraction.datablocks.experiment.item import base as item_base

        ex = ConcreteSc(name='sc1', experiment_type=_mk_type_sc_cwl_bragg())
        original = ex.extinction.type

        warnings: list[str] = []
        monkeypatch.setattr(item_base.log, 'warning', warnings.append)
        ex._replace_extinction('bogus-extinction', announce=False, strict=False)

        assert any('Unsupported extinction type' in w for w in warnings)
        assert ex.extinction.type == original

    def test_replace_extinction_unsupported_strict_raises(self):
        import pytest

        ex = ConcreteSc(name='sc1', experiment_type=_mk_type_sc_cwl_bragg())
        with pytest.raises(ValueError, match='Unsupported extinction type'):
            ex._replace_extinction('bogus-extinction', announce=False, strict=True)

    def test_restore_switchable_types_reads_extinction(self):
        import gemmi

        ex = ConcreteSc(name='sc1', experiment_type=_mk_type_sc_cwl_bragg())

        cif = 'data_sc1\n_extinction.type becker-coppens\n'
        block = gemmi.cif.read_string(cif).sole_block()

        # Must not raise and keeps the (only) supported extinction type.
        ex._restore_switchable_types(block)
        assert ex.extinction.type == 'becker-coppens'

    def test_restore_switchable_types_without_extinction_tag_is_noop(self):
        import gemmi

        ex = ConcreteSc(name='sc1', experiment_type=_mk_type_sc_cwl_bragg())
        original = ex.extinction.type

        # Block has no _extinction.type; restore leaves extinction as-is.
        block = gemmi.cif.read_string('data_sc1\n_diffrn.type whatever\n').sole_block()
        ex._restore_switchable_types(block)
        assert ex.extinction.type == original


# ------------------------------------------------------------------
# Single-crystal read-only accessors
# ------------------------------------------------------------------


class TestScExperimentAccessors:
    def test_linked_structure_instrument_refln(self):
        ex = ConcreteSc(name='sc1', experiment_type=_mk_type_sc_cwl_bragg())
        assert ex.linked_structure is not None
        assert ex.instrument is not None
        assert ex.refln is not None

    def test_x_descriptor_is_none(self):
        ex = ConcreteSc(name='sc1', experiment_type=_mk_type_sc_cwl_bragg())
        assert ex.x_descriptor is None

    def test_fit_data_arrays_empty(self):
        ex = ConcreteSc(name='sc1', experiment_type=_mk_type_sc_cwl_bragg())
        assert ex.fit_data_arrays() == {}

    def test_intensity_category_is_refln(self):
        ex = ConcreteSc(name='sc1', experiment_type=_mk_type_sc_cwl_bragg())
        assert ex._intensity_category() is ex.refln

    def test_calculator_support_category_is_refln(self):
        ex = ConcreteSc(name='sc1', experiment_type=_mk_type_sc_cwl_bragg())
        assert ex._calculator_support_category() is ex.refln


# ------------------------------------------------------------------
# Powder read-only accessors
# ------------------------------------------------------------------


class TestPdExperimentAccessors:
    def test_x_descriptor_delegates_to_data(self):
        ex = ConcretePd(name='pd1', experiment_type=_mk_type_powder_cwl_bragg())
        # x_descriptor forwards to data.x_descriptor; both reference the
        # same underlying 2θ metadata name.
        assert ex.x_descriptor.name == ex.data.x_descriptor.name

    def test_fit_data_arrays_delegates_to_data(self):
        ex = ConcretePd(name='pd1', experiment_type=_mk_type_powder_cwl_bragg())
        assert ex.fit_data_arrays().keys() == ex.data.fit_data_arrays().keys()

    def test_intensity_category_is_data(self):
        ex = ConcretePd(name='pd1', experiment_type=_mk_type_powder_cwl_bragg())
        assert ex._intensity_category() is ex.data

    def test_calculator_support_category_is_data(self):
        ex = ConcretePd(name='pd1', experiment_type=_mk_type_powder_cwl_bragg())
        assert ex._calculator_support_category() is ex.data

    def test_restore_switchable_types_without_peak_tag_keeps_default(self):
        import gemmi

        ex = ConcretePd(name='pd1', experiment_type=_mk_type_powder_cwl_bragg())
        original = ex.peak.type

        # No _peak.type in the block; the peak profile is left unchanged.
        block = gemmi.cif.read_string('data_pd1\n_diffrn.type whatever\n').sole_block()
        ex._restore_switchable_types(block)
        assert ex.peak.type == original


# ------------------------------------------------------------------
# _get_valid_linked_structures
# ------------------------------------------------------------------


class _FakeStructures:
    def __init__(self, names):
        self.names = list(names)


class TestGetValidLinkedStructures:
    def test_no_linked_structures_warns_and_returns_empty(self, monkeypatch):
        from easydiffraction.datablocks.experiment.item import base as item_base

        ex = ConcretePd(name='pd1', experiment_type=_mk_type_powder_cwl_bragg())
        warnings: list[str] = []
        monkeypatch.setattr(item_base.log, 'warning', warnings.append)

        result = ex._get_valid_linked_structures(_FakeStructures([]))

        assert result == []
        assert any('No linked structures defined' in w for w in warnings)

    def test_skips_phases_absent_from_structures(self, monkeypatch):
        from easydiffraction.datablocks.experiment.item import base as item_base

        ex = ConcretePd(name='pd1', experiment_type=_mk_type_powder_cwl_bragg())
        ex.linked_structures.create(structure_id='present', scale=1.0)
        ex.linked_structures.create(structure_id='absent', scale=1.0)

        warnings: list[str] = []
        monkeypatch.setattr(item_base.log, 'warning', warnings.append)

        result = ex._get_valid_linked_structures(_FakeStructures(['present']))

        assert len(result) == 1
        assert result[0].structure_id.value == 'present'
        assert any("'absent' not" in w for w in warnings)

    def test_all_phases_missing_warns_returns_empty(self, monkeypatch):
        from easydiffraction.datablocks.experiment.item import base as item_base

        ex = ConcretePd(name='pd1', experiment_type=_mk_type_powder_cwl_bragg())
        ex.linked_structures.create(structure_id='absent', scale=1.0)

        warnings: list[str] = []
        monkeypatch.setattr(item_base.log, 'warning', warnings.append)

        result = ex._get_valid_linked_structures(_FakeStructures(['other']))

        assert result == []
        assert any('None of the linked structures' in w for w in warnings)
