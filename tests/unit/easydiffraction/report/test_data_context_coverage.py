# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Supplementary edge-case tests for report data-context helpers."""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np


class _Descriptor:
    def __init__(self, value):
        self.value = value


def _make_parameter(name, *, display_handler=None, cif_names=None):
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.variable import Parameter
    from easydiffraction.io.cif.handler import CifHandler

    return Parameter(
        name=name,
        value_spec=AttributeSpec(default=0.0),
        display_handler=display_handler,
        cif_handler=CifHandler(names=cif_names or [f'_{name}']),
    )


# --- _collection_values fallbacks (lines 1227, 1233) ---


def test_collection_values_returns_empty_tuple_for_none():
    from easydiffraction.report.data_context import _collection_values

    assert _collection_values(None) == ()


def test_collection_values_wraps_non_iterable_scalar():
    from easydiffraction.report.data_context import _collection_values

    assert _collection_values(42) == (42,)


def test_collection_values_passes_through_plain_iterables():
    from easydiffraction.report.data_context import _collection_values

    assert list(_collection_values([1, 2, 3])) == [1, 2, 3]


def test_collection_values_uses_values_method_when_present():
    from easydiffraction.report.data_context import _collection_values

    collection = SimpleNamespace(values=lambda: ['a', 'b'])
    assert list(_collection_values(collection)) == ['a', 'b']


# --- _display_units placeholder suppression (line 940) ---


def test_display_units_returns_empty_for_none():
    from easydiffraction.report.data_context import _display_units

    assert _display_units(None) == ''


def test_display_units_suppresses_literal_none_label():
    from easydiffraction.report.data_context import _display_units

    assert _display_units('None') == ''
    assert _display_units('none') == ''


def test_display_units_passes_through_real_units():
    from easydiffraction.report.data_context import _display_units

    assert _display_units('deg') == 'deg'


# --- _first_cif_name no handler / no names (line 933) ---


def test_first_cif_name_returns_none_without_handler():
    from easydiffraction.report.data_context import _first_cif_name

    assert _first_cif_name(SimpleNamespace()) is None


def test_first_cif_name_returns_none_for_empty_names():
    from easydiffraction.report.data_context import _first_cif_name

    parameter = SimpleNamespace(_cif_handler=SimpleNamespace(names=()))
    assert _first_cif_name(parameter) is None


# --- _is_numeric_value bool branch (line 870) ---


def test_is_numeric_value_rejects_booleans():
    from easydiffraction.report.data_context import _is_numeric_value

    true_value = True
    false_value = False
    assert _is_numeric_value(true_value) is False
    assert _is_numeric_value(false_value) is False
    assert _is_numeric_value(1) is True
    assert _is_numeric_value('1.5') is True
    assert _is_numeric_value('not refined') is False


# --- _descriptor_is_numeric classification ---


def test_descriptor_is_numeric_classifies_descriptor_types():
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.variable import IntegerDescriptor
    from easydiffraction.core.variable import NumericDescriptor
    from easydiffraction.core.variable import StringDescriptor
    from easydiffraction.io.cif.handler import CifHandler
    from easydiffraction.report.data_context import _descriptor_is_numeric

    cif_handler = CifHandler(names=['_x.y'])
    integer = IntegerDescriptor(
        name='n',
        value_spec=AttributeSpec(default=0),
        cif_handler=cif_handler,
    )
    numeric = NumericDescriptor(
        name='m',
        value_spec=AttributeSpec(default=0.0),
        cif_handler=cif_handler,
    )
    string = StringDescriptor(
        name='s',
        value_spec=AttributeSpec(default=''),
        cif_handler=cif_handler,
    )

    assert _descriptor_is_numeric(integer) is True
    assert _descriptor_is_numeric(numeric) is True
    assert _descriptor_is_numeric(string) is False


# --- _number_parts / _siunitx_number_parts non-numeric text (lines 820, 746) ---


def test_number_parts_returns_none_for_non_numeric_text():
    from easydiffraction.report.data_context import _number_parts

    assert _number_parts('not refined') is None


def test_siunitx_number_parts_returns_none_for_non_numeric_text():
    from easydiffraction.report.data_context import _siunitx_number_parts

    assert _siunitx_number_parts('abc') is None


# --- _siunitx_table_format default when no numeric parts (line 730) ---


