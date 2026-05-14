# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for sequential fitting helper functions."""

from __future__ import annotations

import contextlib
import csv
from types import SimpleNamespace

import pytest

from easydiffraction.analysis.sequential import SequentialFitTemplate
from easydiffraction.analysis.sequential import _META_COLUMNS
from easydiffraction.analysis.sequential import _append_to_csv
from easydiffraction.analysis.sequential import _build_csv_header
from easydiffraction.analysis.sequential import _read_csv_for_recovery
from easydiffraction.analysis.sequential import _write_csv_header
from easydiffraction.display.progress import ACTIVITY_LABEL_FITTING
from easydiffraction.utils.enums import VerbosityEnum


# ------------------------------------------------------------------
#  Fixture: a minimal template
# ------------------------------------------------------------------


def _minimal_template(
    free_names=None,
    diffrn_fields=None,
):
    if free_names is None:
        free_names = ['cell.a', 'cell.b']
    if diffrn_fields is None:
        diffrn_fields = []
    return SequentialFitTemplate(
        structure_cif='',
        experiment_cif='',
        initial_params={},
        free_param_unique_names=free_names,
        alias_defs=[],
        constraint_defs=[],
        constraints_enabled=False,
        minimizer_tag='lmfit',
        calculator_tag='cryspy',
        diffrn_field_names=diffrn_fields,
    )


# ------------------------------------------------------------------
#  _build_csv_header
# ------------------------------------------------------------------


class TestBuildCsvHeader:
    def test_meta_columns_first(self):
        template = _minimal_template(free_names=[], diffrn_fields=[])
        header = _build_csv_header(template)
        assert header == list(_META_COLUMNS)

    def test_diffrn_fields_after_meta(self):
        template = _minimal_template(
            free_names=[],
            diffrn_fields=['ambient_temperature'],
        )
        header = _build_csv_header(template)
        assert header[-1] == 'diffrn.ambient_temperature'

    def test_param_columns_with_uncertainty(self):
        template = _minimal_template(free_names=['cell.a'])
        header = _build_csv_header(template)
        assert 'cell.a' in header
        assert 'cell.a.uncertainty' in header
        # Uncertainty follows value
        idx = header.index('cell.a')
        assert header[idx + 1] == 'cell.a.uncertainty'

    def test_full_header_order(self):
        template = _minimal_template(
            free_names=['p1', 'p2'],
            diffrn_fields=['temp'],
        )
        header = _build_csv_header(template)
        expected = [
            *_META_COLUMNS,
            'diffrn.temp',
            'p1',
            'p1.uncertainty',
            'p2',
            'p2.uncertainty',
        ]
        assert header == expected


# ------------------------------------------------------------------
#  _write_csv_header / _append_to_csv
# ------------------------------------------------------------------


class TestCsvWriteAndAppend:
    def test_write_creates_file_with_header(self, tmp_path):
        csv_path = tmp_path / 'results.csv'
        header = ['file_path', 'chi_squared', 'param_a']
        _write_csv_header(csv_path, header)

        with csv_path.open() as f:
            reader = csv.reader(f)
            first_row = next(reader)
        assert first_row == header

    def test_append_adds_rows(self, tmp_path):
        csv_path = tmp_path / 'results.csv'
        header = ['file_path', 'value']
        _write_csv_header(csv_path, header)

        _append_to_csv(
            csv_path,
            header,
            [
                {'file_path': 'a.dat', 'value': 1.0},
                {'file_path': 'b.dat', 'value': 2.0},
            ],
        )

        with csv_path.open() as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 2
        assert rows[0]['file_path'] == 'a.dat'
        assert rows[1]['value'] == '2.0'

    def test_append_ignores_extra_keys(self, tmp_path):
        csv_path = tmp_path / 'results.csv'
        header = ['file_path']
        _write_csv_header(csv_path, header)

        _append_to_csv(
            csv_path,
            header,
            [
                {'file_path': 'a.dat', 'extra_key': 'ignored'},
            ],
        )

        with csv_path.open() as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 1
        assert 'extra_key' not in rows[0]


# ------------------------------------------------------------------
#  _read_csv_for_recovery
# ------------------------------------------------------------------


