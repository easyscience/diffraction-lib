"""Benchmark tutorial scripts and save timing results."""

from __future__ import annotations

import argparse
import csv
import os
import platform
import subprocess  # noqa: S404
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from pathlib import PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / 'src'
DEFAULT_TUTORIAL_DIR = ROOT / 'docs' / 'docs' / 'tutorials'
DEFAULT_OUTPUT_DIR = ROOT / 'docs' / 'dev' / 'benchmarking'
CHECKPOINT_DIR_NAME = '.ipynb_checkpoints'
CSV_HEADER = ['tutorial_name', 'elapsed_seconds', 'status', 'return_code']

# Layout for the live single-line table. The name column is sized
# from the longest tutorial name encountered.
STATUS_COLUMN_WIDTH = 10
TIME_COLUMN_WIDTH = 10  # includes trailing 's'
PROGRESS_POLL_SECONDS = 0.2


@dataclass(frozen=True)
class TutorialBenchmarkResult:
    """Store timing data for one tutorial run."""

    tutorial_name: str
    elapsed_seconds: float
    status: str
    return_code: int


def _relative_display_path(path: Path, start_path: Path) -> str:
    try:
        return path.relative_to(start_path).as_posix()
    except ValueError:
        return path.as_posix()


def _slugify(value: str) -> str:
    return value.lower().replace(' ', '-').replace('/', '-')


def _build_env() -> dict[str, str]:
    env = os.environ.copy()
    if SRC_ROOT.exists():
        existing_pythonpath = env.get('PYTHONPATH', '')
        env['PYTHONPATH'] = (
            str(SRC_ROOT)
            if not existing_pythonpath
            else str(SRC_ROOT) + os.pathsep + existing_pythonpath
        )
    return env


def _discover_tutorials(tutorial_dir: Path) -> list[Path]:
    return [
        path
        for path in sorted(tutorial_dir.rglob('*.py'))
        if CHECKPOINT_DIR_NAME not in path.parts
    ]


def _matches_requested_patterns(
    script_path: Path,
    tutorial_dir: Path,
    patterns: list[str],
) -> bool:
    if not patterns:
        return True

    rel_path = PurePosixPath(_relative_display_path(script_path, tutorial_dir))
    return any(rel_path.match(pattern) or script_path.name == pattern for pattern in patterns)


def _format_progress_line(
    *,
    index: int,
    total: int,
    name: str,
    name_width: int,
    status: str,
    elapsed_seconds: float,
) -> str:
    """Format one tutorial row for the live progress table."""
    index_width = len(str(total))
    counter = f'[{index:>{index_width}}/{total}]'
    time_field_width = TIME_COLUMN_WIDTH - 1  # reserve one column for trailing 's'
    return (
        f'{counter}  '
        f'{name:<{name_width}}  '
        f'{status:<{STATUS_COLUMN_WIDTH}}  '
        f'{elapsed_seconds:>{time_field_width}.1f}s'
    )


def _emit_progress_line(*, line: str, final: bool, is_tty: bool) -> None:
    """
    Render one progress line.

    On a TTY the same line is rewritten in place via carriage return so
    the elapsed-seconds field updates while the tutorial is running;
    only the final write terminates with a newline. When stdout is not
    a TTY (CI, log file), only the final row is printed so the log
    stays one-line-per-tutorial without carriage-return noise.
    """
    if is_tty:
        terminator = '\n' if final else ''
        sys.stdout.write('\r' + line + terminator)
        sys.stdout.flush()
    elif final:
        print(line)