def test_siunitx_table_format_defaults_without_numeric_parts():
    from easydiffraction.report.data_context import _siunitx_table_format

    assert _siunitx_table_format([]) == '1.0'
    assert _siunitx_table_format([None, '']) == '1.0'
    assert _siunitx_table_format(['not refined']) == '1.0'


def test_siunitx_table_format_emits_signed_format_for_negatives():
    from easydiffraction.report.data_context import _siunitx_table_format

    assert _siunitx_table_format(['-1.5', '12.34']) == '+2.2'


# --- _loop_column_colspec numeric branches (line 707) ---


def test_loop_column_colspec_non_numeric_returns_centered():
    from easydiffraction.report.data_context import _loop_column_colspec

    assert _loop_column_colspec({'numeric': False}) == 'c'


def test_loop_column_colspec_numeric_without_format_uses_default():
    from easydiffraction.report.data_context import _loop_column_colspec

    assert _loop_column_colspec({'numeric': True}) == 'S[table-format=1.0]'


def test_loop_column_colspec_numeric_with_format():
    from easydiffraction.report.data_context import _loop_column_colspec

    spec = _loop_column_colspec({'numeric': True, 'table_format': '2.3'})
    assert spec == 'S[table-format=2.3]'


# --- _html_markup branches (lines 993-995) ---


def test_html_markup_wraps_bare_latex_backslash():
    from easydiffraction.report.data_context import _html_markup

    assert _html_markup(r'\alpha') == r'\(\alpha\)'


def test_html_markup_returns_plain_text_unchanged():
    from easydiffraction.report.data_context import _html_markup

    assert _html_markup('plain text') == 'plain text'


def test_html_markup_substitutes_inline_math_fragments():
    from easydiffraction.report.data_context import _html_markup

    assert _html_markup(r'value $x$ done') == r'value \(x\) done'


# --- _html_units non-latex display path (lines 963-964) ---


def test_html_units_uses_plain_display_units_when_no_latex_markup():
    from easydiffraction.core.display_handler import DisplayHandler
    from easydiffraction.report.data_context import _html_units

    parameter = _make_parameter(
        'ttheta',
        display_handler=DisplayHandler(display_units='deg', latex_units='degrees'),
    )

    assert _html_units(parameter) == 'deg'


def test_html_units_returns_empty_without_units():
    from easydiffraction.report.data_context import _html_units

    parameter = _make_parameter('plain')

    assert _html_units(parameter) == ''


# --- _skip_category via _skip_cif_serialization (line 400) ---


def test_skip_category_honours_skip_cif_serialization():
    from easydiffraction.report.data_context import _skip_category

    skipped = SimpleNamespace(_skip_cif_serialization=lambda: True)
    kept = SimpleNamespace(_skip_cif_serialization=lambda: False)

    assert _skip_category(skipped, frozenset()) is True
    assert _skip_category(kept, frozenset()) is False


def test_skip_category_honours_skip_codes():
    from easydiffraction.report.data_context import _skip_category

    category = SimpleNamespace(
        _identity=SimpleNamespace(category_code='pd_data'),
    )

    assert _skip_category(category, frozenset({'pd_data'})) is True


# --- _collection_loop_parameters fallback to item.parameters (line 623) ---


def test_collection_loop_parameters_falls_back_to_item_parameters():
    from easydiffraction.report.data_context import _collection_loop_parameters

    item = SimpleNamespace(parameters=['p1', 'p2'])
    category = SimpleNamespace()  # no _cif_loop_parameters

    assert _collection_loop_parameters(category, item) == ['p1', 'p2']


def test_collection_loop_parameters_uses_cif_loop_parameters_hook():
    from easydiffraction.report.data_context import _collection_loop_parameters

    item = SimpleNamespace(parameters=['ignored'])
    category = SimpleNamespace(_cif_loop_parameters=lambda row: ['a', 'b', row])

    assert _collection_loop_parameters(category, item) == ['a', 'b', item]


# --- _merge_label_values dedupes repeated families (branch 596->595) ---


def test_merge_label_values_dedupes_repeated_labels():
    from easydiffraction.report.data_context import _merge_label_values

    assert _merge_label_values(['B11', 'B11', 'U11']) == 'B11 / U11'
    assert _merge_label_values(['B11']) == 'B11'


# --- _analysis_category_contexts skips empty categories (line 367) ---


