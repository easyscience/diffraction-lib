# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Supplementary coverage tests for the CIF serialize/deserialize module.

These tests target behaviour not exercised by the three sibling test
files (test_serialize.py, test_serialize_category_owner_baseline.py,
test_serialize_more.py): scalar helpers, loop truncation, collection
hooks, project-config round-trips, analysis CIF restore branches, and
the descriptor deserialisation paths.
"""

from __future__ import annotations

import gemmi
import pytest

import easydiffraction.io.cif.serialize as MUT
from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import DataTypes
from easydiffraction.core.variable import BoolDescriptor
from easydiffraction.core.variable import IntegerDescriptor
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.core.variable import Parameter
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import TagSpec
from easydiffraction.utils.logging import Logger


def _bare_param(name: str, value: object) -> object:
    """Return a minimal serialize-only param exposing handler + value."""
    param = type('P', (), {})()
    param._tags = TagSpec(edi_names=[name])
    param.value = value
    return param


class _Item(CategoryItem):
    """Minimal single-parameter category item for loop tests."""

    def __init__(self, entry_name: str, tag: str, value: object) -> None:
        super().__init__()
        self._identity.category_entry_name = entry_name
        self._p = _bare_param(tag, value)

    @property
    def parameters(self) -> list:
        return [self._p]

    @property
    def as_cif(self) -> str:
        return MUT.category_item_to_cif(self)


# ----------------------------------------------------------------------
# Scalar formatting helpers
# ----------------------------------------------------------------------


def test_format_value_empty_string_becomes_unknown_marker():
    assert MUT.format_value('   ') == '?'


def test_format_value_unsupported_type_falls_back_to_str():
    assert MUT.format_value([1, 2]) == '[1, 2]'


def test_strip_cif_text_field_delimiters_unwraps_block():
    raw = ';\nmulti line text\n;'
    assert MUT._strip_cif_text_field_delimiters(raw) == 'multi line text'


def test_strip_cif_text_field_delimiters_returns_plain_token_unchanged():
    assert MUT._strip_cif_text_field_delimiters('plain') == 'plain'


def test_parse_bool_cif_value_recognises_tokens():
    assert MUT._parse_bool_cif_value('true') is True
    assert MUT._parse_bool_cif_value('FALSE') is False


def test_parse_bool_cif_value_returns_unquoted_token_when_not_boolean():
    assert MUT._parse_bool_cif_value("'maybe'") == 'maybe'


# ----------------------------------------------------------------------
# format_param_value free-parameter encoding
# ----------------------------------------------------------------------


def test_format_param_value_free_without_uncertainty_uses_empty_brackets():
    param = Parameter(
        name='p',
        value_spec=AttributeSpec(default=0.0),
        tags=TagSpec(edi_names=['_x.p']),
    )
    param.value = 3.5
    param.free = True

    assert MUT.format_param_value(param) == '3.5()'


def test_format_param_value_user_constrained_free_param_has_no_brackets():
    param = Parameter(
        name='p',
        value_spec=AttributeSpec(default=0.0),
        tags=TagSpec(edi_names=['_x.p']),
    )
    param.value = 2.0
    param._set_value_user_constrained(2.0)
    param.free = True

    assert MUT.format_param_value(param) == '2.'


# ----------------------------------------------------------------------
# Loop emission: validation and truncation
# ----------------------------------------------------------------------


def test_loop_tag_mismatch_raises_value_error(monkeypatch):
    monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.RAISE, raising=True)
    coll = CategoryCollection(item_type=_Item)
    coll['a'] = _Item('a', '_x.a', 1)
    coll['b'] = _Item('b', '_x.WRONG', 2)

    with pytest.raises(ValueError, match='CIF tag mismatch'):
        MUT.category_collection_to_cif(coll)


def test_collection_loop_truncates_to_max_display():
    coll = CategoryCollection(item_type=_Item)
    for n in range(6):
        coll[f'n{n}'] = _Item(f'n{n}', '_x.a', n)

    out = MUT.category_collection_to_cif(coll, max_display=4)
    lines = out.splitlines()

    assert '...' in lines
    # header (loop_ + 1 tag) + 2 leading rows + ... + 2 trailing rows
    assert lines == ['loop_', '_x.a', '0', '1', '...', '4', '5']


def test_adp_atom_site_loop_truncates_to_max_display():
    from easydiffraction.datablocks.structure.item.base import Structure

    structure = Structure(name='many')
    for i in range(6):
        structure.atom_sites.create(
            id=f'U{i}',
            type_symbol='O',
            adp_type='Uiso',
            adp_iso=0.01,
        )

    out = MUT.category_collection_to_cif(structure.atom_sites, max_display=4)

    assert '...' in out.splitlines()
    # Edi persistence uses the type-neutral isotropic ADP tag.
    assert '_atom_site.adp_iso' in out


# ----------------------------------------------------------------------
# Collection-level hooks
# ----------------------------------------------------------------------


def test_collection_skip_cif_serialization_returns_empty():
    coll = CategoryCollection(item_type=_Item)
    coll['a'] = _Item('a', '_x.a', 1)
    coll._skip_cif_serialization = lambda: True

    assert MUT.category_collection_to_cif(coll) == ''


def test_collection_format_cif_row_override_replaces_default_row():
    coll = CategoryCollection(item_type=_Item)
    coll['a'] = _Item('a', '_x.a', 1)
    coll._format_cif_row = lambda item: ['CUSTOM']

    out = MUT.category_collection_to_cif(coll)

    assert out == 'loop_\n_x.a\nCUSTOM'


def test_collection_format_cif_row_none_falls_back_to_default_row():
    coll = CategoryCollection(item_type=_Item)
    coll['a'] = _Item('a', '_x.a', 9)
    coll._format_cif_row = lambda item: None

    out = MUT.category_collection_to_cif(coll)

    assert out == 'loop_\n_x.a\n9'


def test_collection_loop_parameters_hook_is_used():
    class HookCollection(CategoryCollection):
        def _cif_loop_parameters(self, item: object) -> list:
            return item.parameters

    coll = HookCollection(item_type=_Item)
    coll['a'] = _Item('a', '_x.a', 5)

    assert MUT.category_collection_to_cif(coll) == 'loop_\n_x.a\n5'


def test_collection_scalar_descriptors_precede_loop():
    class ScalarCollection(CategoryCollection):
        @property
        def scalar_descriptors(self) -> list:
            return [_bare_param('_scalar.count', 1)]

    coll = ScalarCollection(item_type=_Item)
    coll['a'] = _Item('a', '_x.a', 7)

    out = MUT.category_collection_to_cif(coll)

    assert out == '_scalar.count 1\n\nloop_\n_x.a\n7'


def test_category_item_cif_parameters_hook_is_used():
    class HookItem(CategoryItem):
        def __init__(self) -> None:
            super().__init__()
            self._p = _bare_param('_y.b', 8)

        def _cif_parameters(self) -> list:
            return [self._p]

        @property
        def parameters(self) -> list:
            return []

        @property
        def as_cif(self) -> str:
            return MUT.category_item_to_cif(self)

    assert MUT.category_item_to_cif(HookItem()) == '_y.b 8'


# ----------------------------------------------------------------------
# Datablock / project description edge cases
# ----------------------------------------------------------------------


def test_datablock_item_to_cif_without_body_returns_header_only():
    class EmptyDatablock:
        def __init__(self) -> None:
            self._identity = type('I', (), {'datablock_entry_name': 'empty'})()

    assert MUT.datablock_item_to_cif(EmptyDatablock()) == 'data_empty'


def test_format_project_description_blank_is_unknown_marker():
    assert MUT._format_project_description('   ') == '?'


def test_project_info_to_cif_title_without_space_is_unquoted():
    from easydiffraction.project.project_metadata import ProjectMetadata

    metadata = ProjectMetadata(name='p1', title='NoSpaces', description='short')

    out = MUT.project_metadata_to_cif(metadata)

    assert '_metadata.title            NoSpaces' in out
    assert '_metadata.title            "' not in out


# ----------------------------------------------------------------------
# Project config / project assembly
# ----------------------------------------------------------------------


class _Section:
    """Section exposing ``as_cif`` either as a property or method."""

    def __init__(self, text: str, *, as_method: bool = False) -> None:
        self._text = text
        self._as_method = as_method

    @property
    def as_cif(self):
        if self._as_method:
            return lambda: self._text
        return self._text


def test_project_config_to_cif_includes_publication_and_method_sections(monkeypatch):
    monkeypatch.setattr(MUT, 'category_owner_to_cif', lambda owner: 'PUBLICATION')

    class Project:
        metadata = _Section('INFO')
        rendering_plot = _Section('PLOT')
        report = _Section('REPORT')
        publication = object()
        rendering_table = _Section('TABLE')
        verbosity = _Section('VERB', as_method=True)

    out = MUT.project_config_to_cif(Project())

    assert out == 'INFO\n\nPLOT\n\nREPORT\n\nPUBLICATION\n\nTABLE\n\nVERB'


def test_project_to_cif_assembles_structures_experiments_and_analysis(monkeypatch):
    monkeypatch.setattr(MUT, 'project_config_to_cif', lambda project: 'CONFIG')

    class Project:
        metadata = _Section('CFG')
        structures = _Section('STRUCT')
        experiments = _Section('EXP')
        analysis = _Section('ANALYSIS')

    out = MUT.project_to_cif(Project())

    assert out == 'CONFIG\n\nSTRUCT\n\nEXP\n\nANALYSIS'


# ----------------------------------------------------------------------
# Project info / config deserialisation
# ----------------------------------------------------------------------


def test_populate_project_info_uses_manual_reader_when_no_from_cif():
    class PlainInfo:
        name = None
        title = None
        description = None

    block = gemmi.cif.read_string(
        "data_p\n_project.id MYID\n_project.title 'My Title'\n_project.description 'Some desc'\n"
    ).sole_block()
    info = PlainInfo()

    MUT._populate_project_metadata_from_block(info, block)

    assert info.name == 'MYID'
    assert info.title == 'My Title'
    assert info.description == 'Some desc'


def test_populate_project_info_manual_reader_skips_absent_fields():
    class PlainInfo:
        name = 'unchanged'
        title = 'unchanged'
        description = 'unchanged'

    # Only the id is present; title and description tags are absent.
    block = gemmi.cif.read_string('data_p\n_project.id ONLYID\n').sole_block()
    info = PlainInfo()

    MUT._populate_project_metadata_from_block(info, block)

    assert info.name == 'ONLYID'
    assert info.title == 'unchanged'
    assert info.description == 'unchanged'


def test_project_info_from_cif_populates_real_project_info():
    from easydiffraction.project.project_metadata import ProjectMetadata

    metadata = ProjectMetadata(name='orig', title='Orig', description='orig desc')

    MUT.project_metadata_from_cif(
        metadata,
        "_project.id restored\n_project.title 'New Title'\n_project.description Desc\n",
    )

    assert metadata.name == 'restored'
    assert metadata.title == 'New Title'
    assert metadata.description == 'Desc'


def test_make_cif_string_reader_handles_unknown_and_text_fields():
    block = gemmi.cif.read_string(
        'data_p\n_a.known value\n_a.unknown ?\n_a.text\n;\nwrapped text\n;\n'
    ).sole_block()
    read = MUT._make_cif_string_reader(block)

    assert read('_a.known') == 'value'
    assert read('_a.unknown') is None
    assert read('_a.text') == 'wrapped text'
    assert read('_a.absent') is None


def test_project_config_from_cif_dispatches_to_every_section():
    class FakeSection:
        def __init__(self) -> None:
            self.calls = 0

        def from_cif(self, block: object) -> None:
            self.calls += 1

    class FakeProject:
        def __init__(self) -> None:
            self.metadata = FakeSection()
            self.rendering_plot = FakeSection()
            self.report = FakeSection()
            self.publication = FakeSection()
            self.rendering_table = FakeSection()
            self.verbosity = FakeSection()
            self.rendering_structure = FakeSection()
            self.structure_view = FakeSection()
            self.structure_style = FakeSection()

    project = FakeProject()

    MUT.project_config_from_cif(project, '_project.id foo\n')

    sections = (
        project.metadata,
        project.rendering_plot,
        project.report,
        project.publication,
        project.rendering_table,
        project.verbosity,
        project.rendering_structure,
        project.structure_view,
        project.structure_style,
    )
    assert all(section.calls == 1 for section in sections)


# ----------------------------------------------------------------------
# analysis_from_cif branches
# ----------------------------------------------------------------------


class _AnalysisProject:
    structures = type('Structures', (), {'parameters': []})()
    experiments = type('Experiments', (), {'parameters': [], 'names': []})()
    _varname = 'proj'


def _make_analysis() -> object:
    from easydiffraction.analysis.analysis import Analysis

    return Analysis(project=_AnalysisProject())


def test_analysis_from_cif_rejects_legacy_joint_fit_tags():
    analysis = _make_analysis()
    cif_text = """
