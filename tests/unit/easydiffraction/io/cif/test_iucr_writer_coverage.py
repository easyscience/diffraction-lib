# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Supplementary coverage tests for the IUCr CIF writer helpers."""

from __future__ import annotations

from collections import UserDict
from types import SimpleNamespace

import pytest

from easydiffraction.io.cif.handler import CifHandler


class _Descriptor:
    """Minimal CIF descriptor exposing a value and a handler."""

    def __init__(self, value, tag='_x.value', iucr_name=None):
        self.name = tag.rsplit('.', maxsplit=1)[-1]
        self.value = value
        self._cif_handler = CifHandler(names=[tag], iucr_name=iucr_name)


def _descriptor(value, tag='_x.value', iucr_name=None):
    return _Descriptor(value, tag=tag, iucr_name=iucr_name)


# --- _report_path / iucr_report_path ----------------------------------


def test_report_path_uses_explicit_path(tmp_path):
    from easydiffraction.io.cif.iucr_writer import iucr_report_path

    target = tmp_path / 'custom' / 'out.cif'
    project = SimpleNamespace(name='demo', metadata=SimpleNamespace(path=tmp_path))

    assert iucr_report_path(project, target) == target


def test_report_path_raises_when_project_unsaved():
    from easydiffraction.io.cif.iucr_writer import iucr_report_path

    project = SimpleNamespace(name='demo', metadata=SimpleNamespace(path=None))

    with pytest.raises(FileNotFoundError, match='Save the project first'):
        iucr_report_path(project)


def test_report_path_defaults_to_reports_dir(tmp_path):
    from easydiffraction.io.cif.iucr_writer import iucr_report_path

    project = SimpleNamespace(name='demo', metadata=SimpleNamespace(path=tmp_path))

    assert iucr_report_path(project) == tmp_path / 'reports' / 'demo.cif'


# --- _block_name ------------------------------------------------------


def test_block_name_sanitises_and_falls_back():
    from easydiffraction.io.cif.iucr_writer import _block_name

    assert _block_name('my phase!') == 'my_phase'
    # Only non-alphanumeric content collapses to the default code.
    assert _block_name('***') == 'I'
    assert _block_name(None) == 'I'


def test_block_name_prefixes_leading_digit():
    from easydiffraction.io.cif.iucr_writer import _block_name

    assert _block_name('1phase') == 'block_1phase'


def test_unique_block_name_appends_numeric_suffix():
    from easydiffraction.io.cif.iucr_writer import _unique_block_name

    used = {'phase'}
    assert _unique_block_name('phase', used) == 'phase_2'
    assert _unique_block_name('phase', used) == 'phase_3'


# --- _attribute_value / _attribute_descriptor -------------------------


def test_attribute_helpers_return_none_for_missing_owner():
    from easydiffraction.io.cif.iucr_writer import _attribute_descriptor
    from easydiffraction.io.cif.iucr_writer import _attribute_value

    assert _attribute_value(None, 'anything') is None
    assert _attribute_descriptor(None, 'anything') is None


def test_attribute_value_unwraps_descriptor():
    from easydiffraction.io.cif.iucr_writer import _attribute_value

    owner = SimpleNamespace(length_a=_descriptor(5.43))
    assert _attribute_value(owner, 'length_a') == 5.43


# --- _format_item_value / text fields / quoting -----------------------


def test_format_item_value_unknown_and_blank():
    from easydiffraction.io.cif.iucr_writer import _format_item_value

    assert _format_item_value('?') == '?'
    assert _format_item_value('.') == '.'
    # Whitespace-only strings collapse to the CIF unknown marker.
    assert _format_item_value('   ') == '?'


def test_format_item_value_quotes_when_needed():
    from easydiffraction.io.cif.iucr_writer import _format_item_value

    assert _format_item_value('two words') == "'two words'"
    assert _format_item_value('_leading') == "'_leading'"
    assert _format_item_value('plain') == 'plain'


def test_format_item_value_long_string_becomes_text_field():
    from easydiffraction.io.cif.iucr_writer import _format_item_value

    value = 'word ' * 30
    formatted = _format_item_value(value)
    assert formatted.startswith(';\n')
    assert formatted.endswith('\n;')