class TestReadCsvForRecovery:
    def test_returns_empty_when_no_file(self, tmp_path):
        csv_path = tmp_path / 'nonexistent.csv'
        fitted, params = _read_csv_for_recovery(csv_path)
        assert fitted == set()
        assert params is None

    def test_returns_fitted_file_paths(self, tmp_path):
        csv_path = tmp_path / 'results.csv'
        header = [*_META_COLUMNS, 'cell.a', 'cell.a.uncertainty']
        _write_csv_header(csv_path, header)
        _append_to_csv(
            csv_path,
            header,
            [
                {
                    'file_path': '/data/a.dat',
                    'fit_success': 'True',
                    'chi_squared': '5.0',
                    'reduced_chi_squared': '2.5',
                    'n_iterations': '10',
                    'cell.a': '3.89',
                    'cell.a.uncertainty': '0.01',
                },
                {
                    'file_path': '/data/b.dat',
                    'fit_success': 'False',
                    'chi_squared': '',
                    'reduced_chi_squared': '',
                    'n_iterations': '0',
                    'cell.a': '',
                    'cell.a.uncertainty': '',
                },
            ],
        )

        fitted, _params = _read_csv_for_recovery(csv_path)
        assert fitted == {'/data/a.dat', '/data/b.dat'}

    def test_returns_last_successful_params(self, tmp_path):
        csv_path = tmp_path / 'results.csv'
        header = [*_META_COLUMNS, 'cell.a', 'cell.a.uncertainty']
        _write_csv_header(csv_path, header)
        _append_to_csv(
            csv_path,
            header,
            [
                {
                    'file_path': 'a.dat',
                    'fit_success': 'True',
                    'chi_squared': '5.0',
                    'reduced_chi_squared': '2.5',
                    'n_iterations': '10',
                    'cell.a': '3.89',
                    'cell.a.uncertainty': '0.01',
                },
                {
                    'file_path': 'b.dat',
                    'fit_success': 'True',
                    'chi_squared': '4.0',
                    'reduced_chi_squared': '2.0',
                    'n_iterations': '8',
                    'cell.a': '3.90',
                    'cell.a.uncertainty': '0.02',
                },
            ],
        )

        _, params = _read_csv_for_recovery(csv_path)
        assert params is not None
        # Should return the LAST successful row's params
        assert params['cell.a'] == pytest.approx(3.90)

    def test_skips_meta_columns_and_diffrn_and_uncertainty(self, tmp_path):
        csv_path = tmp_path / 'results.csv'
        header = [
            *_META_COLUMNS,
            'diffrn.temp',
            'cell.a',
            'cell.a.uncertainty',
        ]
        _write_csv_header(csv_path, header)
        _append_to_csv(
            csv_path,
            header,
            [
                {
                    'file_path': 'a.dat',
                    'fit_success': 'True',
                    'chi_squared': '5.0',
                    'reduced_chi_squared': '2.5',
                    'n_iterations': '10',
                    'diffrn.temp': '300',
                    'cell.a': '3.89',
                    'cell.a.uncertainty': '0.01',
                },
            ],
        )

        _, params = _read_csv_for_recovery(csv_path)
        assert params is not None
        assert 'cell.a' in params
        # Meta columns, diffrn, and uncertainty should be excluded
        assert 'file_path' not in params
        assert 'fit_success' not in params
        assert 'diffrn.temp' not in params
        assert 'cell.a.uncertainty' not in params

    def test_returns_none_params_when_no_successful_rows(self, tmp_path):
        csv_path = tmp_path / 'results.csv'
        header = [*_META_COLUMNS, 'cell.a', 'cell.a.uncertainty']
        _write_csv_header(csv_path, header)
        _append_to_csv(
            csv_path,
            header,
            [
                {
                    'file_path': 'a.dat',
                    'fit_success': 'False',
                    'chi_squared': '',
                    'reduced_chi_squared': '',
                    'n_iterations': '0',
                    'cell.a': '',
                    'cell.a.uncertainty': '',
                },
            ],
        )

        _, params = _read_csv_for_recovery(csv_path)
        assert params is None


# ------------------------------------------------------------------
#  SequentialFitTemplate
# ------------------------------------------------------------------


class TestSequentialFitTemplate:
    def test_is_frozen(self):
        template = _minimal_template()
        with pytest.raises(AttributeError):
            template.minimizer_tag = 'bumps'

    def test_fields_accessible(self):
        template = _minimal_template(
            free_names=['cell.a'],
            diffrn_fields=['temp'],
        )
        assert template.free_param_unique_names == ['cell.a']
        assert template.diffrn_field_names == ['temp']
        assert template.minimizer_tag == 'lmfit'
        assert template.calculator_tag == 'cryspy'