def test_analysis_category_contexts_skips_empty_and_none_categories():
    from easydiffraction.report.data_context import _analysis_category_contexts

    empty_item = SimpleNamespace(parameters=(), _identity=None, _item_type=None)
    analysis = SimpleNamespace(
        minimizer=empty_item,
        fitting_mode=None,
        fit_result=None,
    )

    assert _analysis_category_contexts(analysis) == []


def test_analysis_category_contexts_includes_populated_categories():
    from easydiffraction.report.data_context import _analysis_category_contexts

    parameter = _make_parameter('n_iterations')
    parameter.value = 42
    category = SimpleNamespace(
        parameters=[parameter],
        _identity=SimpleNamespace(category_code='minimizer'),
        _item_type=None,
    )
    analysis = SimpleNamespace(minimizer=category, fitting_mode=None, fit_result=None)

    contexts = _analysis_category_contexts(analysis)

    assert [context['code'] for context in contexts] == ['minimizer']
    assert contexts[0]['rows'][0]['value'] == '42'


# --- _category_contexts honours explicit skip_codes (branch 378->380) ---


def test_category_contexts_drops_skip_coded_categories():
    from easydiffraction.report.data_context import _category_contexts

    parameter = _make_parameter('value')
    parameter.value = 1.0
    owner = SimpleNamespace(
        categories=[
            SimpleNamespace(
                parameters=[parameter],
                _identity=SimpleNamespace(category_code='keep'),
                _item_type=None,
            ),
            SimpleNamespace(
                parameters=[parameter],
                _identity=SimpleNamespace(category_code='drop'),
                _item_type=None,
            ),
        ],
    )

    contexts = _category_contexts(owner, skip_codes=frozenset({'drop'}))

    assert [context['code'] for context in contexts] == ['keep']


# --- _fit_data_axes_labels exception fallback (lines 1119-1123) ---


class _FallbackXDescriptor:
    @staticmethod
    def resolve_display_units(context):
        del context
        return 'deg'

    @staticmethod
    def resolve_display_name(context):
        del context
        return '2θ'


class _NoUnitsXDescriptor:
    @staticmethod
    def resolve_display_units(context):
        del context
        return ''

    @staticmethod
    def resolve_display_name(context):
        del context
        return 'Q'


def test_fit_data_axes_labels_falls_back_on_attribute_error():
    from easydiffraction.report.data_context import _fit_data_axes_labels

    experiment = SimpleNamespace(type=None)

    labels = _fit_data_axes_labels(experiment, _FallbackXDescriptor())

    assert labels == ['2θ (deg)', 'Intensity (arb. units)']


def test_fit_data_axes_labels_fallback_without_units():
    from easydiffraction.report.data_context import _fit_data_axes_labels

    experiment = SimpleNamespace(type=None)

    labels = _fit_data_axes_labels(experiment, _NoUnitsXDescriptor())

    assert labels == ['Q', 'Intensity (arb. units)']


def test_fit_data_axes_labels_falls_back_on_unknown_combination():
    from easydiffraction.report.data_context import _fit_data_axes_labels

    experiment = SimpleNamespace(
        type=SimpleNamespace(
            sample_form=_Descriptor('nonsense'),
            scattering_type=_Descriptor('nonsense'),
            beam_mode=_Descriptor('nonsense'),
        ),
    )

    labels = _fit_data_axes_labels(experiment, _FallbackXDescriptor())

    assert labels == ['2θ (deg)', 'Intensity (arb. units)']


# --- _single_crystal_fit_data_context (lines 1159-1162, 1175-1188) ---


def _single_crystal_experiment():
    return SimpleNamespace(
        name='heidi',
        type=SimpleNamespace(
            sample_form=_Descriptor('single crystal'),
            scattering_type=_Descriptor('bragg'),
        ),
        refln=SimpleNamespace(
            intensity_calc=np.array([10.0, 20.0]),
            intensity_meas=np.array([11.0, 19.0]),
            intensity_meas_su=np.array([0.5, 0.7]),
        ),
    )


def test_single_crystal_fit_data_context_builds_scatter_payload():
    from easydiffraction.report.data_context import _single_crystal_fit_data_context

    context = _single_crystal_fit_data_context(_single_crystal_experiment())

    assert context['x']['name'] == 'intensity_calc'
    assert context['axes_labels'] == ['Icalc', 'Imeas']
    assert list(context['series']['meas']['values']) == [11.0, 19.0]
    assert list(context['series']['diff']['values']) == [1.0, -1.0]
    assert context['series']['bkg'] is None
    assert context['bragg_tick_sets'] == ()


