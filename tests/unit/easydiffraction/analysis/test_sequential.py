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
from easydiffraction.analysis.sequential import _chunk_file_range
from easydiffraction.analysis.sequential import _read_csv_for_recovery
from easydiffraction.analysis.sequential import _relative_file_path_for_csv
from easydiffraction.analysis.sequential import _write_csv_header
from easydiffraction.display.progress import ACTIVITY_LABEL_FITTING
from easydiffraction.utils.enums import VerbosityEnum

_TEST_SCAN_001 = 'data/scan_001.xye'
_TEST_SCAN_002 = 'data/scan_002.xye'


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
        diffrn_extract_rules=[],
        diffrn_field_names=diffrn_fields,
    )


class _RecordingConsole:
    def __init__(self, events):
        self._events = events

    def paragraph(self, text):
        self._events.append(('paragraph', text))

    def print(self, *args, **kwargs):
        self._events.append(('console_print', args, kwargs))


def _make_indicator(events):
    class RecordingIndicator:
        def __init__(self, label, *, verbosity, animated=True):
            events.append(('init', label, verbosity, animated))

        def start(self):
            events.append(('start',))

        def update(self, *, label=None, content=None):
            events.append(('update', label, content))

        def stop(self):
            events.append(('stop',))

    return RecordingIndicator


def _make_run_fit_loop(events, template, verbosity):
    def fake_run_fit_loop(pool_cm, chunks, template_arg, csv_info, progress):
        del pool_cm, csv_info
        assert chunks == [['scan_001.xye']]
        assert template_arg == template
        assert progress.verbosity is VerbosityEnum(verbosity)
        assert progress.state is not None
        assert progress.state.chunk_rows == []
        assert progress.state.file_rows == []
        events.append((
            'run_loop',
            progress.indicator is not None,
        ))

    return fake_run_fit_loop