def test_quote_string_prefers_double_quotes_then_text_field():
    from easydiffraction.io.cif.iucr_writer import _quote_string

    assert _quote_string("it's here") == '"it\'s here"'
    # When both quote styles are present, fall back to a text field.
    both = 'a \'single\' and "double"'
    formatted = _quote_string(both)
    assert formatted.startswith(';\n')


def test_format_text_field_preserves_blank_lines():
    from easydiffraction.io.cif.iucr_writer import _format_text_field

    formatted = _format_text_field('line one\n\nline two')
    assert formatted.startswith(';\n')
    assert '\n\n' in formatted


# --- _write_item multiline handling -----------------------------------


def test_write_item_emits_multiline_text_field():
    from easydiffraction.io.cif.iucr_writer import _write_item

    lines = []
    _write_item(lines, '_note.text', 'word ' * 30)
    assert lines[0] == '_note.text'
    assert lines[1] == ';'
    assert lines[-1] == ';'


def test_write_item_pads_scalar_tag():
    from easydiffraction.io.cif.iucr_writer import _write_item

    lines = []
    _write_item(lines, '_cell.length_a', 5.43)
    assert lines[0].startswith('_cell.length_a')
    assert lines[0].endswith('5.43')


# --- _format_loop_value -----------------------------------------------


def test_format_loop_value_rejects_long_text():
    from easydiffraction.io.cif.iucr_writer import _format_loop_value

    with pytest.raises(ValueError, match='not supported in IUCr report loops'):
        _format_loop_value('word ' * 30)


def test_format_loop_value_passes_short_value():
    from easydiffraction.io.cif.iucr_writer import _format_loop_value

    assert _format_loop_value('ok') == 'ok'


# --- _section ---------------------------------------------------------


def test_section_skips_blank_separator_after_empty_line():
    from easydiffraction.io.cif.iucr_writer import _section

    lines = ['data_x', '']
    _section(lines, 'Cell')
    # No extra blank line is added when the last line is already blank.
    assert lines == ['data_x', '', '# ---- Cell ----']


def test_section_inserts_blank_separator():
    from easydiffraction.io.cif.iucr_writer import _section

    lines = ['data_x']
    _section(lines, 'Cell')
    assert lines == ['data_x', '', '# ---- Cell ----']


# --- _write_reference_values ------------------------------------------


def test_write_reference_values_unknown_when_empty():
    from easydiffraction.io.cif.iucr_writer import _write_reference_values

    lines = []
    _write_reference_values(lines, '_pd_block_id', [])
    assert lines[-1].endswith('?')


def test_write_reference_values_scalar_then_loop():
    from easydiffraction.io.cif.iucr_writer import _write_reference_values

    scalar_lines = []
    _write_reference_values(scalar_lines, '_pd_block_id', ['only'])
    assert scalar_lines[-1].endswith('only')

    loop_lines = []
    _write_reference_values(loop_lines, '_pd_block_id', ['a', 'b'])
    assert loop_lines[0] == 'loop_'
    assert '  a' in loop_lines
    assert '  b' in loop_lines


# --- _include_status / _finite_number ---------------------------------


def test_include_status_unknown_when_values_missing():
    from easydiffraction.io.cif.iucr_writer import _include_status

    refln = SimpleNamespace(
        intensity_meas=_descriptor(None),
        intensity_meas_su=_descriptor(2.0),
    )
    assert _include_status(refln) == '?'


def test_include_status_observed_for_nonpositive_sigma():
    from easydiffraction.io.cif.iucr_writer import _include_status

    refln = SimpleNamespace(
        intensity_meas=_descriptor(10.0),
        intensity_meas_su=_descriptor(0.0),
    )
    assert _include_status(refln) == 'o'


def test_include_status_below_threshold():
    from easydiffraction.io.cif.iucr_writer import _include_status

    weak = SimpleNamespace(
        intensity_meas=_descriptor(1.0),
        intensity_meas_su=_descriptor(2.0),
    )
    strong = SimpleNamespace(
        intensity_meas=_descriptor(100.0),
        intensity_meas_su=_descriptor(2.0),
    )
    assert _include_status(weak) == '<'
    assert _include_status(strong) == 'o'