def test_single_crystal_fit_data_context_returns_none_for_non_single_crystal():
    from easydiffraction.report.data_context import _single_crystal_fit_data_context

    experiment = SimpleNamespace(
        type=SimpleNamespace(
            sample_form=_Descriptor('powder'),
            scattering_type=_Descriptor('bragg'),
        ),
    )

    assert _single_crystal_fit_data_context(experiment) is None


def test_single_crystal_fit_data_context_returns_none_without_refln():
    from easydiffraction.report.data_context import _single_crystal_fit_data_context

    experiment = _single_crystal_experiment()
    experiment.refln = None

    assert _single_crystal_fit_data_context(experiment) is None


def test_single_crystal_fit_data_context_returns_none_for_empty_calc():
    from easydiffraction.report.data_context import _single_crystal_fit_data_context

    experiment = _single_crystal_experiment()
    experiment.refln = SimpleNamespace(
        intensity_calc=np.array([]),
        intensity_meas=np.array([]),
        intensity_meas_su=np.array([]),
    )

    assert _single_crystal_fit_data_context(experiment) is None


# --- _fit_data_context dispatches to single-crystal path (line 1076) ---


def test_fit_data_context_dispatches_to_single_crystal_when_no_x_descriptor():
    from easydiffraction.report.data_context import _fit_data_context

    experiment = _single_crystal_experiment()  # no x_descriptor attribute

    context = _fit_data_context(experiment)

    assert context['x']['name'] == 'intensity_calc'
    assert context['axes_labels'] == ['Icalc', 'Imeas']


# --- _fit_data_bragg_tick_sets early returns (line 1138) ---


def test_fit_data_bragg_tick_sets_empty_for_non_powder_bragg():
    from easydiffraction.report.data_context import _fit_data_bragg_tick_sets

    experiment = SimpleNamespace(
        type=SimpleNamespace(
            sample_form=_Descriptor('single crystal'),
            scattering_type=_Descriptor('bragg'),
        ),
    )

    result = _fit_data_bragg_tick_sets(experiment, x_axis='two_theta', x_values=[1.0, 2.0])

    assert result == ()


def test_fit_data_bragg_tick_sets_empty_for_empty_x_values():
    from easydiffraction.report.data_context import _fit_data_bragg_tick_sets

    experiment = SimpleNamespace(
        type=SimpleNamespace(
            sample_form=_Descriptor('powder'),
            scattering_type=_Descriptor('bragg'),
        ),
    )

    result = _fit_data_bragg_tick_sets(experiment, x_axis='two_theta', x_values=[])

    assert result == ()


# --- _collection_category_context truncation (line 439) ---


def test_collection_category_context_truncates_long_loops():
    from easydiffraction.datablocks.experiment.categories.background.line_segment import (
        LineSegmentBackground,
    )
    from easydiffraction.report.data_context import _REPORT_LOOP_DISPLAY_LIMIT
    from easydiffraction.report.data_context import _collection_category_context

    category = LineSegmentBackground()
    for index in range(_REPORT_LOOP_DISPLAY_LIMIT + 6):
        category.create(id=str(index), x=float(index), y=float(index) + 0.5)

    context = _collection_category_context(category, truncate=True)

    assert len(context['rows']) == _REPORT_LOOP_DISPLAY_LIMIT + 1
    ellipsis_row = context['rows'][_REPORT_LOOP_DISPLAY_LIMIT // 2]
    assert ellipsis_row['cells'][0]['value'] == '...'


def test_collection_category_context_keeps_short_loops_untruncated():
    from easydiffraction.datablocks.experiment.categories.background.line_segment import (
        LineSegmentBackground,
    )
    from easydiffraction.report.data_context import _collection_category_context

    category = LineSegmentBackground()
    category.create(id='1', x=1.0, y=2.0)
    category.create(id='2', x=2.0, y=3.0)

    context = _collection_category_context(category, truncate=True)

    assert len(context['rows']) == 2
    assert all(row['cells'][0]['value'] != '...' for row in context['rows'])


# --- _category_contexts default frozenset arguments (lines 378->380) ---


def test_category_contexts_handles_owner_without_categories():
    from easydiffraction.report.data_context import _category_contexts

    owner = SimpleNamespace()  # no `categories` attribute

    assert _category_contexts(owner) == []
