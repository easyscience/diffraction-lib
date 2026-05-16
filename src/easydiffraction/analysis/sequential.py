# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Sequential fitting infrastructure: template, worker, CSV, recovery.
"""

from __future__ import annotations

import contextlib
import csv
import multiprocessing as mp
import os
import re
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from dataclasses import replace
from pathlib import Path
from typing import Any

from easydiffraction.display.progress import ACTIVITY_LABEL_FITTING
from easydiffraction.display.progress import ActivityIndicator
from easydiffraction.io.ascii import extract_data_paths_from_dir
from easydiffraction.utils.enums import VerbosityEnum
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log
from easydiffraction.utils.utils import build_table_renderable

# ------------------------------------------------------------------
#  Template dataclass (picklable for ProcessPoolExecutor)
# ------------------------------------------------------------------


@dataclass(frozen=True)
class SequentialFitExtractRule:
    """Picklable sequential-fit extract rule for worker execution."""

    id: str
    field_name: str
    pattern: str
    required: bool


@dataclass(frozen=True)
class SequentialFitTemplate:
    """
    Snapshot of everything a worker needs to recreate and fit a project.

    All fields are plain Python types (str, dict, list) so that the
    template can be pickled for ``ProcessPoolExecutor``.
    """

    structure_cif: str
    experiment_cif: str
    initial_params: dict[str, float]
    free_param_unique_names: list[str]
    alias_defs: list[dict[str, str]]
    constraint_defs: list[str]
    constraints_enabled: bool
    minimizer_tag: str
    calculator_tag: str
    diffrn_extract_rules: list[SequentialFitExtractRule]
    diffrn_field_names: list[str]


# ------------------------------------------------------------------
#  Worker function (module-level for pickling)
# ------------------------------------------------------------------


def _fit_worker(
    template: SequentialFitTemplate,
    data_path: str,
) -> dict[str, Any]:
    """
    Fit a single dataset in isolation.

    Creates a fresh Project, loads the template configuration via CIF,
    replaces data from *data_path*, applies initial parameters, fits,
    and returns a plain dict of results.

    Parameters
    ----------
    template : SequentialFitTemplate
        Snapshot of the project configuration.
    data_path : str
        Path to the data file to fit.

    Returns
    -------
    dict[str, Any]
        Result dict with keys: ``file_path``, ``fit_success``,
        ``chi_squared``, ``reduced_chi_squared``, ``n_iterations``, and
        per-parameter ``{unique_name}`` / ``{unique_name}.uncertainty``.
    """
    # Lazy import to avoid circular dependencies and keep the module
    # importable without heavy imports at top level.
    from easydiffraction.project.project import Project  # noqa: PLC0415

    result: dict[str, Any] = {'file_path': data_path}

    try:
        # 1. Create a fresh, isolated project
        Project._loading = True
        try:
            project = Project(name='_worker')
        finally:
            Project._loading = False

        # 2. Load structure from template CIF
        project.structures.add_from_cif_str(template.structure_cif)

        # 3. Load experiment from template CIF
        #    (full config + template data)
        project.experiments.add_from_cif_str(template.experiment_cif)
        expt = next(iter(project.experiments.values()))

        # 4. Replace data from the new data path
        expt._load_ascii_data_to_experiment(data_path)

        # 5. Extract diffrn metadata from the data file
        result.update(_extract_diffrn_values(expt, data_path, template.diffrn_extract_rules))

        # 6. Override parameter values from propagated starting values
        _apply_param_overrides(project, template.initial_params)

        # 7. Set free flags
        _set_free_params(project, template.free_param_unique_names)

        # 8. Apply constraints
        if template.constraints_enabled and template.alias_defs:
            _apply_constraints(
                project,
                template.alias_defs,
                template.constraint_defs,
            )

        # 9. Set calculator and minimizer
        #    (internal, no console output)
        from easydiffraction.analysis.fitting import Fitter  # noqa: PLC0415

        expt._set_calculator_type(template.calculator_tag, announce=False)
        project.analysis.fitter = Fitter(template.minimizer_tag)

        # 10. Fit
        original_verbosity = project.verbosity
        project.verbosity = 'silent'
        try:
            project.analysis.fit()
        finally:
            project.verbosity = original_verbosity

        # 11. Collect results
        result.update(_collect_results(project, template))

    except (
        RuntimeError,
        ValueError,
        TypeError,
        ArithmeticError,
        KeyError,
        IndexError,
        OSError,
    ) as exc:
        result['fit_success'] = False
        result['chi_squared'] = None
        result['reduced_chi_squared'] = None
        result['n_iterations'] = 0
        result['error'] = str(exc)

    return result


# ------------------------------------------------------------------
#  Helper functions
# ------------------------------------------------------------------


def _apply_param_overrides(
    project: object,
    overrides: dict[str, float],
) -> None:
    """
    Set parameter values from a ``{unique_name: value}`` dict.

    Parameters
    ----------
    project : object
        The worker's project instance.
    overrides : dict[str, float]
        Map of parameter unique names to values.
    """
    all_params = project.structures.parameters + project.experiments.parameters
    by_name = {p.unique_name: p for p in all_params if hasattr(p, 'unique_name')}
    for name, value in overrides.items():
        if name in by_name:
            by_name[name].value = value


def _set_free_params(
    project: object,
    free_names: list[str],
) -> None:
    """
    Mark parameters as free based on their unique names.

    Parameters
    ----------
    project : object
        The worker's project instance.
    free_names : list[str]
        Unique names of parameters to mark as free.
    """
    from easydiffraction.core.variable import Parameter  # noqa: PLC0415

    all_params = project.structures.parameters + project.experiments.parameters
    free_set = set(free_names)
    for p in all_params:
        if isinstance(p, Parameter) and hasattr(p, 'unique_name'):
            p.free = p.unique_name in free_set


def _apply_constraints(
    project: object,
    alias_defs: list[dict[str, str]],
    constraint_defs: list[str],
) -> None:
    """
    Recreate aliases and constraints in the worker project.

    Parameters
    ----------
    project : object
        The worker's project instance.
    alias_defs : list[dict[str, str]]
        Each dict has ``label`` and ``param_unique_name``.
    constraint_defs : list[str]
        Constraint expression strings.
    """
    all_params = project.structures.parameters + project.experiments.parameters
    by_name = {p.unique_name: p for p in all_params if hasattr(p, 'unique_name')}

    for alias_def in alias_defs:
        param = by_name.get(alias_def['param_unique_name'])
        if param is not None:
            project.analysis.aliases.create(
                label=alias_def['label'],
                param=param,
            )

    for expr in constraint_defs:
        project.analysis.constraints.create(expression=expr)


def _extract_diffrn_values(
    experiment: object,
    data_path: str,
    extract_rules: list[SequentialFitExtractRule],
) -> dict[str, float]:
    """
    Extract diffrn metadata from a single data file.

    Parameters
    ----------
    experiment : object
        The worker experiment whose diffrn descriptors are updated.
    data_path : str
        Path to the data file being fitted.
    extract_rules : list[SequentialFitExtractRule]
        Persisted extract rules resolved from analysis settings.

    Returns
    -------
    dict[str, float]
        Extracted ``diffrn.<field>`` values for the CSV row.

    Raises
    ------
    ValueError
        If a required rule does not match or captures a non-numeric
        value.
    """
    if not extract_rules:
        return {}

    compiled_rules = [(rule, re.compile(rule.pattern)) for rule in extract_rules]
    matched_rule_ids: set[str] = set()
    extracted_values: dict[str, float] = {}

    with Path(data_path).open(encoding='utf-8', errors='ignore') as handle:
        for line in handle:
            for rule, pattern in compiled_rules:
                if rule.id in matched_rule_ids:
                    continue

                match = pattern.search(line)
                if match is None:
                    continue

                try:
                    extracted_value = float(match.group(1))
                except (TypeError, ValueError) as error:
                    msg = (
                        f"Sequential extract rule '{rule.id}' captured a non-numeric value "
                        f"for 'diffrn.{rule.field_name}' in {data_path!r}."
                    )
                    raise ValueError(msg) from error

                descriptor = getattr(experiment.diffrn, rule.field_name)
                descriptor.value = extracted_value
                extracted_values[f'diffrn.{rule.field_name}'] = extracted_value
                matched_rule_ids.add(rule.id)

            if len(matched_rule_ids) == len(extract_rules):
                break

    missing_required = [
        f'{rule.id} (diffrn.{rule.field_name})'
        for rule in extract_rules
        if rule.required and rule.id not in matched_rule_ids
    ]
    if missing_required:
        msg = (
            f'Sequential extract rules did not match {data_path!r}: {", ".join(missing_required)}.'
        )
        raise ValueError(msg)

    return extracted_values


def _collect_results(
    project: object,
    template: SequentialFitTemplate,
) -> dict[str, Any]:
    """
    Collect fit results into a plain dict.

    Parameters
    ----------
    project : object
        The worker's project instance after fitting.
    template : SequentialFitTemplate
        The template (for knowing which params to collect).

    Returns
    -------
    dict[str, Any]
        Fit metrics and parameter values/uncertainties.
    """
    from easydiffraction.core.variable import Parameter  # noqa: PLC0415

    result: dict[str, Any] = {}
    fit_results = project.analysis.fit_results

    if fit_results is not None:
        result['fit_success'] = fit_results.success
        result['chi_squared'] = fit_results.chi_square
        result['reduced_chi_squared'] = fit_results.reduced_chi_square
        result['n_iterations'] = project.analysis.fitter.minimizer.tracker.best_iteration or 0
    else:
        result['fit_success'] = False
        result['chi_squared'] = None
        result['reduced_chi_squared'] = None
        result['n_iterations'] = 0

    # Collect all free parameter values and uncertainties
    all_params = project.structures.parameters + project.experiments.parameters
    free_set = set(template.free_param_unique_names)
    result['params'] = {}
    for p in all_params:
        if isinstance(p, Parameter) and p.unique_name in free_set:
            result[p.unique_name] = p.value
            result[f'{p.unique_name}.uncertainty'] = p.uncertainty
            result['params'][p.unique_name] = p.value

    return result


# ------------------------------------------------------------------
#  CSV helpers
# ------------------------------------------------------------------

_META_COLUMNS = [
    'file_path',
    'chi_squared',
    'reduced_chi_squared',
    'fit_success',
    'n_iterations',
]


def _build_csv_header(
    template: SequentialFitTemplate,
) -> list[str]:
    """
    Build the CSV column header list.

    Parameters
    ----------
    template : SequentialFitTemplate
        The template for diffrn fields and free param names.

    Returns
    -------
    list[str]
        Ordered list of column names.
    """
    header = list(_META_COLUMNS)
    header.extend(f'diffrn.{field}' for field in template.diffrn_field_names)
    for name in template.free_param_unique_names:
        header.extend((name, f'{name}.uncertainty'))
    return header


def _write_csv_header(
    csv_path: Path,
    header: list[str],
) -> None:
    """
    Create the CSV file and write the header row.

    Parameters
    ----------
    csv_path : Path
        Path to the CSV file.
    header : list[str]
        Column names.
    """
    with csv_path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()


def _append_to_csv(
    csv_path: Path,
    header: list[str],
    results: list[dict[str, Any]],
) -> None:
    """
    Append result rows to the CSV file.

    Parameters
    ----------
    csv_path : Path
        Path to the CSV file.
    header : list[str]
        Column names (for DictWriter fieldnames).
    results : list[dict[str, Any]]
        Result dicts from workers.
    """
    with csv_path.open('a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=header, extrasaction='ignore')
        for result in results:
            row = dict(result)
            file_path = row.get('file_path')
            if file_path:
                row['file_path'] = _relative_file_path_for_csv(csv_path, str(file_path))
            writer.writerow(row)


def _relative_file_path_for_csv(
    csv_path: Path,
    file_path: str,
) -> str:
    """Return *file_path* relative to the CSV-owning project."""
    project_path = csv_path.parent.parent.resolve()
    resolved_path = _resolve_project_file_path(project_path, file_path)
    relative_path = os.path.relpath(resolved_path, start=project_path)
    return relative_path.replace('\\', '/')


def _resolve_csv_file_path(
    csv_path: Path,
    file_path: str,
) -> str:
    """Resolve a stored CSV file path against the owning project."""
    project_path = csv_path.parent.parent.resolve()
    return str(_resolve_project_file_path(project_path, file_path))


def _resolve_project_file_path(
    project_path: Path,
    file_path: str,
) -> Path:
    """Resolve a data file path to an absolute path near the project."""
    path = Path(file_path)
    if path.is_absolute():
        return path.resolve()

    cwd_relative_path = path.resolve()
    if cwd_relative_path.is_relative_to(project_path):
        return cwd_relative_path

    return (project_path / path).resolve()


def _extract_params_from_row(row: dict[str, str]) -> dict[str, float]:
    """
    Extract parameter values from a single CSV row.

    Skips meta columns, diffrn columns, uncertainty columns, and empty
    values. Non-numeric values are silently ignored.

    Parameters
    ----------
    row : dict[str, str]
        A single CSV row as a dict.

    Returns
    -------
    dict[str, float]
        Parameter name → float value mapping.
    """
    params: dict[str, float] = {}
    for key, val in row.items():
        if key in _META_COLUMNS or key.startswith('diffrn.') or key.endswith('.uncertainty'):
            continue
        if val:
            with contextlib.suppress(ValueError, TypeError):
                params[key] = float(val)
    return params


def _read_csv_for_recovery(
    csv_path: Path,
) -> tuple[set[str], dict[str, float] | None]:
    """
    Read an existing CSV for crash recovery.

    Parameters
    ----------
    csv_path : Path
        Path to the CSV file.

    Returns
    -------
    tuple[set[str], dict[str, float] | None]
        A set of already-fitted file paths and the parameter values from
        the last successful row (or ``None`` if no rows).
    """
    fitted: set[str] = set()
    last_params: dict[str, float] | None = None

    if not csv_path.is_file():
        return fitted, last_params

    with csv_path.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            file_path = row.get('file_path', '')
            if file_path:
                fitted.add(_resolve_csv_file_path(csv_path, file_path))
            if row.get('fit_success', '').lower() == 'true':
                params = _extract_params_from_row(row)
                if params:
                    last_params = params

    return fitted, last_params


# ------------------------------------------------------------------
#  Template builder
# ------------------------------------------------------------------


def _build_template(project: object) -> SequentialFitTemplate:
    """
    Build a SequentialFitTemplate from the current project state.

    Parameters
    ----------
    project : object
        The main project instance (must have exactly 1 structure and 1
        experiment).

    Returns
    -------
    SequentialFitTemplate
        A frozen, picklable snapshot.

    Raises
    ------
    TypeError
        If a sequential extract target does not reference an existing
        numeric ``diffrn`` descriptor on the template experiment.
    """
    from easydiffraction.core.variable import NumericDescriptor  # noqa: PLC0415
    from easydiffraction.core.variable import Parameter  # noqa: PLC0415

    structure = next(iter(project.structures.values()))
    experiment = next(iter(project.experiments.values()))

    # Collect free parameter unique_names and initial values
    all_params = project.structures.parameters + project.experiments.parameters
    free_names: list[str] = []
    initial_params: dict[str, float] = {}
    for p in all_params:
        if isinstance(p, Parameter) and not p.user_constrained and p.free:
            free_names.append(p.unique_name)
            initial_params[p.unique_name] = p.value

    # Collect alias definitions
    alias_defs: list[dict[str, str]] = [
        {
            'label': alias.label.value,
            'param_unique_name': alias.param_unique_name.value,
        }
        for alias in project.analysis.aliases
    ]

    # Collect constraint expressions
    constraint_defs: list[str] = [
        constraint.expression.value for constraint in project.analysis.constraints
    ]

    # Validate and collect sequential diffrn extract rules against the
    # template experiment before worker execution starts.
    diffrn_extract_rules: list[SequentialFitExtractRule] = []
    diffrn_field_names: list[str] = []
    for extract_rule in project.analysis.sequential_fit_extract:
        target = extract_rule.target.value
        field_name = target.split('.', maxsplit=1)[1]
        descriptor = getattr(experiment.diffrn, field_name, None)
        if not isinstance(descriptor, NumericDescriptor):
            msg = (
                f"Sequential extract target '{target}' must reference an existing numeric "
                'diffrn descriptor on the template experiment.'
            )
            raise TypeError(msg)

        diffrn_extract_rules.append(
            SequentialFitExtractRule(
                id=extract_rule.id.value,
                field_name=field_name,
                pattern=extract_rule.pattern.value,
                required=extract_rule.required.value,
            )
        )
        if field_name not in diffrn_field_names:
            diffrn_field_names.append(field_name)

    return SequentialFitTemplate(
        structure_cif=structure.as_cif,
        experiment_cif=experiment.as_cif,
        initial_params=initial_params,
        free_param_unique_names=free_names,
        alias_defs=alias_defs,
        constraint_defs=constraint_defs,
        constraints_enabled=project.analysis.constraints.enabled,
        minimizer_tag=project.analysis.fitting.minimizer_type.value or 'lmfit',
        calculator_tag=experiment.calculation.calculator_type.value,
        diffrn_extract_rules=diffrn_extract_rules,
        diffrn_field_names=diffrn_field_names,
    )


# ------------------------------------------------------------------
#  Progress reporting
# ------------------------------------------------------------------


_SEQUENTIAL_CHUNK_PROGRESS_HEADERS = [
    'chunk',
    'progress',
    'time (s)',
    'files',
    'count',
    'average χ²',
    'status',
]
_SEQUENTIAL_CHUNK_PROGRESS_ALIGNMENTS = [
    'right',
    'right',
    'right',
    'left',
    'right',
    'right',
    'center',
]
_SEQUENTIAL_FILE_PROGRESS_HEADERS = ['file', 'progress', 'time (s)', 'χ²', 'iterations', 'status']
_SEQUENTIAL_FILE_PROGRESS_ALIGNMENTS = ['left', 'right', 'right', 'right', 'right', 'center']


@dataclass
class SequentialProgressState:
    """Mutable live progress rows for sequential fitting."""

    chunk_rows: list[list[str]]
    file_rows: list[list[str]]


@dataclass
class SequentialProgressContext:
    """Mutable sequential-fit progress handles and state."""

    verbosity: VerbosityEnum
    state: SequentialProgressState | None
    indicator: ActivityIndicator | None = None


@dataclass(frozen=True)
class _ChunkProgressMetrics:
    """File counts and elapsed time for a completed chunk."""

    completed_files_before: int
    total_files: int
    elapsed_time: float


@dataclass(frozen=True)
class SequentialRunPlan:
    """Resolved sequential-fit inputs and bookkeeping."""

    verbosity: VerbosityEnum
    template: SequentialFitTemplate
    csv_path: Path
    header: list[str]
    remaining: list[str]
    chunks: list[list[str]]
    max_workers: int
    processed_count: int


def _summarize_chunk_results(results: list[dict[str, Any]]) -> tuple[str, str]:
    """Return average reduced chi-square and status for a chunk."""
    num_files = len(results)
    successful = [r for r in results if r.get('fit_success')]
    if successful:
        avg_chi2 = sum(r['reduced_chi_squared'] for r in successful) / len(successful)
        chi2_str = f'{avg_chi2:.2f}'
    else:
        chi2_str = '—'

    if len(successful) == num_files:
        status = '✅'
    elif successful:
        status = '⚠️'
    else:
        status = '❌'

    return chi2_str, status


def _chunk_file_range(chunk: list[str]) -> str:
    """Return the inclusive file-name range for a chunk."""
    first_name = Path(chunk[0]).name
    last_name = Path(chunk[-1]).name
    if first_name == last_name:
        return first_name
    return f'{first_name} - {last_name}'


def _format_progress_percent(completed_items: int, total_items: int) -> str:
    """Return overall progress as a percentage string."""
    if total_items < 1:
        return '0.0%'
    clamped_completed = min(max(completed_items, 0), total_items)
    return f'{100.0 * clamped_completed / total_items:.1f}%'


def _format_elapsed_seconds(elapsed_time: float) -> str:
    """Return elapsed time in seconds with two decimal places."""
    return f'{max(elapsed_time, 0.0):.2f}'


def _build_chunk_progress_row(
    chunk_idx: int,
    total_chunks: int,
    chunk: list[str],
    results: list[dict[str, Any]],
    completed_files: int,
    total_files: int,
    elapsed_time: float,
) -> list[str]:
    """
    Return one sequential-progress table row for a completed chunk.
    """
    chi2_str, status = _summarize_chunk_results(results)
    return [
        f'{chunk_idx}/{total_chunks}',
        _format_progress_percent(completed_files, total_files),
        _format_elapsed_seconds(elapsed_time),
        _chunk_file_range(chunk),
        str(len(results)),
        chi2_str,
        status,
    ]


def _build_file_progress_rows(
    results: list[dict[str, Any]],
    completed_files_before: int,
    total_files: int,
    elapsed_time: float,
) -> list[list[str]]:
    """Return sequential-progress rows for individual file fits."""
    rows: list[list[str]] = []
    time_str = _format_elapsed_seconds(elapsed_time)
    for index, result in enumerate(results, start=1):
        reduced_chi2 = result.get('reduced_chi_squared')
        chi2_str = f'{reduced_chi2:.2f}' if reduced_chi2 is not None else '—'
        iterations = str(result.get('n_iterations') or 0)
        status = '✅' if result.get('fit_success') else '❌'
        rows.append([
            Path(result['file_path']).name,
            _format_progress_percent(completed_files_before + index, total_files),
            time_str,
            chi2_str,
            iterations,
            status,
        ])
    return rows


def _build_progress_renderable(
    verbosity: VerbosityEnum,
    progress_state: SequentialProgressState,
) -> object:
    """Build the sequential progress table renderable."""
    if verbosity is VerbosityEnum.FULL:
        return build_table_renderable(
            columns_headers=_SEQUENTIAL_FILE_PROGRESS_HEADERS,
            columns_alignment=_SEQUENTIAL_FILE_PROGRESS_ALIGNMENTS,
            columns_data=progress_state.file_rows,
        )

    return build_table_renderable(
        columns_headers=_SEQUENTIAL_CHUNK_PROGRESS_HEADERS,
        columns_alignment=_SEQUENTIAL_CHUNK_PROGRESS_ALIGNMENTS,
        columns_data=progress_state.chunk_rows,
    )


def _create_progress_context(
    verbosity: VerbosityEnum,
) -> SequentialProgressContext:
    """Return a mutable progress context for the given verbosity."""
    if verbosity is VerbosityEnum.SILENT:
        return SequentialProgressContext(verbosity=verbosity, state=None)

    return SequentialProgressContext(
        verbosity=verbosity,
        state=SequentialProgressState(chunk_rows=[], file_rows=[]),
    )


def _start_progress_display(progress: SequentialProgressContext) -> None:
    """
    Start the live progress indicator with an empty bordered table.
    """
    if progress.verbosity is VerbosityEnum.SILENT or progress.state is None:
        return

    indicator = ActivityIndicator(
        ACTIVITY_LABEL_FITTING,
        verbosity=progress.verbosity,
    )
    indicator.start()
    indicator.update(
        content=_build_progress_renderable(progress.verbosity, progress.state),
    )
    progress.indicator = indicator


def _stop_progress_display(progress: SequentialProgressContext) -> None:
    """Stop any active sequential-fit progress display."""
    if progress.indicator is not None:
        progress.indicator.stop()
        progress.indicator = None


def _print_sequential_header(
    analysis: object,
    verbosity: VerbosityEnum,
    remaining: list[str],
    chunks: list[list[str]],
    max_workers: int,
) -> None:
    """Print the user-facing sequential-fit header."""
    if verbosity is VerbosityEnum.SILENT:
        return

    console.paragraph('Sequential fitting')
    console.print(f"🚀 Starting fit process with '{analysis.fitter.selection}'...")
    console.print(f'📋 {len(remaining)} files in {len(chunks)} chunks (max_workers={max_workers})')
    console.print('📈 Goodness-of-fit progress:')


def _print_sequential_completion(
    verbosity: VerbosityEnum,
    processed_count: int,
    csv_path: Path,
) -> None:
    """Print the final sequential-fit summary."""
    if verbosity is VerbosityEnum.SILENT:
        return

    console.print(f'✅ Sequential fitting complete: {processed_count} files processed.')
    console.print(f'📄 Results saved to: {csv_path}')


def _prepare_sequential_run(
    analysis: object,
    data_dir: str,
    max_workers: int | str,
    chunk_size: int | None,
    file_pattern: str,
    *,
    reverse: bool,
) -> SequentialRunPlan | None:
    """Resolve inputs and bookkeeping for one sequential-fit run."""
    verbosity = VerbosityEnum(analysis.project.verbosity)

    _check_seq_preconditions(analysis.project)

    data_paths = extract_data_paths_from_dir(data_dir, file_pattern=file_pattern)
    template = _build_template(analysis.project)
    csv_path, header, already_fitted, template = _setup_csv_and_recovery(
        analysis.project,
        template,
        verbosity,
    )

    remaining = [path for path in data_paths if path not in already_fitted]
    if reverse:
        remaining.reverse()
    if not remaining:
        if verbosity is not VerbosityEnum.SILENT:
            console.print('✅ All files already fitted. Nothing to do.')
        return None

    resolved_workers, resolved_chunk_size = _resolve_workers(max_workers, chunk_size)
    chunks = [
        remaining[index : index + resolved_chunk_size]
        for index in range(0, len(remaining), resolved_chunk_size)
    ]
    return SequentialRunPlan(
        verbosity=verbosity,
        template=template,
        csv_path=csv_path,
        header=header,
        remaining=remaining,
        chunks=chunks,
        max_workers=resolved_workers,
        processed_count=len(already_fitted) + len(remaining),
    )


def _run_fit_loop_with_pool(
    max_workers: int,
    chunks: list[list[str]],
    template: SequentialFitTemplate,
    csv_info: tuple[Path, list[str]],
    progress: SequentialProgressContext,
) -> None:
    """Execute the fit loop inside a worker-pool context."""
    pool_cm, main_mod, main_file_bak, main_spec_bak = _create_pool_context(max_workers)
    try:
        _run_fit_loop(pool_cm, chunks, template, csv_info, progress)
    finally:
        _restore_main_state(main_mod, main_file_bak, main_spec_bak)


def _report_chunk_progress(
    chunk_idx: int,
    total_chunks: int,
    chunk: list[str],
    results: list[dict[str, Any]],
    progress: SequentialProgressContext,
    metrics: _ChunkProgressMetrics,
) -> None:
    """
    Report progress after a chunk completes.

    Parameters
    ----------
    chunk_idx : int
        1-based index of the current chunk.
    total_chunks : int
        Total number of chunks.
    chunk : list[str]
        File paths in the current chunk.
    results : list[dict[str, Any]]
        Results from the chunk.
    progress : SequentialProgressContext
        Mutable progress handles and accumulated table rows.
    metrics : _ChunkProgressMetrics
        File counts and elapsed time for the completed chunk.
    """
    if progress.verbosity is VerbosityEnum.SILENT or progress.state is None:
        return

    completed_files = metrics.completed_files_before + len(results)

    if progress.verbosity is VerbosityEnum.FULL:
        new_rows = _build_file_progress_rows(
            results,
            metrics.completed_files_before,
            metrics.total_files,
            metrics.elapsed_time,
        )
        progress.state.file_rows.extend(new_rows)
    else:
        new_rows = [
            _build_chunk_progress_row(
                chunk_idx,
                total_chunks,
                chunk,
                results,
                completed_files,
                metrics.total_files,
                metrics.elapsed_time,
            )
        ]
        progress.state.chunk_rows.extend(new_rows)

    if progress.indicator is not None:
        progress.indicator.update(
            content=_build_progress_renderable(progress.verbosity, progress.state),
        )


# ------------------------------------------------------------------
#  Main orchestration
# ------------------------------------------------------------------


def _check_seq_preconditions(project: object) -> list[str]:
    """
    Validate sequential fitting preconditions.

    Parameters
    ----------
    project : object
        The project to validate.

    Returns
    -------
    list[str]
        Data file paths from the template experiment.

    Raises
    ------
    ValueError
        If preconditions are not met.
    """
    if len(project.structures) != 1:
        msg = f'Sequential fitting requires exactly 1 structure, found {len(project.structures)}.'
        raise ValueError(msg)

    if len(project.experiments) != 1:
        msg = (
            f'Sequential fitting requires exactly 1 experiment (the template), '
            f'found {len(project.experiments)}.'
        )
        raise ValueError(msg)

    if project.info.path is None:
        msg = 'Project must be saved before sequential fitting. Call save_as() first.'
        raise ValueError(msg)

    from easydiffraction.core.variable import Parameter  # noqa: PLC0415

    free_params = [
        p
        for p in project.parameters
        if isinstance(p, Parameter) and not p.user_constrained and p.free
    ]
    if not free_params:
        msg = 'No free parameters found. Mark at least one parameter as free.'
        raise ValueError(msg)


def _setup_csv_and_recovery(
    project: object,
    template: SequentialFitTemplate,
    verb: VerbosityEnum,
) -> tuple[Path, list[str], set[str], SequentialFitTemplate]:
    """
    Set up CSV and perform crash recovery.

    Parameters
    ----------
    project : object
        The project instance.
    template : SequentialFitTemplate
        The fit template.
    verb : VerbosityEnum
        Output verbosity.

    Returns
    -------
    tuple[Path, list[str], set[str], SequentialFitTemplate]
        CSV path, header, already-fitted set, and updated template.
    """
    csv_path = project.info.path / 'analysis' / 'results.csv'
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    header = _build_csv_header(template)

    already_fitted, recovered_params = _read_csv_for_recovery(csv_path)

    if already_fitted:
        num_skipped = len(already_fitted)
        log.info(f'Resuming: {num_skipped} files already fitted, skipping.')
        if verb is not VerbosityEnum.SILENT:
            console.print(f'📂 Resuming from CSV: {num_skipped} files already fitted.')
        if recovered_params is not None:
            template = replace(template, initial_params=recovered_params)
    else:
        _write_csv_header(csv_path, header)

    return csv_path, header, already_fitted, template


def _resolve_workers(
    max_workers: int | str,
    chunk_size: int | None,
) -> tuple[int, int]:
    """
    Resolve worker count and chunk size.

    Parameters
    ----------
    max_workers : int | str
        Worker count or ``'auto'``.
    chunk_size : int | None
        Explicit chunk size or ``None``.

    Returns
    -------
    tuple[int, int]
        Resolved (max_workers, chunk_size).

    Raises
    ------
    ValueError
        If max_workers is invalid.
    """
    if isinstance(max_workers, str) and max_workers == 'auto':
        import os  # noqa: PLC0415

        max_workers = os.cpu_count() or 1

    if not isinstance(max_workers, int) or max_workers < 1:
        msg = f"max_workers must be a positive integer or 'auto', got {max_workers!r}"
        raise ValueError(msg)

    if chunk_size is None:
        chunk_size = max_workers

    return max_workers, chunk_size


def _create_pool_context(max_workers: int) -> tuple[object, object, object, object]:
    """
    Create a process pool context manager and back up __main__ state.

    Parameters
    ----------
    max_workers : int
        Number of workers. ``1`` → nullcontext.

    Returns
    -------
    tuple[object, object, object, object]
        ``(pool_cm, main_mod, main_file_bak, main_spec_bak)``.
    """
    main_mod = sys.modules.get('__main__')
    main_file_bak = getattr(main_mod, '__file__', None)
    main_spec_bak = getattr(main_mod, '__spec__', None)

    if max_workers > 1:
        if main_mod is not None and main_file_bak is not None:
            main_mod.__file__ = None  # type: ignore[assignment]
        if main_mod is not None and main_spec_bak is not None:
            main_mod.__spec__ = None
        spawn_ctx = mp.get_context('spawn')
        pool_cm = ProcessPoolExecutor(
            max_workers=max_workers,
            mp_context=spawn_ctx,
            max_tasks_per_child=100,
        )
    else:
        pool_cm = contextlib.nullcontext()

    return pool_cm, main_mod, main_file_bak, main_spec_bak


def _restore_main_state(
    main_mod: object,
    main_file_bak: object,
    main_spec_bak: object,
) -> None:
    """Restore ``__main__`` attributes after pool execution."""
    if main_mod is not None and main_file_bak is not None:
        main_mod.__file__ = main_file_bak
    if main_mod is not None and main_spec_bak is not None:
        main_mod.__spec__ = main_spec_bak


def _run_fit_loop(
    pool_cm: object,
    chunks: list[list[str]],
    template: SequentialFitTemplate,
    csv_info: tuple[Path, list[str]],
    progress: SequentialProgressContext,
) -> None:
    """
    Execute the chunk-based fitting loop.

    Parameters
    ----------
    pool_cm : object
        Pool context manager (ProcessPoolExecutor or nullcontext).
    chunks : list[list[str]]
        Chunked file paths.
    template : SequentialFitTemplate
        Starting template (updated via propagation).
    csv_info : tuple[Path, list[str]]
        Tuple of ``(csv_path, header)``.
    progress : SequentialProgressContext
        Mutable progress handles and accumulated table rows.
    """
    csv_path, header = csv_info
    total_chunks = len(chunks)
    total_files = sum(len(chunk) for chunk in chunks)
    completed_files = 0
    started_at = time.perf_counter()
    with pool_cm as executor:
        for chunk_idx, chunk in enumerate(chunks, start=1):
            if executor is not None:
                templates = [template] * len(chunk)
                results = list(executor.map(_fit_worker, templates, chunk))
            else:
                results = [_fit_worker(template, path) for path in chunk]

            _append_to_csv(csv_path, header, results)
            elapsed_time = time.perf_counter() - started_at
            _report_chunk_progress(
                chunk_idx,
                total_chunks,
                chunk,
                results,
                progress,
                _ChunkProgressMetrics(
                    completed_files_before=completed_files,
                    total_files=total_files,
                    elapsed_time=elapsed_time,
                ),
            )
            completed_files += len(results)

            # Propagate last successful params
            last_ok = _find_last_successful(results)
            if last_ok is not None:
                template = replace(template, initial_params=last_ok['params'])


def _find_last_successful(results: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Return the last successful result dict, or None."""
    for r in reversed(results):
        if r.get('fit_success') and r.get('params'):
            return r
    return None