def _run_non_silent_fit(monkeypatch, tmp_path, *, verbosity, is_jupyter):
    import easydiffraction.analysis.sequential as sequential_mod

    events: list[tuple[object, ...]] = []
    template = _minimal_template()

    monkeypatch.setattr(sequential_mod.mp, 'parent_process', lambda: None)
    monkeypatch.setattr(sequential_mod, '_check_seq_preconditions', lambda project: None)
    monkeypatch.setattr(sequential_mod, 'console', _RecordingConsole(events))
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
        '_run_fit_loop_with_pool',
        lambda max_workers, chunks, template_arg, csv_info, progress: _make_run_fit_loop(
            events,
            template,
            verbosity,
        )(None, chunks, template_arg, csv_info, progress),
    )
    monkeypatch.setattr(sequential_mod, 'ActivityIndicator', _make_indicator(events))
    del is_jupyter  # legacy parameter, no longer affects behavior

    analysis = SimpleNamespace(
        project=SimpleNamespace(verbosity=SimpleNamespace(fit=SimpleNamespace(value=verbosity))),
        fitter=SimpleNamespace(selection='lmfit'),
    )

    sequential_mod.fit_sequential(analysis, data_dir=str(tmp_path))
    return events


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

    def test_append_stores_file_paths_relative_to_project(self, tmp_path):
        project_dir = tmp_path / 'project'
        csv_path = project_dir / 'analysis' / 'results.csv'
        csv_path.parent.mkdir(parents=True)
        data_dir = project_dir / 'experiments' / 'scan'
        data_dir.mkdir(parents=True)
        data_path = data_dir / 'scan_001.dat'
        data_path.write_text('1 2 3\n')
        header = ['file_path', 'value']
        _write_csv_header(csv_path, header)

        _append_to_csv(
            csv_path,
            header,
            [
                {'file_path': str(data_path), 'value': 1.0},
            ],
        )

        with csv_path.open() as f:
            rows = list(csv.DictReader(f))
        assert rows[0]['file_path'] == 'experiments/scan/scan_001.dat'

    def test_append_normalizes_repo_relative_project_paths(self, tmp_path, monkeypatch):
        workspace_dir = tmp_path / 'workspace'
        project_dir = workspace_dir / 'projects' / 'cosio'
        csv_path = project_dir / 'analysis' / 'results.csv'
        csv_path.parent.mkdir(parents=True)
        monkeypatch.chdir(workspace_dir)
        header = ['file_path', 'value']
        _write_csv_header(csv_path, header)

        _append_to_csv(
            csv_path,
            header,
            [
                {
                    'file_path': 'projects/cosio/experiments/d20_scan/scan_001.dat',
                    'value': 1.0,
                },
            ],
        )

        with csv_path.open() as f:
            rows = list(csv.DictReader(f))
        assert rows[0]['file_path'] == 'experiments/d20_scan/scan_001.dat'

    def test_relative_file_paths_use_posix_separators(self, tmp_path, monkeypatch):
        import easydiffraction.analysis.sequential as sequential_mod

        project_dir = tmp_path / 'project'
        csv_path = project_dir / 'analysis' / 'results.csv'
        csv_path.parent.mkdir(parents=True)
        data_dir = project_dir / 'experiments' / 'scan'
        data_dir.mkdir(parents=True)
        data_path = data_dir / 'scan_001.dat'
        data_path.write_text('1 2 3\n')
        monkeypatch.setattr(
            sequential_mod.os.path,
            'relpath',
            lambda _path, start: 'experiments\\scan\\scan_001.dat',
        )

        relative_path = _relative_file_path_for_csv(csv_path, str(data_path))

        assert relative_path == 'experiments/scan/scan_001.dat'

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
        project_dir = tmp_path / 'project'
        csv_path = project_dir / 'analysis' / 'results.csv'
        csv_path.parent.mkdir(parents=True)
        header = [*_META_COLUMNS, 'cell.a', 'cell.a.uncertainty']
        _write_csv_header(csv_path, header)
        _append_to_csv(
            csv_path,
            header,
            [
                {
                    'file_path': str(project_dir / 'experiments' / 'a.dat'),
                    'fit_success': 'True',
                    'chi_squared': '5.0',
                    'reduced_chi_squared': '2.5',
                    'n_iterations': '10',
                    'cell.a': '3.89',
                    'cell.a.uncertainty': '0.01',
                },
                {
                    'file_path': str(project_dir / 'experiments' / 'b.dat'),
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
        assert fitted == {
            str((project_dir / 'experiments' / 'a.dat').resolve()),
            str((project_dir / 'experiments' / 'b.dat').resolve()),
        }

    def test_resolves_legacy_repo_relative_paths(self, tmp_path, monkeypatch):
        workspace_dir = tmp_path / 'workspace'
        project_dir = workspace_dir / 'projects' / 'cosio'
        csv_path = project_dir / 'analysis' / 'results.csv'
        csv_path.parent.mkdir(parents=True)
        monkeypatch.chdir(workspace_dir)
        header = [*_META_COLUMNS, 'cell.a', 'cell.a.uncertainty']

        with csv_path.open('w', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(handle, fieldnames=header)
            writer.writeheader()
            writer.writerow({
                'file_path': 'projects/cosio/experiments/d20_scan/scan_001.dat',
                'fit_success': 'True',
                'chi_squared': '5.0',
                'reduced_chi_squared': '2.5',
                'n_iterations': '10',
                'cell.a': '3.89',
                'cell.a.uncertainty': '0.01',
            })

        fitted, _params = _read_csv_for_recovery(csv_path)
        assert fitted == {
            str((project_dir / 'experiments' / 'd20_scan' / 'scan_001.dat').resolve())
        }

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


class TestChunkFileRange:
    def test_formats_inclusive_range_with_spaced_dash(self):
        assert _chunk_file_range([_TEST_SCAN_001, _TEST_SCAN_002]) == (
            'scan_001.xye - scan_002.xye'
        )

    def test_returns_single_name_for_single_file_chunk(self):
        assert _chunk_file_range([_TEST_SCAN_001]) == 'scan_001.xye'


@pytest.mark.parametrize('verbosity', [VerbosityEnum.SHORT, VerbosityEnum.FULL])
def test_report_chunk_progress_updates_indicator_with_renderable(monkeypatch, verbosity):
    import easydiffraction.analysis.sequential as sequential_mod

    update_calls: list[object] = []

    class RecordingIndicator:
        def update(self, *, label=None, content=None):
            del label
            update_calls.append(content)

    progress_state = sequential_mod.SequentialProgressState(chunk_rows=[], file_rows=[])
    progress = sequential_mod.SequentialProgressContext(
        verbosity=verbosity,
        state=progress_state,
        indicator=RecordingIndicator(),
    )

    sequential_mod._report_chunk_progress(
        1,
        3,
        [_TEST_SCAN_001, _TEST_SCAN_002],
        [
            {
                'file_path': _TEST_SCAN_001,
                'fit_success': True,
                'reduced_chi_squared': 4.0,
                'n_iterations': 11,
            },
            {
                'file_path': _TEST_SCAN_002,
                'fit_success': False,
                'reduced_chi_squared': None,
                'n_iterations': 0,
            },
        ],
        progress,
        sequential_mod._ChunkProgressMetrics(
            completed_files_before=0,
            total_files=3,
            elapsed_time=19.76,
        ),
    )

    if verbosity is VerbosityEnum.SHORT:
        expected_rows = [
            ['1/3', '66.7%', '19.76', 'scan_001.xye - scan_002.xye', '2', '4.00', '⚠️']
        ]
        assert progress_state.chunk_rows == expected_rows
        assert progress_state.file_rows == []
    else:
        expected_rows = [
            ['scan_001.xye', '33.3%', '19.76', '4.00', '11', '✅'],
            ['scan_002.xye', '66.7%', '19.76', '—', '0', '❌'],
        ]
        assert progress_state.chunk_rows == []
        assert progress_state.file_rows == expected_rows

    assert len(update_calls) == 1
    assert update_calls[0] is not None


@pytest.mark.parametrize(
    'verbosity',
    ['short', 'full'],
)
def test_fit_sequential_non_silent_starts_indicator_with_progress_table(
    monkeypatch,
    tmp_path,
    verbosity,
):
    events = _run_non_silent_fit(
        monkeypatch,
        tmp_path,
        verbosity=verbosity,
        is_jupyter=False,
    )

    verb_enum = VerbosityEnum(verbosity)

    assert events[:4] == [
        ('paragraph', 'Sequential fitting'),
        ('console_print', ("🚀 Starting fit process with 'lmfit'...",), {}),
        ('console_print', ('📋 1 files in 1 chunks (max_workers=1)',), {}),
        ('console_print', ('📈 Goodness-of-fit progress:',), {}),
    ]
    assert events[4] == ('init', ACTIVITY_LABEL_FITTING, verb_enum, True)
    assert events[5] == ('start',)
    # Initial empty table renderable is pushed before the fit loop runs.
    assert events[6][0] == 'update'
    assert events[6][1] is None
    assert events[6][2] is not None
    assert events[7] == ('run_loop', True)
    assert events[8] == ('stop',)
    assert events[9:] == [
        ('console_print', ('✅ Sequential fitting complete: 1 files processed.',), {}),
        ('console_print', (f'📄 Results saved to: {tmp_path / "results.csv"}',), {}),
    ]


def test_run_fit_loop_runs_chunks_sequentially_with_executor_map(monkeypatch, tmp_path):
    import easydiffraction.analysis.sequential as sequential_mod

    template = _minimal_template()
    header = ['file_path']
    events: list[tuple[object, ...]] = []
    progress = sequential_mod.SequentialProgressContext(
        verbosity=VerbosityEnum.SHORT,
        state=sequential_mod.SequentialProgressState(chunk_rows=[], file_rows=[]),
    )

    class FakeExecutor:
        def map(self, func, templates, paths):
            assert func is sequential_mod._fit_worker
            for template_arg in templates:
                assert template_arg == template
            for path in paths:
                yield {
                    'file_path': path,
                    'fit_success': True,
                    'reduced_chi_squared': 1.0,
                    'n_iterations': 5,
                    'params': {'cell.a': 4.0},
                }

    class FakePool:
        def __enter__(self):
            return FakeExecutor()

        def __exit__(self, exc_type, exc, tb):
            del exc_type, exc, tb
            return False

    monkeypatch.setattr(
        sequential_mod,
        '_append_to_csv',
        lambda csv_path, header_arg, results: events.append((
            'append',
            csv_path,
            header_arg,
            [result['file_path'] for result in results],
        )),
    )
    monkeypatch.setattr(
        sequential_mod,
        '_report_chunk_progress',
        lambda *args: events.append(('report', [result['file_path'] for result in args[3]])),
    )

    sequential_mod._run_fit_loop(
        FakePool(),
        [[_TEST_SCAN_001, _TEST_SCAN_002]],
        template,
        (tmp_path / 'results.csv', header),
        progress,
    )

    assert events == [
        ('append', tmp_path / 'results.csv', header, [_TEST_SCAN_001, _TEST_SCAN_002]),
        ('report', [_TEST_SCAN_001, _TEST_SCAN_002]),
    ]


def test_fit_sequential_silent_does_not_start_indicator(monkeypatch, tmp_path):
    import easydiffraction.analysis.sequential as sequential_mod

    template = _minimal_template()

    class FailingIndicator:
        def __init__(self, *args, **kwargs):
            message = 'silent mode should not create an activity indicator'
            raise AssertionError(message)

    def fake_run_fit_loop(
        pool_cm,
        chunks,
        template_arg,
        csv_info,
        progress,
    ):
        del pool_cm, csv_info
        assert chunks == [['scan_001.xye']]
        assert template_arg == template
        assert progress.verbosity is VerbosityEnum.SILENT
        assert progress.state is None
        assert progress.indicator is None

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
        project=SimpleNamespace(verbosity=SimpleNamespace(fit=SimpleNamespace(value='silent'))),
        fitter=SimpleNamespace(selection='lmfit'),
    )

    sequential_mod.fit_sequential(analysis, data_dir=str(tmp_path))