def test_fit_sequential_short_starts_and_stops_shared_indicator(monkeypatch, tmp_path):
    import easydiffraction.analysis.sequential as sequential_mod

    events: list[tuple[object, ...]] = []
    template = _minimal_template()

    class FakeIndicator:
        def __init__(self, label, *, verbosity):
            events.append(('init', label, verbosity))

        def start(self):
            events.append(('start',))

        def update(self):
            events.append(('update',))

        def stop(self):
            events.append(('stop',))

    def fake_run_fit_loop(
        pool_cm, chunks, template_arg, csv_info, extract_diffrn, verb, indicator
    ):
        del pool_cm, csv_info, extract_diffrn
        assert chunks == [['scan_001.xye']]
        assert template_arg == template
        assert verb is VerbosityEnum.SHORT
        assert indicator is not None
        indicator.update()

    monkeypatch.setattr(sequential_mod, 'ActivityIndicator', FakeIndicator)
    monkeypatch.setattr(sequential_mod.mp, 'parent_process', lambda: None)
    monkeypatch.setattr(sequential_mod, '_check_seq_preconditions', lambda project: None)
    monkeypatch.setattr(
        sequential_mod,
        'extract_data_paths_from_dir',
        lambda data_dir, file_pattern='*': ['scan_001.xye'],
    )
    monkeypatch.setattr(sequential_mod, '_build_template', lambda project: template)
    monkeypatch.setattr(
        sequential_mod,
        '_setup_csv_and_recovery',
        lambda project, template_arg, verb: (
            tmp_path / 'results.csv',
            ['file_path'],
            set(),
            template_arg,
        ),
    )
    monkeypatch.setattr(sequential_mod, '_resolve_workers', lambda max_workers, chunk_size: (1, 1))
    monkeypatch.setattr(
        sequential_mod,
        '_create_pool_context',
        lambda max_workers: (contextlib.nullcontext(None), None, None, None),
    )
    monkeypatch.setattr(sequential_mod, '_run_fit_loop', fake_run_fit_loop)
    monkeypatch.setattr(sequential_mod, '_restore_main_state', lambda *args: None)

    analysis = SimpleNamespace(
        project=SimpleNamespace(verbosity='short'),
        fitter=SimpleNamespace(selection='lmfit'),
    )

    sequential_mod.fit_sequential(analysis, data_dir=str(tmp_path))

    assert events == [
        ('init', ACTIVITY_LABEL_FITTING, VerbosityEnum.SHORT),
        ('start',),
        ('update',),
        ('stop',),
    ]


def test_fit_sequential_silent_does_not_start_indicator(monkeypatch, tmp_path):
    import easydiffraction.analysis.sequential as sequential_mod

    template = _minimal_template()

    class FailingIndicator:
        def __init__(self, *args, **kwargs):
            message = 'silent mode should not create an activity indicator'
            raise AssertionError(message)

    def fake_run_fit_loop(
        pool_cm, chunks, template_arg, csv_info, extract_diffrn, verb, indicator
    ):
        del pool_cm, csv_info, extract_diffrn
        assert chunks == [['scan_001.xye']]
        assert template_arg == template
        assert verb is VerbosityEnum.SILENT
        assert indicator is None

    monkeypatch.setattr(sequential_mod, 'ActivityIndicator', FailingIndicator)
    monkeypatch.setattr(sequential_mod.mp, 'parent_process', lambda: None)
    monkeypatch.setattr(sequential_mod, '_check_seq_preconditions', lambda project: None)
    monkeypatch.setattr(
        sequential_mod,
        'extract_data_paths_from_dir',
        lambda data_dir, file_pattern='*': ['scan_001.xye'],
    )
    monkeypatch.setattr(sequential_mod, '_build_template', lambda project: template)
    monkeypatch.setattr(
        sequential_mod,
        '_setup_csv_and_recovery',
        lambda project, template_arg, verb: (
            tmp_path / 'results.csv',
            ['file_path'],
            set(),
            template_arg,
        ),
    )
    monkeypatch.setattr(sequential_mod, '_resolve_workers', lambda max_workers, chunk_size: (1, 1))
    monkeypatch.setattr(
        sequential_mod,
        '_create_pool_context',
        lambda max_workers: (contextlib.nullcontext(None), None, None, None),
    )
    monkeypatch.setattr(sequential_mod, '_run_fit_loop', fake_run_fit_loop)
    monkeypatch.setattr(sequential_mod, '_restore_main_state', lambda *args: None)

    analysis = SimpleNamespace(
        project=SimpleNamespace(verbosity='silent'),
        fitter=SimpleNamespace(selection='lmfit'),
    )

    sequential_mod.fit_sequential(analysis, data_dir=str(tmp_path))
