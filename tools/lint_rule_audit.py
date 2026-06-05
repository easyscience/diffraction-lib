# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Regenerate the disabled-rule inventory for the lint-rule audit.

This helper reproduces the table in
``docs/dev/plans/lint-rule-audit.md`` without modifying any tracked
file. It layers the currently-disabled Ruff rules onto the *unmodified*
``pyproject.toml`` at the command line, runs ``ruff check``, and prints
a per-rule breakdown by source scope (``src``/``tests``/``tutorials``)
and auto-fixability::

    pixi run python tools/lint_rule_audit.py

The aggregation logic (:func:`scope`, :func:`family`, :func:`aggregate`)
is kept pure and importable so it can be unit-tested without invoking
Ruff; :func:`collect_records` and :func:`main` are the thin shim that
shells out to Ruff and prints.
"""

from __future__ import annotations

import json
import shutil
import subprocess  # noqa: S404
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Trees that the ``py-lint-check`` pixi task covers.
LINT_PATHS = ('src/', 'tests/', 'docs/docs/tutorials/')

# Disabled rules enabled for the audit. The commented-out ``select``
# families (``A``, ``FIX``, ``SLF``, ``T20``, ``TD``) plus the three
# *Temporary* global-ignore codes. ``--extend-select`` overrides the
# global ``ignore`` list for an exact code, so the global-ignore codes
# are listed here rather than removed from ``ignore``.
EXTEND_SELECT = ('A', 'FIX', 'SLF', 'T20', 'TD', 'D100', 'D104', 'DTZ005')

# Per-file-ignore table reduced to the documented (structural) entries
# only, dropping the *Temporary* tests/docs entries so their impact is
# measured. Passed verbatim to ``ruff check --config``.
PER_FILE_IGNORES = (
    "lint.per-file-ignores = {"
    "'*/__init__.py' = ['F401'], "
    "'tests/**' = ['ANN','D','DOC','INP001','RUF012','RUF069','S101'], "
    "'docs/**' = ['INP001','RUF001','RUF002','RUF003','T201'], "
    "'docs/docs/tutorials/**' = ['E402']}"
)

# Scopes reported in the table, in display order.
SCOPES = ('src', 'tests', 'tutorials')


def scope(filename: str, root: Path = REPO_ROOT) -> str:
    """Return the audit scope that a file belongs to.

    Parameters
    ----------
    filename
        Path reported by Ruff (absolute or repo-relative).
    root
        Repository root used to relativise absolute paths.

    Returns
    -------
    str
        ``'src'``, ``'tests'``, ``'tutorials'``, or ``'other'``.
    """
    path = Path(filename)
    if path.is_absolute():
        try:
            path = path.relative_to(root)
        except ValueError:
            return 'other'
    parts = path.parts
    if not parts:
        return 'other'
    if parts[0] == 'docs':
        return 'tutorials'
    if parts[0] == 'tests':
        return 'tests'
    if parts[0] == 'src':
        return 'src'
    return 'other'


def family(code: str) -> str:
    """Return the rule family (leading alphabetic prefix) of a code.

    Parameters
    ----------
    code
        A Ruff rule code such as ``'PLC0415'``.

    Returns
    -------
    str
        The leading-alphabetic prefix, e.g. ``'PLC'`` for ``'PLC0415'``.
    """
    end = 0
    while end < len(code) and code[end].isalpha():
        end += 1
    return code[:end]


def aggregate(records: list[dict], root: Path = REPO_ROOT) -> dict[str, dict]:
    """Aggregate Ruff JSON records into per-rule totals.

    Parameters
    ----------
    records
        Parsed ``ruff check --output-format=json`` records.
    root
        Repository root used to assign each record a scope.

    Returns
    -------
    dict
        Mapping of rule code to a summary with ``total``, per-scope
        counts (``src``/``tests``/``tutorials``/``other``), ``fix_safe``
        (applied by ``ruff --fix``), ``fix_unsafe`` (needs
        ``--unsafe-fixes``), ``family``, and a representative
        ``message``.
    """
    summary: dict[str, dict] = {}
    for record in records:
        code = record['code']
        entry = summary.get(code)
        if entry is None:
            entry = {
                'total': 0,
                'src': 0,
                'tests': 0,
                'tutorials': 0,
                'other': 0,
                'fix_safe': 0,
                'fix_unsafe': 0,
                'family': family(code),
                'message': record['message'],
            }
            summary[code] = entry
        entry['total'] += 1
        entry[scope(record['filename'], root)] += 1
        applicability = (record.get('fix') or {}).get('applicability')
        if applicability == 'safe':
            entry['fix_safe'] += 1
        elif applicability == 'unsafe':
            entry['fix_unsafe'] += 1
    return summary


def ruff_command(ruff_path: str) -> list[str]:
    """Return the non-destructive audit ``ruff check`` command.

    Parameters
    ----------
    ruff_path
        Absolute path to the ``ruff`` executable.

    Returns
    -------
    list of str
        Argument vector for :func:`subprocess.run`.
    """
    return [
        ruff_path,
        'check',
        *LINT_PATHS,
        '--extend-select',
        ','.join(EXTEND_SELECT),
        '--config',
        PER_FILE_IGNORES,
        '--output-format=json',
        '--no-cache',
    ]


def collect_records(root: Path = REPO_ROOT) -> list[dict]:
    """Run the audit ``ruff check`` and return parsed JSON records.

    Parameters
    ----------
    root
        Repository root; used as the working directory for Ruff.

    Returns
    -------
    list of dict
        Parsed Ruff JSON records.

    Raises
    ------
    SystemExit
        If the ``ruff`` executable cannot be located on ``PATH``.
    """
    ruff_path = shutil.which('ruff')
    if ruff_path is None:
        msg = "ruff not found on PATH; run via 'pixi run python tools/lint_rule_audit.py'."
        raise SystemExit(msg)
    # Ruff exits non-zero when violations exist, which is expected here.
    result = subprocess.run(  # noqa: S603
        ruff_command(ruff_path),
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding='utf-8',
    )
    if not result.stdout:
        raise SystemExit(result.stderr.strip() or 'ruff produced no output')
    return json.loads(result.stdout)


def format_table(summary: dict[str, dict]) -> str:
    """Render a per-rule table sorted by descending total count.

    Parameters
    ----------
    summary
        The mapping returned by :func:`aggregate`.

    Returns
    -------
    str
        A fixed-width, printable table. The ``safe`` column counts fixes
        applied by ``ruff --fix``; ``uns`` counts fixes that require
        ``--unsafe-fixes``.
    """
    header = (
        f'{"RULE":9}{"TOTAL":>7}{"src":>6}{"tests":>7}{"tut":>6}'
        f'{"safe":>6}{"uns":>5}  description'
    )
    lines = [header, '-' * len(header)]
    for code in sorted(summary, key=lambda c: -summary[c]['total']):
        entry = summary[code]
        lines.append(
            f'{code:9}{entry["total"]:7}{entry["src"]:6}{entry["tests"]:7}'
            f'{entry["tutorials"]:6}{entry["fix_safe"]:6}{entry["fix_unsafe"]:5}'
            f'  {entry["message"][:44]}'
        )
    total = sum(entry['total'] for entry in summary.values())
    safe = sum(entry['fix_safe'] for entry in summary.values())
    unsafe = sum(entry['fix_unsafe'] for entry in summary.values())
    lines.append('-' * len(header))
    lines.append(
        f'Total: {total} violations across {len(summary)} rules; '
        f'{safe} safe-fixable (ruff --fix), {unsafe} need --unsafe-fixes.'
    )
    return '\n'.join(lines)


def main() -> None:
    """Print the disabled-rule inventory table."""
    print(format_table(aggregate(collect_records())))


if __name__ == '__main__':
    main()