_fitting_mode.type single
loop_
_joint_fit_experiment.id
_joint_fit_experiment.weight
ex1 0.5
"""

    with pytest.raises(ValueError, match='Legacy analysis CIF tags'):
        MUT.analysis_from_cif(analysis, cif_text)


def test_analysis_from_cif_rejects_legacy_minimizer_output_tags():
    analysis = _make_analysis()
    cif_text = """
_fitting_mode.type single
_minimizer.objective_value 1.23
"""

    with pytest.raises(ValueError, match='Legacy analysis CIF tags'):
        MUT.analysis_from_cif(analysis, cif_text)


def test_analysis_from_cif_uses_defaults_when_mode_and_minimizer_missing():
    from easydiffraction.analysis.enums import FitModeEnum
    from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum

    analysis = _make_analysis()

    MUT.analysis_from_cif(analysis, '_software.framework_name X\n')

    assert analysis.fitting_mode.type == FitModeEnum.default().value
    assert analysis.minimizer.type == MinimizerTypeEnum.default().value


def test_analysis_from_cif_restores_joint_fit_rows_in_joint_mode():
    analysis = _make_analysis()
    cif_text = """
_fitting_mode.type joint
loop_
_joint_fit.experiment_id
_joint_fit.weight
ex1 0.5
ex2 0.5
"""

    MUT.analysis_from_cif(analysis, cif_text)

    assert analysis.fitting_mode.type == 'joint'
    assert len(analysis.joint_fit) == 2


def test_analysis_from_cif_restores_sequential_sections_in_sequential_mode():
    analysis = _make_analysis()
    cif_text = (
        '\n_fitting_mode.type sequential'
        '\n_sequential_fit.data_dir scans'
        '\n_sequential_fit.file_pattern *.xye'
        '\nloop_'
        '\n_sequential_fit_extract.id'
        '\n_sequential_fit_extract.target'
        '\n_sequential_fit_extract.pattern'
        '\n_sequential_fit_extract.required'
        '\ntemperature diffrn.ambient_temperature temp true\n'
    )

    MUT.analysis_from_cif(analysis, cif_text)

    assert analysis.fitting_mode.type == 'sequential'
    assert analysis.sequential_fit.data_dir.value == 'scans'
    assert len(analysis.sequential_fit_extract) == 1


def test_analysis_from_cif_warns_when_inactive_sections_present(monkeypatch):
    monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)
    analysis = _make_analysis()
    cif_text = """