def fit_sequential(
    analysis: object,
    data_dir: str,
    max_workers: int | str = 1,
    chunk_size: int | None = None,
    file_pattern: str = '*',
    *,
    reverse: bool = False,
) -> None:
    """
    Run sequential fitting over all data files in a directory.

    Parameters
    ----------
    analysis : object
        The ``Analysis`` instance (owns project reference).
    data_dir : str
        Path to directory containing data files.
    max_workers : int | str, default=1
        Number of parallel worker processes. ``1`` = sequential (no
        subprocess overhead). ``'auto'`` = physical CPU count. Uses
        ``ProcessPoolExecutor`` with ``spawn`` context when > 1.
    chunk_size : int | None, default=None
        Files per chunk. Default ``None`` uses ``max_workers``.
    file_pattern : str, default='*'
        Glob pattern to filter files in *data_dir*.
    reverse : bool, default=False
        When ``True``, process data files in reverse order.  Useful when
        starting values are better matched to the last file (e.g.
        highest-temperature dataset in a cooling scan).
    """
    if mp.parent_process() is not None:
        return

    plan = _prepare_sequential_run(
        analysis,
        data_dir,
        max_workers,
        chunk_size,
        file_pattern,
        reverse=reverse,
    )
    if plan is None:
        return

    _print_sequential_header(
        analysis,
        plan.verbosity,
        plan.remaining,
        plan.chunks,
        plan.max_workers,
    )

    progress = _create_progress_context(plan.verbosity)
    _start_progress_display(progress)
    try:
        _run_fit_loop_with_pool(
            plan.max_workers,
            plan.chunks,
            plan.template,
            (plan.csv_path, plan.header),
            progress,
        )
    finally:
        _stop_progress_display(progress)

    _print_sequential_completion(
        plan.verbosity,
        plan.processed_count,
        plan.csv_path,
    )
