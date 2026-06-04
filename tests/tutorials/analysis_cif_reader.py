# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Minimal reader for the fit results stored in a saved tutorial project.

The tutorial-output tests read each saved project and compare a few
fit-quality metrics and refined parameter values against a committed
baseline.

Two sources are parsed:

* ``analysis/analysis.cif`` for the scalar ``_fit_result.*`` metrics and
  the ``_fit_parameter`` loop. The loop's ``start_value`` column is a
  *pre-fit* snapshot, so it is **not** used for deterministic parameter
  values; it only tells us which parameters were refined (and, for
  Bayesian fits, carries the post-fit ``posterior_median``).
* ``structures/*.cif`` and ``experiments/*.cif`` for the *refined*
  parameter values of deterministic fits, which the library persists as
  the live ``param.value`` (e.g. ``si 1.4525(73)``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from dataclasses import field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

_FIT_RESULT_PREFIX = '_fit_result.'
_FIT_PARAMETER_NAME_TAG = '_fit_parameter.param_unique_name'
_BAYESIAN_VALUE_COLUMN = 'posterior_median'

# Parameter attribute names that differ from their CIF data-name tail.
# ``param_unique_name`` uses the Python attribute name, the CIF uses the
# data name; they match for most parameters (``scale``, ``length_a``,
# ``occupancy``, ``fract_x`` ...) but not all. Extend as needed; an
# unmapped mismatch raises rather than silently passing.
_ATTR_TAG_ALIASES = {'adp_iso': 'U_iso_or_equiv'}

# A CIF number may carry a standard uncertainty in parentheses, e.g.
# ``1.4525(73)``, ``8.16(74)e+04``, ``1134.3(2.6)``, or empty ``1.358()``
# (single-crystal scales); strip it before float conversion.
_STANDARD_UNCERTAINTY_RE = re.compile(r'\([\d.]*\)')


def _unquote(value: str) -> str:
    """Strip a single pair of surrounding single or double quotes."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _cif_float(token: str) -> float:
    """Convert a CIF number (optionally with ``(su)``) to a float."""
    return float(_STANDARD_UNCERTAINTY_RE.sub('', token))


@dataclass(frozen=True)
class _CifBlock:
    """Scalars and loops parsed from one CIF data block."""

    scalars: dict[str, str]
    loops: list[tuple[list[str], list[list[str]]]]


@dataclass(frozen=True)
class AnalysisCif:
    """Parsed fit results for one saved tutorial project."""

    fit_result: dict[str, str]
    fit_parameters: dict[str, dict[str, str]]
    model_blocks: dict[str, _CifBlock] = field(default_factory=dict)

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

        Bayesian fits use the post-fit ``posterior_median`` recorded in
        ``analysis.cif``. Deterministic fits read the refined value from
        the model/experiment CIFs, because ``analysis.cif`` only keeps a
        pre-fit snapshot of each parameter.
        """
        columns = self.fit_parameters.get(name, {})
        if self.result_kind == 'bayesian' and _BAYESIAN_VALUE_COLUMN in columns:
            return float(columns[_BAYESIAN_VALUE_COLUMN])
        return self._resolve_refined_value(name)

    def _resolve_refined_value(self, name: str) -> float:
        """Resolve a refined value from the model/experiment CIF blocks.

        ``name`` is a ``param_unique_name`` of the form
        ``<block>.<category>.<attr>`` (scalar) or
        ``<block>.<category>.<id>.<attr>`` (one row of a loop).
        """
        parts = name.split('.')
        if len(parts) == 4:
            block_name, _category, row_id, attr = parts
        elif len(parts) == 3:
            block_name, _category, attr = parts
            row_id = None
        else:
            unexpected = f'Cannot resolve parameter {name!r}: unexpected name structure.'
            raise ValueError(unexpected)

        block = self.model_blocks.get(block_name)
        if block is None:
            missing = f'No model/experiment CIF block {block_name!r} for parameter {name!r}.'
            raise ValueError(missing)

        suffix = '.' + _ATTR_TAG_ALIASES.get(attr, attr)

        if row_id is None:
            matches = [raw for tag, raw in block.scalars.items() if tag.endswith(suffix)]
            if len(matches) != 1:
                ambiguous = (
                    f'Expected one scalar ending in {suffix!r} for {name!r}, found {len(matches)}.'
                )
                raise ValueError(ambiguous)
            return _cif_float(matches[0])

        for tags, rows in block.loops:
            column = next((i for i, tag in enumerate(tags) if tag.endswith(suffix)), None)
            if column is None:
                continue
            for row in rows:
                if row and row[0] == row_id and column < len(row):
                    return _cif_float(row[column])
        not_found = f'No loop row {row_id!r} ending in {suffix!r} for {name!r}.'
        raise ValueError(not_found)


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


def _parse_cif_block(text: str) -> _CifBlock:
    """Parse scalars and loops from one model/experiment CIF text."""
    scalars: dict[str, str] = {}
    loops: list[tuple[list[str], list[list[str]]]] = []

    lines = text.splitlines()
    index = 0
    count = len(lines)
    while index < count:
        stripped = lines[index].strip()
        if not stripped or stripped.startswith(('#', 'data_')):
            index += 1
            continue
        if stripped == 'loop_':
            index, tags, rows = _read_loop(lines, index + 1)
            loops.append((tags, [row.split() for row in rows]))
            continue
        if stripped.startswith('_'):
            tag, _, value = stripped.partition(' ')
            scalars[tag] = _unquote(value.strip())
        index += 1

    return _CifBlock(scalars=scalars, loops=loops)


def _load_model_blocks(project_dir: Path) -> dict[str, _CifBlock]:
    """Parse every structure and experiment CIF under *project_dir*."""
    blocks: dict[str, _CifBlock] = {}
    for subdir in ('structures', 'experiments'):
        directory = project_dir / subdir
        if not directory.is_dir():
            continue
        for cif_path in sorted(directory.glob('*.cif')):
            text = cif_path.read_text(encoding='utf-8')
            name = next(
                (
                    line.strip().removeprefix('data_')
                    for line in text.splitlines()
                    if line.strip().startswith('data_')
                ),
                None,
            )
            if name is not None:
                blocks[name] = _parse_cif_block(text)
    return blocks


def parse_analysis_cif(text: str, model_blocks: dict[str, _CifBlock] | None = None) -> AnalysisCif:
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

    return AnalysisCif(
        fit_result=fit_result,
        fit_parameters=fit_parameters,
        model_blocks=model_blocks or {},
    )


def read_analysis_cif(path: Path) -> AnalysisCif:
    """Parse ``analysis.cif`` at *path* plus its sibling model CIFs.

    Deterministic refined parameter values are read from the
    ``structures/`` and ``experiments/`` CIFs of the same project
    directory (``<project>/analysis/analysis.cif`` → ``<project>``).
    """
    model_blocks = _load_model_blocks(path.parents[1])
    return parse_analysis_cif(path.read_text(encoding='utf-8'), model_blocks)