def test_finite_number_rejects_non_numeric_and_nonfinite():
    from easydiffraction.io.cif.iucr_writer import _finite_number

    assert _finite_number('5') is None
    assert _finite_number(float('nan')) is None
    assert _finite_number(float('inf')) is None
    assert _finite_number(3) == 3.0


# --- _powder_weight ---------------------------------------------------


def test_powder_weight_unknown_for_nonpositive_sigma():
    from easydiffraction.io.cif.iucr_writer import _powder_weight

    point = SimpleNamespace(intensity_meas_su=_descriptor(0.0))
    assert _powder_weight(point) == '?'


def test_powder_weight_inverse_variance():
    from easydiffraction.io.cif.iucr_writer import _powder_weight

    point = SimpleNamespace(intensity_meas_su=_descriptor(2.0))
    assert _powder_weight(point) == pytest.approx(0.25)


# --- _adp_family / _atom_site_for_aniso -------------------------------


def test_adp_family_distinguishes_b_and_u():
    from easydiffraction.io.cif.iucr_writer import _adp_family

    assert _adp_family(SimpleNamespace(adp_type=_descriptor('Biso'))) == 'B'
    assert _adp_family(SimpleNamespace(adp_type=_descriptor('Uiso'))) == 'U'


def test_atom_site_for_aniso_matches_by_label():
    from easydiffraction.io.cif.iucr_writer import _atom_site_for_aniso

    site = SimpleNamespace(id=_descriptor('Si1'))
    by_id = {'Si1': site}
    aniso = SimpleNamespace(id=_descriptor('Si1'))
    missing = SimpleNamespace(id=_descriptor('O1'))

    assert _atom_site_for_aniso(by_id, aniso) is site
    assert _atom_site_for_aniso(by_id, missing) is None


# --- formula helpers --------------------------------------------------


def test_formula_values_unknown_without_atom_sites():
    from easydiffraction.io.cif.iucr_writer import _structure_formula_values

    structure = SimpleNamespace(atom_sites=None)
    formula = _structure_formula_values(structure)
    assert formula.sum_formula == '?'
    assert formula.weight == '?'


def test_formula_values_hill_ordering_and_counts():
    from easydiffraction.io.cif.iucr_writer import _structure_formula_values

    atom_sites = [
        SimpleNamespace(type_symbol=_descriptor('O'), occupancy=_descriptor(2.0)),
        SimpleNamespace(type_symbol=_descriptor('C'), occupancy=_descriptor(1.0)),
        SimpleNamespace(type_symbol=_descriptor('H'), occupancy=_descriptor(4.0)),
    ]
    structure = SimpleNamespace(atom_sites=atom_sites)
    formula = _structure_formula_values(structure)
    # Hill order: carbon, hydrogen, then the rest; count 1 has no suffix.
    assert formula.sum_formula == 'C H4 O2'
    assert formula.moiety == formula.sum_formula


def test_formula_count_defaults_to_one_for_non_numeric():
    from easydiffraction.io.cif.iucr_writer import _formula_count

    assert _formula_count('full') == 1.0
    assert _formula_count(0.5) == 0.5


def test_format_formula_suffix_handles_fractions():
    from easydiffraction.io.cif.iucr_writer import _format_formula_suffix

    assert _format_formula_suffix(1.0) == ''
    assert _format_formula_suffix(3.0) == '3'
    assert _format_formula_suffix(0.5) == '0.5'


def test_formula_sort_key_orders_carbon_hydrogen_rest():
    from easydiffraction.io.cif.iucr_writer import _formula_sort_key

    assert _formula_sort_key('C') < _formula_sort_key('H')
    assert _formula_sort_key('H') < _formula_sort_key('O')


# --- software-role helpers --------------------------------------------


def test_software_role_label_unknown_without_name():
    from easydiffraction.io.cif.iucr_writer import _software_role_label

    project = SimpleNamespace(
        analysis=SimpleNamespace(
            software={
                'framework': SimpleNamespace(name=_descriptor(None)),
            }
        )
    )
    assert _software_role_label(project, 'framework') == '?'


def test_software_role_label_name_only_when_version_missing():
    from easydiffraction.io.cif.iucr_writer import _software_role_label

    project = SimpleNamespace(
        analysis=SimpleNamespace(
            software={
                'framework': SimpleNamespace(
                    name=_descriptor('CrysPy'),
                    version=_descriptor(''),
                ),
            }
        )
    )
    assert _software_role_label(project, 'framework') == 'CrysPy'