_fitting_mode.type single
loop_
_joint_fit.experiment_id
_joint_fit.weight
ex1 0.5
"""

    MUT.analysis_from_cif(analysis, cif_text)

    # single mode keeps the joint rows inactive (not restored)
    assert analysis.fitting_mode.type == 'single'
    assert len(analysis.joint_fit) == 0


def test_analysis_from_cif_restores_persisted_fit_result_state():
    analysis = _make_analysis()
    cif_text = """
_fitting_mode.type single
_fit_result.result_kind deterministic
"""

    MUT.analysis_from_cif(analysis, cif_text)

    assert analysis._has_persisted_fit_state() is True
    assert analysis.fit_result.result_kind.value == 'deterministic'


# ----------------------------------------------------------------------
# Descriptor deserialisation: _set_param_from_raw_cif_value & defaults
# ----------------------------------------------------------------------


def test_set_param_from_raw_integer_value():
    param = IntegerDescriptor(
        name='n',
        value_spec=AttributeSpec(data_type=DataTypes.INTEGER, default=0),
        tags=TagSpec(edi_names=['_x.n']),
    )

    MUT._set_param_from_raw_cif_value(param, '7')

    assert param.value == 7


def test_set_param_from_raw_non_integer_is_ignored_with_warning(monkeypatch):
    monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)
    param = IntegerDescriptor(
        name='n',
        value_spec=AttributeSpec(data_type=DataTypes.INTEGER, default=0),
        tags=TagSpec(edi_names=['_x.n']),
    )
    param.value = 5

    MUT._set_param_from_raw_cif_value(param, '3.5')

    # Non-integer CIF value is ignored; the prior value is preserved.
    assert param.value == 5


def test_set_param_from_raw_numeric_with_brackets_marks_free_and_uncertainty():
    param = Parameter(
        name='p',
        value_spec=AttributeSpec(default=0.0),
        tags=TagSpec(edi_names=['_x.p']),
    )

    MUT._set_param_from_raw_cif_value(param, '1.23(45)')

    assert param.value == pytest.approx(1.23)
    assert param.free is True
    assert param.uncertainty == pytest.approx(0.45)


def test_set_param_from_raw_string_strips_quotes():
    param = StringDescriptor(
        name='s',
        value_spec=AttributeSpec(default='x'),
        tags=TagSpec(edi_names=['_x.s']),
    )

    MUT._set_param_from_raw_cif_value(param, "'hello'")

    assert param.value == 'hello'


def test_set_param_from_raw_bool_value():
    param = BoolDescriptor(name='b', tags=TagSpec(edi_names=['_x.b']))

    MUT._set_param_from_raw_cif_value(param, 'true')

    assert param.value is True


def test_set_param_from_raw_unknown_marker_resets_to_default():
    param = StringDescriptor(
        name='s',
        value_spec=AttributeSpec(default='def'),
        tags=TagSpec(edi_names=['_x.s']),
    )
    param.value = 'changed'

    MUT._set_param_from_raw_cif_value(param, '?')

    assert param.value == 'def'


def test_set_param_to_default_restores_descriptor_default():
    param = StringDescriptor(
        name='s',
        value_spec=AttributeSpec(default='dd'),
        tags=TagSpec(edi_names=['_x.s']),
    )
    param.value = 'changed'

    MUT._set_param_to_default_from_cif(param, raw=None)

    assert param.value == 'dd'


def test_set_param_to_default_raises_for_required_field_without_default(monkeypatch):
    monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.RAISE, raising=True)
    param = StringDescriptor(
        name='nd',
        value_spec=AttributeSpec(),
        tags=TagSpec(edi_names=['_x.nd']),
    )

    with pytest.raises(ValueError, match='Cannot load required CIF field'):
        MUT._set_param_to_default_from_cif(param, raw=None)


# ----------------------------------------------------------------------
# param_from_cif / category_collection_from_cif
# ----------------------------------------------------------------------


def test_param_from_cif_missing_tag_uses_default():
    param = Parameter(
        name='p',
        value_spec=AttributeSpec(default=9.0),
        tags=TagSpec(edi_names=['_x.absent']),
    )
    param.value = 3.0
    block = gemmi.cif.read_string('data_t\n_x.other 1\n').sole_block()

    MUT.param_from_cif(param, block)

    assert param.value == 9.0


def test_param_from_cif_selects_value_at_loop_index():
    param = NumericDescriptor(
        name='a',
        value_spec=AttributeSpec(default=0.0),
        tags=TagSpec(edi_names=['_loop.a']),
    )
    block = gemmi.cif.read_string('data_t\nloop_\n_loop.a\n10\n20\n30\n').sole_block()

    MUT.param_from_cif(param, block, idx=2)

    assert param.value == 30.0


def test_category_collection_from_cif_requires_item_type():
    coll = CategoryCollection(item_type=None)
    block = gemmi.cif.read_string('data_t\n_x.a 1\n').sole_block()

    with pytest.raises(ValueError, match='Child class is not defined'):
        MUT.category_collection_from_cif(coll, block)


class _PairItem(CategoryItem):
    """Two-numeric-parameter item with a category code, for loop tests."""

    _category_code = 'pc'

    def __init__(self) -> None:
        super().__init__()
        self._a = NumericDescriptor(
            name='a',
            value_spec=AttributeSpec(default=0.0),
            tags=TagSpec(edi_names=['_pc.a']),
        )
        self._b = NumericDescriptor(
            name='b',
            value_spec=AttributeSpec(default=99.0),
            tags=TagSpec(edi_names=['_pc.b']),
        )

    @property
    def parameters(self) -> list:
        return [self._a, self._b]


def test_category_collection_from_cif_populates_rows():
    coll = CategoryCollection(item_type=_PairItem)
    block = gemmi.cif.read_string('data_t\nloop_\n_pc.a\n_pc.b\n1 2\n3 4\n').sole_block()

    MUT.category_collection_from_cif(coll, block)

    values = [(item._a.value, item._b.value) for item in coll.values()]
    assert values == [(1.0, 2.0), (3.0, 4.0)]


def test_category_collection_from_cif_missing_column_uses_default():
    coll = CategoryCollection(item_type=_PairItem)
    block = gemmi.cif.read_string('data_t\nloop_\n_pc.a\n1\n2\n').sole_block()

    MUT.category_collection_from_cif(coll, block)

    # _pc.b is absent from the loop, so each row keeps the default 99.
    values = [(item._a.value, item._b.value) for item in coll.values()]
    assert values == [(1.0, 99.0), (2.0, 99.0)]


def test_category_collection_from_cif_no_matching_loop_is_noop():
    coll = CategoryCollection(item_type=_PairItem)
    block = gemmi.cif.read_string('data_t\n_other.x 1\n').sole_block()

    MUT.category_collection_from_cif(coll, block)

    assert len(coll) == 0


def test_category_collection_from_cif_reads_scalar_descriptors():
    class ScalarCollection(CategoryCollection):
        def __init__(self) -> None:
            super().__init__(item_type=_PairItem)
            self._count = NumericDescriptor(
                name='count',
                value_spec=AttributeSpec(default=0.0),
                tags=TagSpec(edi_names=['_pc.count']),
            )

    coll = ScalarCollection()
    block = gemmi.cif.read_string('data_t\n_pc.count 5\nloop_\n_pc.a\n_pc.b\n1 2\n').sole_block()

    MUT.category_collection_from_cif(coll, block)

    assert coll._count.value == 5.0
    assert len(coll) == 1


def test_category_collection_from_cif_invokes_after_from_cif_hook():
    calls: list[int] = []

    class HookedCollection(CategoryCollection):
        def __init__(self) -> None:
            super().__init__(item_type=_PairItem)

        def _after_from_cif(self) -> None:
            calls.append(len(self))

    coll = HookedCollection()
    block = gemmi.cif.read_string('data_t\nloop_\n_pc.a\n_pc.b\n1 2\n3 4\n').sole_block()

    MUT.category_collection_from_cif(coll, block)

    assert calls == [2]
