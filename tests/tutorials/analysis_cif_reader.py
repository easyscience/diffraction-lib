# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Minimal reader for the fit results stored in a project ``analysis.cif``.

The tutorial-output tests read the persisted ``analysis/analysis.cif`` of
each saved tutorial project and compare a few fit-quality metrics and
refined parameter values against a committed baseline. Only the two
blocks needed for that comparison are parsed: the scalar
``_fit_result.*`` entries and the ``_fit_parameter`` loop.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

_FIT_RESULT_PREFIX = '_fit_result.'
_FIT_PARAMETER_NAME_TAG = '_fit_parameter.param_unique_name'
_BAYESIAN_VALUE_COLUMN = 'posterior_median'
_DETERMINISTIC_VALUE_COLUMN = 'start_value'


def _unquote(value: str) -> str:
    """Strip a single pair of surrounding single or double quotes."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


@dataclass(frozen=True)
class AnalysisCif:
    """Parsed fit results from a project ``analysis.cif`` file."""

    fit_result: dict[str, str]
    fit_parameters: dict[str, dict[str, str]]

    @property
    def result_kind(self) -> str | None:
        """Return ``'deterministic'`` or ``'bayesian'`` when recorded."""
        return self.fit_result.get('result_kind')

    def scalar(self, name: str) -> float | None:
        """Return a ``_fit_result`` scalar as a float, or ``None``."""
        raw = self.fit_result.get(name)
        if raw is None:
            return None
        try:
            return float(raw)
        except ValueError:
            return None

    def parameter_value(self, name: str) -> float:
        """Return the refined value of a named parameter.

        Bayesian fits use ``posterior_median``; deterministic fits use
        ``start_value`` (the value held after refinement).
        """
        columns = self.fit_parameters[name]
        if self.result_kind == 'bayesian' and _BAYESIAN_VALUE_COLUMN in columns:
            return float(columns[_BAYESIAN_VALUE_COLUMN])
        return float(columns[_DETERMINISTIC_VALUE_COLUMN])


def _read_loop(lines: list[str], start: int) -> tuple[int, list[str], list[str]]:
    """Read one ``loop_`` block, returning the next index, tags, rows."""
    index = start
    count = len(lines)
    tags: list[str] = []
    while index < count and lines[index].strip().startswith('_'):
        tags.append(lines[index].strip())
        index += 1
    rows: list[str] = []
    while index < count:
        stripped = lines[index].strip()
        if not stripped or stripped == 'loop_' or stripped.startswith('_'):
            break
        rows.append(stripped)
        index += 1
    return index, tags, rows


def _store_fit_parameters(
    tags: list[str],
    rows: list[str],
    fit_parameters: dict[str, dict[str, str]],
) -> None:
    """Populate ``fit_parameters`` from a ``_fit_parameter`` loop."""
    column_names = [tag.split('.', 1)[1] for tag in tags]
    for row in rows:
        tokens = row.split()
        if len(tokens) != len(column_names):
            continue
        fit_parameters[tokens[0]] = dict(zip(column_names, tokens, strict=True))


def parse_analysis_cif(text: str) -> AnalysisCif:
    """Parse ``_fit_result`` scalars and the ``_fit_parameter`` loop."""
    fit_result: dict[str, str] = {}
    fit_parameters: dict[str, dict[str, str]] = {}

    lines = text.splitlines()
    index = 0
    count = len(lines)
    while index < count:
        stripped = lines[index].strip()
        if not stripped:
            index += 1
            continue
        if stripped == 'loop_':
            index, tags, rows = _read_loop(lines, index + 1)
            if tags and tags[0] == _FIT_PARAMETER_NAME_TAG:
                _store_fit_parameters(tags, rows, fit_parameters)
            continue
        if stripped.startswith(_FIT_RESULT_PREFIX):
            key, _, value = stripped.partition(' ')
            fit_result[key.removeprefix(_FIT_RESULT_PREFIX)] = _unquote(value.strip())
        index += 1

    return AnalysisCif(fit_result=fit_result, fit_parameters=fit_parameters)


def read_analysis_cif(path: Path) -> AnalysisCif:
    """Parse the ``analysis.cif`` file at *path*."""
    return parse_analysis_cif(path.read_text(encoding='utf-8'))