def test_software_role_label_name_and_version():
    from easydiffraction.io.cif.iucr_writer import _software_role_label

    project = SimpleNamespace(
        analysis=SimpleNamespace(
            software={
                'calculator': SimpleNamespace(
                    name=_descriptor('cryspy'),
                    version=_descriptor('1.2'),
                ),
            }
        )
    )
    assert _software_role_label(project, 'calculator') == 'cryspy 1.2'


def test_software_fit_datetime_none_and_value():
    from easydiffraction.io.cif.iucr_writer import _software_fit_datetime

    empty = SimpleNamespace(metadata=SimpleNamespace(timestamp=''))
    assert _software_fit_datetime(empty) is None

    populated = SimpleNamespace(metadata=SimpleNamespace(timestamp='2026-06-06T00:00:00'))
    assert _software_fit_datetime(populated) == '2026-06-06T00:00:00'


# --- refinement-label helpers -----------------------------------------


def test_structure_refinement_label_falls_back_to_framework():
    from easydiffraction.io.cif.iucr_writer import _structure_refinement_label

    # A missing calculator or minimizer collapses to the framework label.
    assert _structure_refinement_label('MyFramework', '?', 'lmfit') == 'MyFramework'


def test_structure_refinement_label_full_sentence():
    from easydiffraction.io.cif.iucr_writer import _structure_refinement_label

    label = _structure_refinement_label('MyFramework', 'cryspy', 'lmfit')
    assert label == 'MyFramework with lmfit minimizer and cryspy calculator'


def test_framework_refinement_label_default_software(monkeypatch):
    from easydiffraction.io.cif import iucr_writer

    monkeypatch.setattr(iucr_writer, 'package_version', lambda _name: None)
    assert iucr_writer._framework_refinement_label('?') == 'EasyDiffraction'
    assert iucr_writer._framework_refinement_label('Custom') == 'Custom'


def test_software_label_appends_version(monkeypatch):
    from easydiffraction.io.cif import iucr_writer

    monkeypatch.setattr(iucr_writer, 'package_version', lambda _name: '9.9')
    assert iucr_writer._software_label('cryspy') == 'cryspy 9.9'


# --- _linked_structure / _linked_powder_structures errors -------------


class _Structures(UserDict):
    @property
    def names(self):
        return list(self.data)


def test_linked_structure_falls_back_to_single_structure():
    from easydiffraction.io.cif.iucr_writer import _linked_structure

    only = SimpleNamespace(name='only')
    structures = _Structures(only=only)
    experiment = SimpleNamespace(
        name='expt',
        linked_structure=SimpleNamespace(structure_id=_descriptor('missing')),
    )
    project = SimpleNamespace(structures=structures)
    assert _linked_structure(project, experiment) is only


def test_linked_structure_raises_on_ambiguous_link():
    from easydiffraction.io.cif.iucr_writer import _linked_structure

    structures = _Structures(
        a=SimpleNamespace(name='a'),
        b=SimpleNamespace(name='b'),
    )
    experiment = SimpleNamespace(
        name='expt',
        linked_structure=SimpleNamespace(structure_id=_descriptor('missing')),
    )
    project = SimpleNamespace(structures=structures)
    with pytest.raises(ValueError, match="links crystal 'missing'"):
        _linked_structure(project, experiment)


def test_linked_powder_structures_falls_back_to_single():
    from easydiffraction.io.cif.iucr_writer import _linked_powder_structures

    only = SimpleNamespace(name='only')
    structures = _Structures(only=only)
    linked_phase = SimpleNamespace(structure_id=_descriptor('missing'))
    experiment = SimpleNamespace(name='expt', linked_structures=[linked_phase])
    project = SimpleNamespace(structures=structures)

    result = _linked_powder_structures(project, experiment)
    assert result == [(only, linked_phase)]


def test_linked_powder_structures_raises_on_ambiguous_link():
    from easydiffraction.io.cif.iucr_writer import _linked_powder_structures

    structures = _Structures(
        a=SimpleNamespace(name='a'),
        b=SimpleNamespace(name='b'),
    )
    experiment = SimpleNamespace(
        name='expt',
        linked_structures=[SimpleNamespace(structure_id=_descriptor('missing'))],
    )
    project = SimpleNamespace(structures=structures)
    with pytest.raises(ValueError, match='links structures'):
        _linked_powder_structures(project, experiment)


