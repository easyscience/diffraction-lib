# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for sequential fitting helper functions."""

from __future__ import annotations

import contextlib
import csv
from io import StringIO
from types import SimpleNamespace

import pytest
from rich.console import Console
from rich.table import Table

from easydiffraction.analysis.sequential import SequentialFitTemplate
from easydiffraction.analysis.sequential import _META_COLUMNS
from easydiffraction.analysis.sequential import _append_to_csv
from easydiffraction.analysis.sequential import _build_csv_header
from easydiffraction.analysis.sequential import _read_csv_for_recovery
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


def _progress_renderable_snapshot(verbosity_arg, state):
    return (
        'renderable',
        verbosity_arg,
        [row[:] for row in state.chunk_rows],
        [row[:] for row in state.file_rows],
    )


class _RecordingConsole:
    def __init__(self, events):
        self._events = events

    def paragraph(self, text):
        self._events.append(('paragraph', text))

    def print(self, *args, **kwargs):
        self._events.append(('console_print', args, kwargs))


class _RecordingDisplayHandle:
    def __init__(self, events):
        self._events = events

    def start(self):
        self._events.append(('display_start',))

    def update(self, renderable):
        self._events.append(('display_update', renderable))

    def close(self):
        self._events.append(('display_close',))


def _make_terminal_display(events):
    class RecordingTerminalDisplay:
        def __init__(self, *, console, label, renderable):
            del console
            events.append(('display_init', label, renderable))
            self._handle = _RecordingDisplayHandle(events)

        def start(self):
            self._handle.start()

        def update(self, renderable):
            self._handle.update(renderable)

        def close(self):
            self._handle.close()

    return RecordingTerminalDisplay


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
            progress.display_handle is not None,
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
    monkeypatch.setattr(sequential_mod, 'in_jupyter', lambda: is_jupyter)
    monkeypatch.setattr(
        sequential_mod.ConsoleManager,
        'get',
        lambda: SimpleNamespace(
            is_terminal=True,
            is_dumb_terminal=False,
        ),
    )
    monkeypatch.setattr(
        sequential_mod, '_TerminalSequentialDisplay', _make_terminal_display(events)
    )
    monkeypatch.setattr(
        sequential_mod, '_build_progress_renderable', _progress_renderable_snapshot
    )

    analysis = SimpleNamespace(
        project=SimpleNamespace(verbosity=verbosity),
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


@pytest.mark.parametrize('verbosity', [VerbosityEnum.SHORT, VerbosityEnum.FULL])
def test_report_chunk_progress_updates_indicator(monkeypatch, verbosity):
    import easydiffraction.analysis.sequential as sequential_mod

    updates: list[object] = []

    class FakeIndicator:
        def update(self, *, label=None, content=None):
            del label
            updates.append(content)

    progress_state = sequential_mod.SequentialProgressState(chunk_rows=[], file_rows=[])

    monkeypatch.setattr(
        sequential_mod, '_build_progress_renderable', _progress_renderable_snapshot
    )

    progress = sequential_mod.SequentialProgressContext(
        verbosity=verbosity,
        state=progress_state,
        indicator=FakeIndicator(),
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
        0,
        3,
        19.76,
    )

    if verbosity is VerbosityEnum.SHORT:
        expected_chunk_rows = [['1/3', '66.7%', '19.76', 'scan_001.xye-scan_002.xye', '2', '4.00', '⚠️']]
        expected_file_rows = []
    else:
        expected_chunk_rows = []
        expected_file_rows = [
            ['scan_001.xye', '33.3%', '19.76', '4.00', '11', '✅'],
            ['scan_002.xye', '66.7%', '19.76', '—', '0', '❌'],
        ]

    assert progress_state.chunk_rows == expected_chunk_rows
    assert progress_state.file_rows == expected_file_rows
    assert updates == [('renderable', verbosity, expected_chunk_rows, expected_file_rows)]


def test_report_chunk_progress_uses_display_handle_when_provided(monkeypatch):
    import easydiffraction.analysis.sequential as sequential_mod

    updates: list[object] = []
    progress_state = sequential_mod.SequentialProgressState(chunk_rows=[], file_rows=[])

    class FakeDisplayHandle:
        def update(self, renderable):
            updates.append(renderable)

    monkeypatch.setattr(
        sequential_mod, '_build_progress_renderable', _progress_renderable_snapshot
    )

    progress = sequential_mod.SequentialProgressContext(
        verbosity=VerbosityEnum.FULL,
        state=progress_state,
        display_handle=FakeDisplayHandle(),
    )

    sequential_mod._report_chunk_progress(
        1,
        2,
        [_TEST_SCAN_001],
        [
            {
                'file_path': _TEST_SCAN_001,
                'fit_success': True,
                'reduced_chi_squared': 3.5,
                'n_iterations': 12,
            }
        ],
        progress,
        1,
        2,
        3.50,
    )

    assert updates == [
        ('renderable', VerbosityEnum.FULL, [], [['scan_001.xye', '100.0%', '3.50', '3.50', '12', '✅']])
    ]


@pytest.mark.parametrize(
    ('verbosity', 'is_jupyter', 'expects_display_handle', 'expects_indicator'),
    [
        ('short', False, True, False),
        ('full', False, True, False),
        ('full', True, False, True),
    ],
)
def test_fit_sequential_non_silent_starts_indicator_with_progress_table(
    monkeypatch,
    tmp_path,
    verbosity,
    is_jupyter,
    expects_display_handle,
    expects_indicator,
):
    events = _run_non_silent_fit(
        monkeypatch,
        tmp_path,
        verbosity=verbosity,
        is_jupyter=is_jupyter,
    )

    if expects_display_handle:
        assert events == [
            ('paragraph', 'Sequential fitting'),
            ('console_print', ("🚀 Starting fit process with 'lmfit'...",), {}),
            ('console_print', ('📋 1 files in 1 chunks (max_workers=1)',), {}),
            ('console_print', ('📈 Goodness-of-fit progress:',), {}),
            (
                'display_init',
                ACTIVITY_LABEL_FITTING,
                ('renderable', VerbosityEnum(verbosity), [], []),
            ),
            ('display_start',),
            ('run_loop', False, True),
            ('display_close',),
            ('console_print', ('✅ Sequential fitting complete: 1 files processed.',), {}),
            ('console_print', (f'📄 Results saved to: {tmp_path / "results.csv"}',), {}),
        ]
    else:
        assert events == [
            ('paragraph', 'Sequential fitting'),
            ('console_print', ("🚀 Starting fit process with 'lmfit'...",), {}),
            ('console_print', ('📋 1 files in 1 chunks (max_workers=1)',), {}),
            ('console_print', ('📈 Goodness-of-fit progress:',), {}),
            ('init', ACTIVITY_LABEL_FITTING, VerbosityEnum(verbosity), True),
            ('start',),
            ('update', None, ('renderable', VerbosityEnum(verbosity), [], [])),
            ('run_loop', True, False),
            ('stop',),
            ('console_print', ('✅ Sequential fitting complete: 1 files processed.',), {}),
            ('console_print', (f'📄 Results saved to: {tmp_path / "results.csv"}',), {}),
        ]


def test_run_fit_loop_advances_terminal_display_while_waiting(monkeypatch, tmp_path):
    import easydiffraction.analysis.sequential as sequential_mod

    template = _minimal_template()
    header = ['file_path']
    events: list[tuple[object, ...]] = []
    progress = sequential_mod.SequentialProgressContext(
        verbosity=VerbosityEnum.SHORT,
        state=sequential_mod.SequentialProgressState(chunk_rows=[], file_rows=[]),
        display_handle=SimpleNamespace(advance=lambda: events.append(('advance',))),
    )

    class FakeFuture:
        def __init__(self, path):
            self.path = path

        def result(self):
            return {
                'file_path': self.path,
                'fit_success': True,
                'reduced_chi_squared': 1.0 if self.path.endswith('001.xye') else 2.0,
                'n_iterations': 5,
                'params': {'cell.a': 4.0},
            }

    class FakeExecutor:
        def submit(self, func, template_arg, path):
            assert func is sequential_mod._fit_worker
            assert template_arg == template
            return FakeFuture(path)

    class FakePool:
        def __enter__(self):
            return FakeExecutor()

        def __exit__(self, exc_type, exc, tb):
            del exc_type, exc, tb
            return False

    def fake_wait(pending, timeout, return_when):
        assert timeout == sequential_mod._SEQUENTIAL_SPINNER_FRAME_SECONDS
        assert return_when == sequential_mod.FIRST_COMPLETED
        pending_by_path = {future.path: future for future in pending}
        if _TEST_SCAN_001 in pending_by_path and _TEST_SCAN_002 in pending_by_path:
            if not any(event[0] == 'advance' for event in events):
                return set(), set(pending)
            return {pending_by_path[_TEST_SCAN_001]}, {pending_by_path[_TEST_SCAN_002]}
        return set(pending), set()

    monkeypatch.setattr(sequential_mod, 'wait', fake_wait)
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
        ('advance',),
        ('append', tmp_path / 'results.csv', header, [_TEST_SCAN_001, _TEST_SCAN_002]),
        ('report', [_TEST_SCAN_001, _TEST_SCAN_002]),
    ]


def test_terminal_sequential_display_preserves_ansi_styles():
    import easydiffraction.analysis.sequential as sequential_mod

    terminal_console = Console(
        file=StringIO(),
        width=40,
        force_jupyter=False,
        force_terminal=True,
        color_system='standard',
    )
    table = Table(border_style='red')
    table.add_column('chunk')
    table.add_row('1/2')

    display = sequential_mod._TerminalSequentialDisplay(
        console=terminal_console,
        label='Fitting...',
        renderable=table,
    )

    spinner_line = display._spinner_line()
    table_lines = display._render_lines(table)

    assert '\x1b[' in spinner_line
    assert any('\x1b[' in line for line in table_lines)


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
        assert progress.display_handle is None

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
