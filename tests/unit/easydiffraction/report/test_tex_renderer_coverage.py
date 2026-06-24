# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Supplementary coverage tests for the TeX report renderer.

These tests target helper functions and edge-case branches of
``easydiffraction.report.tex_renderer`` that the primary test file does
not exercise: path resolution, single-crystal scatter assets,
reflection-category CSV writing from live experiment objects, CSV
fallback/validation behaviour, and the TeX escaping/formatting filters.
"""

from __future__ import annotations

import csv
import types

import pytest


def _read_csv(path) -> list[list[str]]:
    """Return parsed CSV rows from ``path``."""
    with path.open(newline='', encoding='utf-8') as handle:
        return list(csv.reader(handle))


# ---------------------------------------------------------------------------
# tex_report_path
# ---------------------------------------------------------------------------


def test_tex_report_path_returns_explicit_path(tmp_path):
    from easydiffraction.report.tex_renderer import tex_report_path

    explicit = tmp_path / 'custom' / 'out.tex'
    result = tex_report_path(object(), explicit)

    assert result == explicit


def test_tex_report_path_builds_from_project_info(tmp_path):
    from easydiffraction.report.tex_renderer import tex_report_path

    metadata = types.SimpleNamespace(path=str(tmp_path))
    project = types.SimpleNamespace(metadata=metadata, name='myproj')

    result = tex_report_path(project)

    assert result == tmp_path / 'reports' / 'tex' / 'myproj.tex'


def test_tex_report_path_uses_default_name_when_missing(tmp_path):
    from easydiffraction.report.tex_renderer import tex_report_path

    metadata = types.SimpleNamespace(path=str(tmp_path))
    project = types.SimpleNamespace(metadata=metadata)

    result = tex_report_path(project)

    assert result.name == 'project.tex'


def test_tex_report_path_raises_when_project_unsaved():
    from easydiffraction.report.tex_renderer import tex_report_path

    project = types.SimpleNamespace(metadata=types.SimpleNamespace(path=None))

    with pytest.raises(FileNotFoundError, match='Save the project first'):
        tex_report_path(project)


def test_tex_report_path_raises_when_project_has_no_info():
    from easydiffraction.report.tex_renderer import tex_report_path

    with pytest.raises(FileNotFoundError):
        tex_report_path(object())


# ---------------------------------------------------------------------------
# _safe_asset_stem / _fit_csv_filename / _structure_asset_stem
# ---------------------------------------------------------------------------


def test_safe_asset_stem_sanitizes_special_characters():
    from easydiffraction.report.tex_renderer import _safe_asset_stem

    assert _safe_asset_stem('hr pt/01') == 'hr_pt_01'
    assert _safe_asset_stem('keep-_ok') == 'keep-_ok'


def test_safe_asset_stem_falls_back_to_experiment_when_empty():
    from easydiffraction.report.tex_renderer import _safe_asset_stem

    assert _safe_asset_stem('***') == 'experiment'
    assert _safe_asset_stem('') == 'experiment'


def test_fit_csv_filename_uses_safe_stem():
    from easydiffraction.report.tex_renderer import _fit_csv_filename

    assert _fit_csv_filename('a b') == 'a_b.csv'


def test_structure_asset_stem_prefixes_struct():
    from easydiffraction.report.tex_renderer import _structure_asset_stem

    assert _structure_asset_stem('na cl') == 'struct_na_cl'


# ---------------------------------------------------------------------------
# Path helper collections skip non-dict / fit_data-less entries
# ---------------------------------------------------------------------------


def test_fit_csv_and_figure_paths_skip_experiments_without_fit_data():
    from easydiffraction.report.tex_renderer import _fit_csv_paths
    from easydiffraction.report.tex_renderer import _fit_figure_paths

    context = {
        'experiments': [
            'not-a-dict',
            {'id': 'no_fit'},
            {'id': 'with fit', 'fit_data': {}},
        ]
    }

    csv_paths = _fit_csv_paths(context)
    figure_paths = _fit_figure_paths(context)

    assert csv_paths == {'with fit': 'data/with_fit.csv'}
    assert figure_paths == {'with fit': 'data/with_fit.pdf'}


def test_structure_figure_paths_skips_non_dict_and_uses_id():
    from easydiffraction.report.tex_renderer import _structure_figure_paths

    context = {
        'structures': [
            'not-a-dict',
            {'id': 'na cl'},
            {},  # missing id -> fallback
        ]
    }

    paths = _structure_figure_paths(context)

    assert paths == {
        'na cl': 'data/struct_na_cl.png',
        'structure': 'data/struct_structure.png',
    }


def test_structure_figure_paths_empty_when_no_structures():
    from easydiffraction.report.tex_renderer import _structure_figure_paths

    assert _structure_figure_paths({}) == {}


# ---------------------------------------------------------------------------
# _experiment_contexts
# ---------------------------------------------------------------------------


def test_experiment_contexts_filters_non_dict_entries():
    from easydiffraction.report.tex_renderer import _experiment_contexts

    context = {'experiments': [{'id': 'a'}, 'bad', 7]}

    assert _experiment_contexts(context) == [{'id': 'a'}]


def test_experiment_contexts_returns_empty_for_non_list():
    from easydiffraction.report.tex_renderer import _experiment_contexts

    assert _experiment_contexts({'experiments': 'oops'}) == []
    assert _experiment_contexts({}) == []


# ---------------------------------------------------------------------------
# _fit_x_field
# ---------------------------------------------------------------------------


def test_fit_x_field_prefers_category_field():
    from easydiffraction.report.tex_renderer import _fit_x_field

    category_values = {'d_spacing': [1.0, 2.0]}
    fit_data = {'x': {'name': 'two_theta'}}

    assert _fit_x_field(category_values, fit_data) == 'd_spacing'


def test_fit_x_field_falls_back_to_x_name():
    from easydiffraction.report.tex_renderer import _fit_x_field

    fit_data = {'x': {'name': 'time_of_flight'}}

    assert _fit_x_field({}, fit_data) == 'time_of_flight'


def test_fit_x_field_defaults_to_two_theta():
    from easydiffraction.report.tex_renderer import _fit_x_field

    fit_data = {'x': {'name': 'unrecognized'}}

    assert _fit_x_field({}, fit_data) == 'two_theta'


# ---------------------------------------------------------------------------
# _fit_csv_values / _series_values_or_empty / _empty_csv_values
# ---------------------------------------------------------------------------


def test_fit_csv_values_returns_category_values_when_populated():
    from easydiffraction.report.tex_renderer import _fit_csv_values

    category_values = {'point_id': ['1', '2']}

    assert _fit_csv_values(category_values, 'point_id', ['x', 'y']) == ['1', '2']


def test_fit_csv_values_uses_fallback_when_missing_or_all_empty():
    from easydiffraction.report.tex_renderer import _fit_csv_values

    fallback = ['a', 'b']

    assert _fit_csv_values({}, 'point_id', fallback) == fallback
    assert _fit_csv_values({'point_id': [None, '']}, 'point_id', fallback) == fallback


def test_series_values_or_empty_handles_none_and_values():
    from easydiffraction.report.tex_renderer import _series_values_or_empty

    assert _series_values_or_empty(None, 3) == ['', '', '']
    assert _series_values_or_empty([1, 2], 2) == [1, 2]


# ---------------------------------------------------------------------------
# _is_csv_empty
# ---------------------------------------------------------------------------


def test_is_csv_empty_classification():
    from easydiffraction.report.tex_renderer import _is_csv_empty

    assert _is_csv_empty(None) is True
    assert _is_csv_empty('') is True
    assert _is_csv_empty('x') is False
    assert _is_csv_empty(0) is False


# ---------------------------------------------------------------------------
# _validate_fit_csv_columns / _write_csv
# ---------------------------------------------------------------------------


def test_validate_fit_csv_columns_raises_on_mismatch():
    from easydiffraction.report.tex_renderer import _validate_fit_csv_columns

    columns = [
        ('_pd_proc.2theta_scan', [1.0, 2.0]),
        ('_pd_meas.intensity_total', [10.0]),
    ]

    with pytest.raises(ValueError, match="experiment 'hrpt'"):
        _validate_fit_csv_columns('hrpt', columns)


def test_validate_fit_csv_columns_accepts_equal_lengths():
    from easydiffraction.report.tex_renderer import _validate_fit_csv_columns

    columns = [
        ('x', [1.0, 2.0]),
        ('y', [3.0, 4.0]),
    ]

    # No exception means the columns validated.
    assert _validate_fit_csv_columns('hrpt', columns) is None


def test_write_csv_emits_header_and_rows(tmp_path):
    from easydiffraction.report.tex_renderer import _write_csv

    path = tmp_path / 'out.csv'
    columns = [
        ('x', [1, 2]),
        ('y', ['a', 'b']),
    ]
    _write_csv(path, 'hrpt', columns)

    rows = _read_csv(path)
    assert rows[0] == ['x', 'y']
    assert rows[1] == ['1', 'a']
    assert rows[2] == ['2', 'b']


# ---------------------------------------------------------------------------
# _context_category_values / _context_loop_values
# ---------------------------------------------------------------------------


def test_context_category_values_reads_loop_cells():
    from easydiffraction.report.tex_renderer import _context_category_values

    experiment = {
        'categories': [
            'ignored-non-dict',
            {'code': 'other', 'columns': [], 'rows': []},
            {
                'code': 'pd_data',
                'columns': [{'name': 'point_id'}, {'name': 'two_theta'}],
                'rows': [
                    {'cells': [{'value': '1'}, {'value': 10.0}]},
                    {'cells': [{'value': '2'}, {'value': 20.0}]},
                ],
            },
        ]
    }

    values = _context_category_values(experiment, 'pd_data')

    assert values == {'point_id': ['1', '2'], 'two_theta': [10.0, 20.0]}


def test_context_category_values_returns_empty_when_missing():
    from easydiffraction.report.tex_renderer import _context_category_values

    assert _context_category_values({'categories': []}, 'pd_data') == {}
    assert _context_category_values({}, 'pd_data') == {}


def test_context_loop_values_skips_non_dict_rows_and_cells():
    from easydiffraction.report.tex_renderer import _context_loop_values

    category = {
        'columns': [{'name': 'a'}, 'bad-column'],
        'rows': [
            'not-a-dict',
            {'cells': ['not-a-dict-cell']},
        ],
    }

    values = _context_loop_values(category)

    assert values == {'a': ['']}


# ---------------------------------------------------------------------------
# _category_values / live-experiment source path
# ---------------------------------------------------------------------------


class _FakeParameter:
    def __init__(self, name, value):
        self.name = name
        self.value = value


class _FakeItem:
    def __init__(self, parameters):
        self.parameters = parameters


class _FakeCategoryValues:
    """Iterable category exposing live loop rows and an identity code."""

    def __init__(self, code, items):
        self._identity = types.SimpleNamespace(category_code=code)
        self._items = items

    def values(self):
        return list(self._items)


class _FakeSourceExperiment:
    def __init__(self, categories):
        self.categories = categories


def test_source_category_values_extracts_raw_values():
    from easydiffraction.report.tex_renderer import _category_values

    items = [
        _FakeItem([_FakeParameter('two_theta', 10.0), _FakeParameter('point_id', 1)]),
        _FakeItem([_FakeParameter('two_theta', 20.0), _FakeParameter('point_id', 2)]),
    ]
    category = _FakeCategoryValues('pd_data', items)
    source = _FakeSourceExperiment([category])

    values = _category_values(source, {}, code='pd_data')

    assert values == {'two_theta': [10.0, 20.0], 'point_id': [1, 2]}


def test_source_category_values_falls_back_to_context_when_empty():
    from easydiffraction.report.tex_renderer import _category_values

    category = _FakeCategoryValues('pd_data', [])  # no items -> {}
    source = _FakeSourceExperiment([category])
    experiment = {
        'categories': [
            {
                'code': 'pd_data',
                'columns': [{'name': 'point_id'}],
                'rows': [{'cells': [{'value': '1'}]}],
            }
        ]
    }

    values = _category_values(source, experiment, code='pd_data')

    assert values == {'point_id': ['1']}


def test_source_category_returns_none_when_no_matching_code():
    from easydiffraction.report.tex_renderer import _source_category

    category = _FakeCategoryValues('other', [])
    source = _FakeSourceExperiment([category])

    assert _source_category(source, 'pd_data') is None


def test_source_category_code_falls_back_to_item_type():
    from easydiffraction.report.tex_renderer import _source_category_code

    item_type = types.SimpleNamespace(_category_code='refln')
    category = types.SimpleNamespace(_identity=None, _item_type=item_type)

    assert _source_category_code(category) == 'refln'


def test_source_category_values_returns_empty_when_values_not_callable():
    from easydiffraction.report.tex_renderer import _source_category_values

    category = types.SimpleNamespace(
        _identity=types.SimpleNamespace(category_code='pd_data'),
        values=None,
    )
    source = _FakeSourceExperiment([category])

    assert _source_category_values(source, 'pd_data') == {}


def test_source_category_values_returns_empty_when_no_matching_category():
    from easydiffraction.report.tex_renderer import _source_category_values

    category = _FakeCategoryValues('other', [])
    source = _FakeSourceExperiment([category])

    assert _source_category_values(source, 'pd_data') == {}


def test_category_parameters_uses_cif_loop_parameters_hook():
    from easydiffraction.report.tex_renderer import _category_parameters

    sentinel = [_FakeParameter('h', 1)]
    category = types.SimpleNamespace(_cif_loop_parameters=lambda item: sentinel)

    assert _category_parameters(category, object()) == sentinel


def test_raw_value_unwraps_descriptor():
    from easydiffraction.report.tex_renderer import _raw_value

    assert _raw_value(_FakeParameter('a', 7)) == 7
    assert _raw_value(5) == 5


# ---------------------------------------------------------------------------
# _write_bragg_csvs via live refln category
# ---------------------------------------------------------------------------


def _refln_source_experiment():
    """Return a live experiment exposing a refln loop category."""
    items = [
        _FakeItem([
            _FakeParameter('structure_id', 'phase-a'),
            _FakeParameter('two_theta', 12.0),
            _FakeParameter('index_h', 1),
            _FakeParameter('index_k', 0),
            _FakeParameter('index_l', 0),
        ]),
        _FakeItem([
            _FakeParameter('structure_id', ''),  # empty -> skipped
            _FakeParameter('two_theta', 13.0),
            _FakeParameter('index_h', 1),
            _FakeParameter('index_k', 1),
            _FakeParameter('index_l', 0),
        ]),
        _FakeItem([
            _FakeParameter('structure_id', 'phase-b'),
            _FakeParameter('two_theta', 14.0),
            _FakeParameter('index_h', 2),
            _FakeParameter('index_k', 0),
            _FakeParameter('index_l', 0),
        ]),
    ]
    category = _FakeCategoryValues('refln', items)
    return _FakeSourceExperiment([category])


def test_write_bragg_csvs_from_refln_category_splits_by_phase(tmp_path):
    from easydiffraction.report.tex_renderer import _write_bragg_csvs

    csvs = _write_bragg_csvs(
        'hrpt',
        {},
        _refln_source_experiment(),
        {'bragg_tick_sets': ()},
        tmp_path,
    )

    assert set(csvs) == {'phase-a', 'phase-b'}
    assert csvs['phase-a']['x_column'] == '_refln.two_theta'

    phase_a_path = tmp_path / 'data' / csvs['phase-a']['filename']
    rows = _read_csv(phase_a_path)
    header = rows[0]
    assert '_pd_refln.phase_id' in header
    assert '_refln.two_theta' in header
    # Only the single phase-a row is written.
    assert len(rows) == 2
    assert rows[1][header.index('_refln.two_theta')] == '12.0'


def test_write_refln_category_csvs_empty_without_structure_id(tmp_path):
    from easydiffraction.report.tex_renderer import _write_refln_category_csvs

    values = {'two_theta': [10.0, 20.0]}  # no structure_id

    assert _write_refln_category_csvs('hrpt', values, tmp_path) == {}


def test_refln_x_column_selection():
    from easydiffraction.report.tex_renderer import _refln_x_column

    assert _refln_x_column({'two_theta': [1.0]}) == '_refln.two_theta'
    assert _refln_x_column({'time_of_flight': [1.0]}) == '_refln.time_of_flight'
    assert _refln_x_column({}) == '_refln.two_theta'


def test_write_bragg_csvs_falls_back_to_tick_sets(tmp_path):
    import numpy as np

    from easydiffraction.display.plotters.base import BraggTickSet
    from easydiffraction.report.tex_renderer import _write_bragg_csvs

    tick_set = BraggTickSet(
        structure_id='phase-a',
        x=np.array([1.5, 2.5]),
        h=np.array([1, 2]),
        k=np.array([0, 0]),
        ell=np.array([1, 1]),
        f_squared_calc=np.array([100.0, 50.0]),
        f_calc=np.array([10.0, 7.0]),
    )

    csvs = _write_bragg_csvs(
        'hrpt',
        {},  # no context refln category
        None,  # no source experiment
        {'bragg_tick_sets': (tick_set,)},
        tmp_path,
    )

    assert set(csvs) == {'phase-a'}
    rows = _read_csv(tmp_path / 'data' / csvs['phase-a']['filename'])
    header = rows[0]
    assert header[-1] == '_refln.two_theta'
    assert rows[1][header.index('_refln.two_theta')] == '1.5'
    assert len(rows) == 3


# ---------------------------------------------------------------------------
# _bragg_tick_sources
# ---------------------------------------------------------------------------


def test_bragg_tick_sources_skips_phases_without_csv():
    import numpy as np

    from easydiffraction.display.plotters.base import BraggTickSet
    from easydiffraction.report.tex_renderer import _bragg_tick_sources

    tick_set = BraggTickSet(
        structure_id='phase-a',
        x=np.array([1.0]),
        h=np.array([1]),
        k=np.array([0]),
        ell=np.array([0]),
        f_squared_calc=np.array([1.0]),
        f_calc=np.array([1.0]),
    )
    fit_data = {'bragg_tick_sets': (tick_set,)}

    # bragg_csvs has no entry for phase-a -> skipped.
    assert _bragg_tick_sources(fit_data, {}) == []

    sources = _bragg_tick_sources(
        fit_data,
        {'phase-a': {'filename': 'f.csv', 'x_column': '_refln.two_theta'}},
    )
    assert sources == [
        {
            'structure_id': 'phase-a',
            'csv_filename': 'f.csv',
            'x_column': '_refln.two_theta',
        }
    ]


# ---------------------------------------------------------------------------
# _fit_plot_ranges
# ---------------------------------------------------------------------------


def test_fit_plot_ranges_skips_missing_and_scatter_fit_data():
    from easydiffraction.report.tex_renderer import _fit_plot_ranges

    context = {
        'experiments': [
            {'id': 'no_fit'},
            {
                'id': 'scatter',
                'fit_data': {
                    'x': {'name': 'intensity_calc', 'values': [1.0]},
                    'series': {'meas': {'values': [1.0], 'su': None}},
                },
            },
            {
                'id': 'powder',
                'fit_data': {
                    'x': {'name': 'two_theta', 'values': [1.0, 2.0]},
                    'series': {
                        'meas': {'values': [10.0, 12.0], 'su': None},
                        'calc': {'values': [9.0, 11.0]},
                    },
                },
            },
        ]
    }

    ranges = _fit_plot_ranges(context)

    assert set(ranges) == {'powder'}
    assert 'x_min' in ranges['powder']


# ---------------------------------------------------------------------------
# Single-crystal scatter assets via save_tex_report
# ---------------------------------------------------------------------------


def _scatter_context():
    """Return a report context exercising the scatter fit branch."""
    from copy import deepcopy

    base = {
        'project': {
            'name': 'sc_project',
            'title': 'SC Project',
            'description': '',
            'n_phases': 0,
            'n_experiments': 1,
        },
        'metadata': {
            'generated_at': '2026-05-26T00:00:00Z',
            'easydiffraction_version': '0.0',
        },
        'refinement': {
            'fit_result': {
                'reduced_chi_square': None,
                'r_factor_all': None,
                'wr_factor_all': None,
            },
            'parameters': {'free': 0, 'total': 0},
            'constraints': 0,
            'rows': [],
            'colspec': 'lS[table-format=1.0]',
        },
        'software': {
            'framework': {'name': 'EasyDiffraction', 'version': '0.0'},
            'calculator': {'name': 'cryspy', 'version': '0.0'},
            'minimizer': {'name': 'lmfit', 'version': '0.0'},
        },
        'analysis': {
            'software': {
                'framework': {'name': 'EasyDiffraction', 'version': '0.0'},
                'calculator': {'name': 'cryspy', 'version': '0.0'},
                'minimizer': {'name': 'lmfit', 'version': '0.0'},
            },
            'categories': [],
        },
        'structures': [],
        'experiments': [
            {
                'id': 'sx',
                'type': {
                    'sample_form': 'single crystal',
                    'radiation_probe': 'neutron',
                    'beam_mode': 'constant wavelength',
                    'scattering_type': 'bragg',
                },
                'calculator': {'type': 'cryspy'},
                'diffrn': {},
                'diffrn_latex': {},
                'categories': [],
                'fit_data': {
                    'x': {
                        'name': 'intensity_calc',
                        'values': [1.0, 2.0, 3.0],
                    },
                    'axes_labels': ['Icalc', 'Imeas'],
                    'series': {
                        'meas': {
                            'values': [1.1, 1.9, 3.2],
                            'su': [0.1, 0.2, 0.3],
                        },
                    },
                },
            }
        ],
        'figures': {'fit_per_experiment': {}},
    }
    return deepcopy(base)


def test_save_tex_report_writes_scatter_csv_and_figure(tmp_path):
    from easydiffraction.report.tex_renderer import save_tex_report

    tex_path = tmp_path / 'reports' / 'tex' / 'report.tex'
    save_tex_report(object(), _scatter_context(), path=tex_path)

    csv_rows = _read_csv(tex_path.parent / 'data' / 'sx.csv')
    assert csv_rows[0] == ['icalc', 'imeas', 'imeas_su']
    assert csv_rows[1] == ['1.0', '1.1', '0.1']
    assert len(csv_rows) == 4

    figure_tex = (tex_path.parent / 'data' / 'sx.tex').read_text(encoding='utf-8')
    assert r'\documentclass[border=2pt]{standalone}' in figure_tex
    assert 'x={icalc}' in figure_tex
    assert 'y={imeas}' in figure_tex
    assert 'y error={imeas_su}' in figure_tex
    # No Bragg-tick group plot for a scatter figure.
    assert r'\begin{groupplot}' not in figure_tex


def test_save_tex_report_scatter_without_su_writes_zero_column(tmp_path):
    from easydiffraction.report.tex_renderer import save_tex_report

    context = _scatter_context()
    context['experiments'][0]['fit_data']['series']['meas']['su'] = None

    tex_path = tmp_path / 'reports' / 'tex' / 'report.tex'
    save_tex_report(object(), context, path=tex_path)

    csv_rows = _read_csv(tex_path.parent / 'data' / 'sx.csv')
    assert csv_rows[0] == ['icalc', 'imeas', 'imeas_su']
    # su absent -> zero-filled column.
    assert [row[2] for row in csv_rows[1:]] == ['0.0', '0.0', '0.0']


def test_save_tex_report_skips_experiment_without_fit_data(tmp_path):
    from easydiffraction.report.tex_renderer import save_tex_report

    context = _scatter_context()
    # Prepend an experiment that carries no fit_data; it must be skipped
    # by _write_fit_assets without producing CSV/figure assets.
    no_fit_experiment = {
        'id': 'no_fit',
        'type': context['experiments'][0]['type'],
        'calculator': {'type': 'cryspy'},
        'diffrn': {},
        'diffrn_latex': {},
        'categories': [],
    }
    context['experiments'].insert(0, no_fit_experiment)

    tex_path = tmp_path / 'reports' / 'tex' / 'report.tex'
    save_tex_report(object(), context, path=tex_path)

    data_dir = tex_path.parent / 'data'
    # The fit-data experiment still produced its assets.
    assert (data_dir / 'sx.csv').exists()
    # The fit-data-less experiment produced none.
    assert not (data_dir / 'no_fit.csv').exists()


def test_is_scatter_fit_data_detection():
    from easydiffraction.report.tex_renderer import _is_scatter_fit_data

    assert _is_scatter_fit_data({'x': {'name': 'intensity_calc'}}) is True
    assert _is_scatter_fit_data({'x': {'name': 'two_theta'}}) is False
    assert _is_scatter_fit_data({}) is False


# ---------------------------------------------------------------------------
# TeX formatting filters
# ---------------------------------------------------------------------------


def test_tex_number_formats_and_falls_back():
    from easydiffraction.report.tex_renderer import _tex_number

    assert _tex_number(1.23456789) == '1.23457'
    assert _tex_number(42) == '42'
    # Booleans are escaped as text, not formatted as numbers.
    truthy = True
    assert _tex_number(truthy) == 'True'
    assert _tex_number('n/a') == 'n/a'


def test_tex_markup_preserves_explicit_tex_and_escapes_plain():
    from easydiffraction.report.tex_renderer import _tex_markup

    assert _tex_markup(None) == ''
    assert _tex_markup(r'$\alpha$') == r'$\alpha$'
    assert _tex_markup(r'\frac{1}{2}') == r'\frac{1}{2}'
    assert _tex_markup('a_b') == r'a\_b'


def test_tex_unit_handles_none_empty_and_math():
    from easydiffraction.report.tex_renderer import _tex_unit

    assert _tex_unit(None) == ''
    assert _tex_unit('') == ''
    assert _tex_unit('kPa') == 'kPa'
    # A unit containing TeX is wrapped in math mode with angstrom normalized.
    assert _tex_unit(r'\AA') == r'$\mathring{\mathrm{A}}$'


def test_tex_unit_math_normalizes_angstrom_variants():
    from easydiffraction.report.tex_renderer import _tex_unit_math

    assert _tex_unit_math(r'\mathrm{\AA}') == r'\mathring{\mathrm{A}}'
    assert _tex_unit_math(r'\AA') == r'\mathring{\mathrm{A}}'


def test_tex_degree_unit_math_replaces_markers():
    from easydiffraction.report.tex_renderer import _tex_degree_unit_math

    assert _tex_degree_unit_math(r'^\circ{}^2') == r'\mathrm{deg}^2'
    assert _tex_degree_unit_math(r'^\circ^{2}') == r'\mathrm{deg}^2'
    assert _tex_degree_unit_math(r'^\circ{}') == r'\mathrm{deg}'
    assert _tex_degree_unit_math(r'^\circ') == r'\mathrm{deg}'


def test_tex_axis_label_replaces_symbols():
    from easydiffraction.report.tex_renderer import _tex_axis_label

    assert _tex_axis_label(None) == ''
    label = _tex_axis_label('2θ (degree) λ μ Å⁻¹ ²')
    assert r'$\theta$' in label
    assert 'deg' in label
    assert r'$\lambda$' in label
    assert r'$\mu$' in label
    assert r'\AA{}' in label
    assert '$^{-1}$' in label
    assert '$^2$' in label


def test_tex_escape_handles_specials_collections_and_newlines():
    from easydiffraction.report.tex_renderer import _tex_escape

    assert _tex_escape(None) == ''
    assert _tex_escape('a & b % c') == r'a \& b \% c'
    assert _tex_escape(['x', None, 'y']) == 'x, y'
    assert _tex_escape(('p', 'q')) == 'p, q'
    # Paragraph break vs single newline.
    assert _tex_escape('a\n\nb') == r'a\par b'
    assert _tex_escape('a\r\nb') == 'a b'
