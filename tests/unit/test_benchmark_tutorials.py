# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for tutorial benchmark CSV persistence."""

from __future__ import annotations

import csv
import importlib.util
import sys
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace


def _load_module():
    module_path = Path(__file__).resolve().parents[2] / 'tools' / 'benchmark_tutorials.py'
    spec = importlib.util.spec_from_file_location('benchmark_tutorials', module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


MUT = _load_module()


def test_append_result_writes_one_row(tmp_path):
    output_path = tmp_path / 'benchmark.csv'

    MUT._write_csv_header(output_path)
    MUT._append_result(
        output_path,
        MUT.TutorialBenchmarkResult(
            tutorial_name='ed-21.py',
            elapsed_seconds=12.3456,
            status='ok',
            return_code=0,
        ),
    )

    with output_path.open(encoding='utf-8', newline='') as handle:
        rows = list(csv.DictReader(handle))

    assert rows == [
        {
            'tutorial_name': 'ed-21.py',
            'elapsed_seconds': '12.346',
            'status': 'ok',
            'return_code': '0',
        }
    ]


def test_main_appends_first_result_before_second_tutorial_starts(monkeypatch, tmp_path):
    tutorial_dir = tmp_path / 'tutorials'
    tutorial_dir.mkdir()
    first_tutorial = tutorial_dir / 'ed-01.py'
    second_tutorial = tutorial_dir / 'ed-02.py'
    first_tutorial.write_text('print("first")\n', encoding='utf-8')
    second_tutorial.write_text('print("second")\n', encoding='utf-8')

    output_path = tmp_path / 'benchmarking' / 'results.csv'
    args = Namespace(
        tutorial_dir=tutorial_dir,
        output_dir=tmp_path / 'benchmarking',
        pattern=[],
    )

    monkeypatch.setattr(
        MUT,
        'build_parser',
        lambda: SimpleNamespace(parse_args=lambda: args),
    )
    monkeypatch.setattr(MUT, '_build_output_path', lambda output_dir: output_path)
    monkeypatch.setattr(MUT, '_build_env', dict)

    def fake_run_tutorial(
        script_path: Path,
        tutorial_dir_path: Path,
        env: dict[str, str],
    ) -> MUT.TutorialBenchmarkResult:
        del tutorial_dir_path, env
        if script_path == first_tutorial:
            with output_path.open(encoding='utf-8', newline='') as handle:
                rows = list(csv.reader(handle))
            assert rows == [MUT.CSV_HEADER]
            return MUT.TutorialBenchmarkResult(
                tutorial_name='ed-01.py',
                elapsed_seconds=1.0,
                status='ok',
                return_code=0,
            )

        with output_path.open(encoding='utf-8', newline='') as handle:
            rows = list(csv.DictReader(handle))
        assert rows == [
            {
                'tutorial_name': 'ed-01.py',
                'elapsed_seconds': '1.000',
                'status': 'ok',
                'return_code': '0',
            }
        ]
        return MUT.TutorialBenchmarkResult(
            tutorial_name='ed-02.py',
            elapsed_seconds=2.0,
            status='ok',
            return_code=0,
        )

    monkeypatch.setattr(MUT, '_run_tutorial', fake_run_tutorial)

    exit_code = MUT.main()

    assert exit_code == 0
    with output_path.open(encoding='utf-8', newline='') as handle:
        rows = list(csv.DictReader(handle))
    assert rows == [
        {
            'tutorial_name': 'ed-01.py',
            'elapsed_seconds': '1.000',
            'status': 'ok',
            'return_code': '0',
        },
        {
            'tutorial_name': 'ed-02.py',
            'elapsed_seconds': '2.000',
            'status': 'ok',
            'return_code': '0',
        },
    ]