# --- _collection_values -----------------------------------------------


def test_collection_values_handles_none_callable_and_iterable():
    from easydiffraction.io.cif.iucr_writer import _collection_values

    assert tuple(_collection_values(None)) == ()

    with_values = SimpleNamespace(values=lambda: [1, 2, 3])
    assert list(_collection_values(with_values)) == [1, 2, 3]

    assert list(_collection_values([4, 5])) == [4, 5]


def test_collection_values_wraps_scalar_object():
    from easydiffraction.io.cif.iucr_writer import _collection_values

    scalar = SimpleNamespace(name='scalar')
    assert tuple(_collection_values(scalar)) == (scalar,)


# --- descriptor / iucr-name helpers -----------------------------------


def test_iucr_descriptor_fallback_through_parameters():
    from easydiffraction.io.cif.iucr_writer import _iucr_descriptor

    descriptor = _descriptor('val', '_a.b', iucr_name='_iucr.a')
    descriptor.name = 'target'
    owner = SimpleNamespace(
        target='plain string',
        parameters=[descriptor],
        scalar_descriptors=[],
    )
    assert _iucr_descriptor(owner, 'target') is descriptor


def test_iucr_descriptor_raises_when_no_handler():
    from easydiffraction.io.cif.iucr_writer import _iucr_descriptor

    owner = SimpleNamespace(target='plain', parameters=[], scalar_descriptors=[])
    with pytest.raises(AttributeError, match='no CIF handler'):
        _iucr_descriptor(owner, 'target')


def test_iucr_descriptor_for_tag_uses_private_type():
    from easydiffraction.io.cif.iucr_writer import _iucr_descriptor_for_tag

    type_descriptor = _descriptor('chebyshev', '_background.type', '_iucr.bg_type')
    owner = SimpleNamespace(_type=type_descriptor, parameters=[], scalar_descriptors=[])
    assert _iucr_descriptor_for_tag(owner, '_iucr.bg_type') is type_descriptor


def test_iucr_descriptor_for_tag_searches_descriptors():
    from easydiffraction.io.cif.iucr_writer import _iucr_descriptor_for_tag

    descriptor = _descriptor(1.0, '_extinction.radius', '_iucr.radius')
    owner = SimpleNamespace(_type=None, parameters=[descriptor], scalar_descriptors=[])
    assert _iucr_descriptor_for_tag(owner, '_iucr.radius') is descriptor
    assert _iucr_descriptor_for_tag(owner, '_iucr.missing') is None


def test_iucr_descriptor_for_tag_returns_none_for_missing_owner():
    from easydiffraction.io.cif.iucr_writer import _iucr_descriptor_for_tag

    assert _iucr_descriptor_for_tag(None, '_iucr.radius') is None


def test_descriptor_iucr_name_handles_handlerless_value():
    from easydiffraction.io.cif.iucr_writer import _descriptor_iucr_name

    assert _descriptor_iucr_name(SimpleNamespace(value=1.0)) is None
    assert _descriptor_iucr_name(_descriptor(1.0, '_a.b', '_iucr.a')) == '_iucr.a'


def test_iucr_items_empty_for_missing_owner():
    from easydiffraction.io.cif.iucr_writer import _iucr_items

    assert _iucr_items(None, ('scale',)) == []


def test_is_cif_descriptor_detects_handler():
    from easydiffraction.io.cif.iucr_writer import _is_cif_descriptor

    assert _is_cif_descriptor(_descriptor(1.0)) is True
    assert _is_cif_descriptor(SimpleNamespace(value=1.0)) is False
    assert _is_cif_descriptor(1.0) is False


# --- _with_extension_descriptor ---------------------------------------


def test_with_extension_descriptor_keeps_item_when_no_descriptor():
    from easydiffraction.io.cif.iucr_transformers import IucrItem
    from easydiffraction.io.cif.iucr_writer import _with_extension_descriptor

    experiment = SimpleNamespace(extinction=None)
    item = IucrItem('_easydiffraction_extinction.radius', 1.0)
    assert _with_extension_descriptor(experiment, item) is item