def _run_tutorial(
    script_path: Path,
    tutorial_dir: Path,
    env: dict[str, str],
    *,
    index: int,
    total: int,
    name_width: int,
    is_tty: bool,
) -> TutorialBenchmarkResult:
    """Run one tutorial with a live single-line progress indicator."""
    tutorial_name = _relative_display_path(script_path, tutorial_dir)
    start_time = time.perf_counter()

    # Combined stdout+stderr land in a temp file so the OS pipe buffer
    # cannot fill up and stall the subprocess while we poll. We only
    # read the contents back if the tutorial fails.
    with tempfile.TemporaryFile(mode='wb+') as out_file:
        proc = subprocess.Popen(  # noqa: S603
            [sys.executable, str(script_path)],
            cwd=str(ROOT),
            env=env,
            stdout=out_file,
            stderr=subprocess.STDOUT,
        )

        last_displayed_second = -1
        while proc.poll() is None:
            elapsed = time.perf_counter() - start_time
            current_second = int(elapsed)
            if current_second != last_displayed_second:
                _emit_progress_line(
                    line=_format_progress_line(
                        index=index,
                        total=total,
                        name=tutorial_name,
                        name_width=name_width,
                        status='Running...',
                        elapsed_seconds=elapsed,
                    ),
                    final=False,
                    is_tty=is_tty,
                )
                last_displayed_second = current_second
            time.sleep(PROGRESS_POLL_SECONDS)

        elapsed_seconds = time.perf_counter() - start_time
        success = proc.returncode == 0
        status_word = 'OK' if success else 'FAILED'
        _emit_progress_line(
            line=_format_progress_line(
                index=index,
                total=total,
                name=tutorial_name,
                name_width=name_width,
                status=status_word,
                elapsed_seconds=elapsed_seconds,
            ),
            final=True,
            is_tty=is_tty,
        )

        if not success:
            out_file.seek(0)
            details = out_file.read().decode('utf-8', errors='replace').strip()
            if details:
                print(details, file=sys.stderr)

    return TutorialBenchmarkResult(
        tutorial_name=tutorial_name,
        elapsed_seconds=elapsed_seconds,
        status='ok' if success else 'failed',
        return_code=proc.returncode,
    )


def _build_output_path(output_dir: Path) -> Path:
    timestamp = datetime.now().astimezone().strftime('%Y%m%d-%H%M%S')
    system_name = _slugify(platform.system())
    machine_name = _slugify(platform.machine())
    python_name = f'py{sys.version_info.major}{sys.version_info.minor}'
    file_name = (
        f'{timestamp}_{system_name}-{machine_name}_'
        f'{python_name}_tutorial-benchmarks.csv'
    )
    return output_dir / file_name


def _write_csv_header(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(CSV_HEADER)


def _append_result(output_path: Path, result: TutorialBenchmarkResult) -> None:
    with output_path.open('a', encoding='utf-8', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                result.tutorial_name,
                f'{result.elapsed_seconds:.3f}',
                result.status,
                result.return_code,
            ]
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Run tutorial scripts sequentially and record timings.',
    )
    parser.add_argument(
        '--tutorial-dir',
        type=Path,
        default=DEFAULT_TUTORIAL_DIR,
        help='Directory containing tutorial scripts to benchmark.',
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help='Directory where the benchmark CSV should be written.',
    )
    parser.add_argument(
        '--pattern',
        action='append',
        default=[],
        help=(
            'Glob for tutorial paths relative to the tutorial directory. '
            'Pass multiple times to benchmark a subset.'
        ),
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    tutorial_dir = args.tutorial_dir.resolve()
    output_dir = args.output_dir.resolve()

    if not tutorial_dir.is_dir():
        print(f'Tutorial directory not found: {tutorial_dir}', file=sys.stderr)
        return 1

    tutorials = [
        path
        for path in _discover_tutorials(tutorial_dir)
        if _matches_requested_patterns(path, tutorial_dir, args.pattern)
    ]
    if not tutorials:
        print('No tutorial scripts matched the requested pattern(s).', file=sys.stderr)
        return 1

    output_path = _build_output_path(output_dir)
    _write_csv_header(output_path)

    env = _build_env()
    is_tty = sys.stdout.isatty()
    name_width = max(
        len(_relative_display_path(path, tutorial_dir)) for path in tutorials
    )

    results: list[TutorialBenchmarkResult] = []
    for index, tutorial_path in enumerate(tutorials, start=1):
        result = _run_tutorial(
            tutorial_path,
            tutorial_dir,
            env,
            index=index,
            total=len(tutorials),
            name_width=name_width,
            is_tty=is_tty,
        )
        results.append(result)
        _append_result(output_path, result)

    total_elapsed = sum(result.elapsed_seconds for result in results)
    failure_count = sum(result.status == 'failed' for result in results)

    print(f'Wrote benchmark results to {_relative_display_path(output_path, ROOT)}')
    print(f'Total elapsed time: {total_elapsed:.1f}s')

    if failure_count:
        print(f'Failed tutorials: {failure_count}', file=sys.stderr)
        return 1

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
