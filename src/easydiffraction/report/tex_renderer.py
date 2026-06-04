# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Render project reports as LaTeX source bundles."""

from __future__ import annotations

import csv
import pathlib
import shutil

from jinja2 import Environment
from jinja2 import PackageLoader
from jinja2 import select_autoescape

from easydiffraction.report.fit_plot import fit_bragg_tick_styles
from easydiffraction.report.fit_plot import fit_plot_axis_styles
from easydiffraction.report.fit_plot import fit_plot_geometry
from easydiffraction.report.fit_plot import fit_plot_ranges
from easydiffraction.report.fit_plot import fit_plot_styles
from easydiffraction.report.fit_plot import fit_scatter_geometry
from easydiffraction.report.fit_plot import fit_scatter_ranges
from easydiffraction.report.fit_plot import fit_scatter_style
from easydiffraction.report.style import report_style_context

_TEMPLATE_NAME = 'tex/report.tex.j2'
_FIGURE_TEMPLATE_NAME = 'tex/figure.tex.j2'
_FIGURE_SC_TEMPLATE_NAME = 'tex/figure_sc.tex.j2'
_TEX_SPECIAL_CHARS = {
    '\\': r'\textbackslash{}',
    '&': r'\&',
    '%': r'\%',
    '$': r'\$',
    '#': r'\#',
    '_': r'\_',
    '{': r'\{',
    '}': r'\}',
    '~': r'\textasciitilde{}',
    '^': r'\textasciicircum{}',
}
_FIT_X_FIELD_TAGS = {
    'two_theta': '_pd_proc.2theta_scan',
    'time_of_flight': '_pd_meas.time_of_flight',
    'd_spacing': '_pd_proc.d_spacing',
    'x': '_pd_proc.r',
    'r': '_pd_proc.r',
}
_FIT_CSV_FIELD_TAGS = (
    ('point_id', '_pd_data.point_id'),
    ('d_spacing', '_pd_proc.d_spacing'),
    ('intensity_meas', '_pd_meas.intensity_total'),
    ('intensity_meas_su', '_pd_meas.intensity_total_su'),
    ('intensity_calc', '_pd_calc.intensity_total'),
    ('intensity_bkg', '_pd_calc.intensity_bkg'),
    ('calc_status', '_pd_data.refinement_status'),
)
_REFLN_CSV_FIELD_TAGS = (
    ('id', '_refln.id'),
    ('phase_id', '_refln.phase_id'),
    ('d_spacing', '_refln.d_spacing'),
    ('sin_theta_over_lambda', '_refln.sin_theta_over_lambda'),
    ('index_h', '_refln.index_h'),
    ('index_k', '_refln.index_k'),
    ('index_l', '_refln.index_l'),
    ('f_calc', '_refln.f_calc'),
    ('f_squared_calc', '_refln.f_squared_calc'),
    ('two_theta', '_refln.two_theta'),
    ('time_of_flight', '_refln.time_of_flight'),
)


def tex_report_path(
    project: object,
    path: str | pathlib.Path | None = None,
) -> pathlib.Path:
    """
    Return the target TeX report path for a project.

    Parameters
    ----------
    project : object
        Project instance.
    path : str | pathlib.Path | None, default=None
        Explicit report path.

    Returns
    -------
    pathlib.Path
        Resolved report path.

    Raises
    ------
    FileNotFoundError
        If no path is supplied and the project has not been saved.
    """
    if path is not None:
        return pathlib.Path(path)

    project_path = getattr(getattr(project, 'info', None), 'path', None)
    if project_path is None:
        msg = 'Project has no saved path. Save the project first.'
        raise FileNotFoundError(msg)

    project_name = getattr(project, 'name', 'project')
    return pathlib.Path(project_path) / 'reports' / 'tex' / f'{project_name}.tex'


def render_tex_report(context: dict[str, object]) -> str:
    """
    Render a report data context as LaTeX.

    Parameters
    ----------
    context : dict[str, object]
        Data returned by ``Report.data_context()``.

    Returns
    -------
    str
        Complete LaTeX document.
    """
    template_context = dict(context)
    template_context['report_style'] = report_style_context()
    template_context['tex'] = _tex_context(
        context,
        fit_csv_paths=_fit_csv_paths(context),
        fit_figure_paths=_fit_figure_paths(context),
        structure_figure_paths=_structure_figure_paths(context),
    )
    return _environment().get_template(_TEMPLATE_NAME).render(**template_context)


def save_tex_report(
    project: object,
    context: dict[str, object],
    *,
    path: str | pathlib.Path | None = None,
) -> pathlib.Path:
    """
    Write a TeX report bundle.

    Parameters
    ----------
    project : object
        Project instance.
    context : dict[str, object]
        Data returned by ``Report.data_context()``.
    path : str | pathlib.Path | None, default=None
        Explicit report path.

    Returns
    -------
    pathlib.Path
        Path of the written main TeX document.
    """
    output_path = tex_report_path(project, path)
    tex_dir = output_path.parent

    _prepare_tex_bundle(tex_dir)

    template_context = dict(context)
    template_context['report_style'] = report_style_context()
    fit_asset_paths = _write_fit_assets(project, context, tex_dir)
    structure_figure_paths = _write_structure_assets(project, context, tex_dir)
    template_context['tex'] = _tex_context(
        context,
        fit_csv_paths=fit_asset_paths['csv'],
        fit_figure_paths=fit_asset_paths['figure'],
        structure_figure_paths=structure_figure_paths,
    )
    output_path.write_text(
        _render_prepared_context(template_context),
        encoding='utf-8',
    )
    return output_path


def _render_prepared_context(context: dict[str, object]) -> str:
    """Render a context that already contains TeX asset paths."""
    return _environment().get_template(_TEMPLATE_NAME).render(**context)


def _environment() -> Environment:
    """Return the Jinja environment for TeX report templates."""
    environment = Environment(
        loader=PackageLoader('easydiffraction.report', 'templates'),
        autoescape=select_autoescape(
            enabled_extensions=(),
            default_for_string=False,
            default=False,
        ),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    environment.filters['tex'] = _tex_escape
    environment.filters['tex_axis_label'] = _tex_axis_label
    environment.filters['tex_markup'] = _tex_markup
    environment.filters['tex_number'] = _tex_number
    environment.filters['tex_unit'] = _tex_unit
    return environment


def _prepare_tex_bundle(tex_dir: pathlib.Path) -> None:
    """Remove managed bundle directories before writing TeX assets."""
    tex_dir.mkdir(parents=True, exist_ok=True)
    for dirname in ('data', 'styles', 'figures'):
        path = tex_dir / dirname
        if path.exists():
            shutil.rmtree(path)


def _write_fit_assets(
    project: object,
    context: dict[str, object],
    out_dir: pathlib.Path,
) -> dict[str, dict[str, str]]:
    """Write fit-data CSV and figure TeX files."""
    csv_paths: dict[str, str] = {}
    figure_paths: dict[str, str] = {}
    project_experiments = _project_experiments_by_id(project)
    for experiment in _experiment_contexts(context):
        fit_data = experiment.get('fit_data')
        if fit_data is None:
            continue
        experiment_id = str(experiment.get('id') or 'experiment')
        source_experiment = project_experiments.get(experiment_id)
        if _is_scatter_fit_data(fit_data):
            csv_path = _write_fit_scatter_csv(experiment_id, fit_data, out_dir)
            figure_path = _write_fit_scatter_tex(
                experiment=experiment,
                csv_path=csv_path,
                out_dir=out_dir,
            )
        else:
            csv_path = _write_fit_csv(
                experiment_id,
                experiment,
                source_experiment,
                fit_data,
                out_dir,
            )
            bragg_csvs = _write_bragg_csvs(
                experiment_id,
                experiment,
                source_experiment,
                fit_data,
                out_dir,
            )
            figure_path = _write_fit_figure_tex(
                experiment=experiment,
                csv_path=csv_path,
                bragg_csvs=bragg_csvs,
                out_dir=out_dir,
            )
        csv_paths[experiment_id] = f'data/{csv_path.name}'
        figure_paths[experiment_id] = f'data/{figure_path.stem}.pdf'
    return {'csv': csv_paths, 'figure': figure_paths}


def _is_scatter_fit_data(fit_data: dict[str, object]) -> bool:
    """Return whether fit data is a single-crystal agreement scatter."""
    x_data = fit_data.get('x') or {}
    return x_data.get('name') == 'intensity_calc'


def _tex_context(
    context: dict[str, object],
    *,
    fit_csv_paths: dict[str, str],
    fit_figure_paths: dict[str, str],
    structure_figure_paths: dict[str, str],
) -> dict[str, object]:
    """Return TeX-specific render context."""
    return {
        'fit_csv_paths': fit_csv_paths,
        'fit_figure_paths': fit_figure_paths,
        'structure_figure_paths': structure_figure_paths,
        'fit_bragg_tick_styles': fit_bragg_tick_styles(),
        'fit_plot_ranges': _fit_plot_ranges(context),
        'fit_plot_styles': fit_plot_styles(),
    }


def _fit_plot_ranges(context: dict[str, object]) -> dict[str, dict[str, float]]:
    """Return fit-figure axis ranges by experiment id."""
    ranges = {}
    for experiment in _experiment_contexts(context):
        fit_data = experiment.get('fit_data')
        if fit_data is None:
            continue
        if _is_scatter_fit_data(fit_data):
            continue
        experiment_id = str(experiment.get('id') or 'experiment')
        ranges[experiment_id] = fit_plot_ranges(fit_data)
    return ranges


def _write_fit_csv(
    expt_id: str,
    experiment: dict[str, object],
    source_experiment: object | None,
    fit_data: dict[str, object],
    out_dir: pathlib.Path,
) -> pathlib.Path:
    """Write one fit-data CSV file under ``out_dir / 'data'``."""
    data_dir = out_dir / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    csv_path = data_dir / _fit_csv_filename(expt_id)
    columns = _fit_csv_columns(expt_id, experiment, source_experiment, fit_data)
    _write_csv(csv_path, expt_id, columns)
    return csv_path


def _write_fit_figure_tex(
    *,
    experiment: dict[str, object],
    csv_path: pathlib.Path,
    bragg_csvs: dict[str, dict[str, str]],
    out_dir: pathlib.Path,
) -> pathlib.Path:
    """Write one standalone pgfplots TeX figure."""
    data_dir = out_dir / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    experiment_id = str(experiment.get('id') or 'experiment')
    fit_data = experiment['fit_data']
    figure_path = data_dir / f'{_safe_asset_stem(experiment_id)}.tex'
    template_context = {
        'experiment': experiment,
        'fit_data': fit_data,
        'csv_filename': csv_path.name,
        'fit_csv': _fit_csv_plot_columns(experiment, fit_data),
        'bragg_tick_sources': _bragg_tick_sources(fit_data, bragg_csvs),
        'geometry': fit_plot_geometry(fit_data),
        'ranges': fit_plot_ranges(fit_data),
        'axis_styles': fit_plot_axis_styles(),
        'styles': fit_plot_styles(),
        'bragg_styles': fit_bragg_tick_styles(),
    }
    figure_path.write_text(
        _environment()
        .get_template(_FIGURE_TEMPLATE_NAME)
        .render(
            **template_context,
        ),
        encoding='utf-8',
    )
    return figure_path


def _write_fit_scatter_csv(
    expt_id: str,
    fit_data: dict[str, object],
    out_dir: pathlib.Path,
) -> pathlib.Path:
    """Write the single-crystal agreement-scatter CSV file."""
    data_dir = out_dir / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    csv_path = data_dir / _fit_csv_filename(expt_id)
    meas = fit_data['series']['meas']
    calc_values = list(fit_data['x']['values'])
    su = meas.get('su')
    su_values = list(su) if su is not None else [0.0] * len(calc_values)
    columns = [
        ('icalc', calc_values),
        ('imeas', list(meas['values'])),
        ('imeas_su', su_values),
    ]
    _write_csv(csv_path, expt_id, columns)
    return csv_path


def _write_fit_scatter_tex(
    *,
    experiment: dict[str, object],
    csv_path: pathlib.Path,
    out_dir: pathlib.Path,
) -> pathlib.Path:
    """Write one standalone single-crystal scatter TeX figure."""
    data_dir = out_dir / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    experiment_id = str(experiment.get('id') or 'experiment')
    fit_data = experiment['fit_data']
    figure_path = data_dir / f'{_safe_asset_stem(experiment_id)}.tex'
    template_context = {
        'experiment': experiment,
        'fit_data': fit_data,
        'csv_filename': csv_path.name,
        'fit_csv': {'x': 'icalc', 'meas': 'imeas', 'meas_su': 'imeas_su'},
        'geometry': fit_scatter_geometry(),
        'ranges': fit_scatter_ranges(fit_data),
        'axis_styles': fit_plot_axis_styles(),
        'style': fit_scatter_style(),
    }
    figure_path.write_text(
        _environment().get_template(_FIGURE_SC_TEMPLATE_NAME).render(**template_context),
        encoding='utf-8',
    )
    return figure_path


def _fit_csv_paths(context: dict[str, object]) -> dict[str, str]:
    """Return expected fit-data CSV paths for TeX rendering."""
    paths = {}
    for experiment in _experiment_contexts(context):
        if experiment.get('fit_data') is None:
            continue
        experiment_id = str(experiment.get('id') or 'experiment')
        paths[experiment_id] = f'data/{_fit_csv_filename(experiment_id)}'
    return paths


def _fit_figure_paths(context: dict[str, object]) -> dict[str, str]:
    """Return expected fit-figure PDF paths for TeX rendering."""
    paths = {}
    for experiment in _experiment_contexts(context):
        if experiment.get('fit_data') is None:
            continue
        experiment_id = str(experiment.get('id') or 'experiment')
        paths[experiment_id] = f'data/{_safe_asset_stem(experiment_id)}.pdf'
    return paths


def _structure_asset_stem(struct_id: str) -> str:
    """Return a filesystem-safe stem for a structure figure asset."""
    return f'struct_{_safe_asset_stem(struct_id)}'


def _structure_figure_paths(context: dict[str, object]) -> dict[str, str]:
    """Return expected structure-figure PNG paths for TeX rendering."""
    paths: dict[str, str] = {}
    for structure in context.get('structures') or []:
        if not isinstance(structure, dict):
            continue
        struct_id = str(structure.get('id') or 'structure')
        paths[struct_id] = f'data/{_structure_asset_stem(struct_id)}.png'
    return paths


def _write_structure_assets(
    project: object,
    context: dict[str, object],
    out_dir: pathlib.Path,
) -> dict[str, str]:
    """Write one z-buffered PNG structure figure per structure."""
    from easydiffraction.display.structure.builder import build_scene  # noqa: PLC0415
    from easydiffraction.display.structure.builder import (  # noqa: PLC0415
        structure_feature_availability,
    )
    from easydiffraction.display.structure.renderers.raster import (  # noqa: PLC0415
        RasterStructureRenderer,
    )

    del context
    structures = getattr(project, 'structures', None)
    values = getattr(structures, 'values', None)
    if not callable(values):
        return {}

    renderer = RasterStructureRenderer()
    window = project.structure_view.view_range()
    style = project.structure_style
    data_dir = out_dir / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)

    figure_paths: dict[str, str] = {}
    for structure in values():
        struct_id = str(getattr(structure, 'name', '') or 'structure')
        availability = structure_feature_availability(structure, style=style)
        features = project.display._resolve_structure_features('auto', availability)
        scene = build_scene(structure, style=style, view_range=window, features=features)
        figure_path = data_dir / f'{_structure_asset_stem(struct_id)}.png'
        figure_path.write_bytes(renderer.render_png(scene, features=features))
        figure_paths[struct_id] = f'data/{figure_path.name}'
    return figure_paths


def _project_experiments_by_id(project: object) -> dict[str, object]:
    """Return project experiment objects keyed by datablock id."""
    experiments = getattr(project, 'experiments', None)
    values = getattr(experiments, 'values', None)
    if not callable(values):
        return {}
    return {str(getattr(experiment, 'name', '')): experiment for experiment in values()}


def _experiment_contexts(context: dict[str, object]) -> list[dict[str, object]]:
    """Return experiment contexts from a report context."""
    experiments = context.get('experiments')
    if not isinstance(experiments, list):
        return []
    return [experiment for experiment in experiments if isinstance(experiment, dict)]


def _fit_csv_filename(expt_id: str) -> str:
    """Return a filesystem-safe fit-data CSV filename."""
    return f'{_safe_asset_stem(expt_id)}.csv'


def _safe_asset_stem(identifier: str) -> str:
    """Return a filesystem-safe report asset stem."""
    safe_id = ''.join(
        char if char.isascii() and (char.isalnum() or char in {'-', '_'}) else '_'
        for char in identifier
    ).strip('_')
    if not safe_id:
        safe_id = 'experiment'
    return safe_id


def _fit_csv_columns(
    expt_id: str,
    experiment: dict[str, object],
    source_experiment: object | None,
    fit_data: dict[str, object],
) -> list[tuple[str, list[object]]]:
    """Return ordered CSV columns for one fit-data payload."""
    x_data = fit_data['x']
    series = fit_data['series']
    meas = series['meas']
    calc = series['calc']
    bkg = series.get('bkg')
    category_values = _category_values(
        source_experiment,
        experiment,
        code='pd_data',
    )
    x_field = _fit_x_field(category_values, fit_data)
    row_count = len(list(x_data['values']))

    columns = [
        (
            _FIT_X_FIELD_TAGS[x_field],
            _fit_csv_values(
                category_values,
                x_field,
                list(x_data['values']),
            ),
        ),
    ]
    fallback_values = {
        'point_id': [str(index + 1) for index in range(row_count)],
        'd_spacing': _empty_csv_values(row_count),
        'intensity_meas': list(meas['values']),
        'intensity_meas_su': _series_values_or_empty(meas.get('su'), row_count),
        'intensity_calc': list(calc['values']),
        'intensity_bkg': _series_values_or_empty(
            None if bkg is None else bkg.get('values'),
            row_count,
        ),
        'calc_status': _empty_csv_values(row_count),
    }
    columns.extend(
        (
            tag,
            _fit_csv_values(category_values, field_name, fallback_values[field_name]),
        )
        for field_name, tag in _FIT_CSV_FIELD_TAGS
    )
    _validate_fit_csv_columns(expt_id, columns)
    return columns


def _fit_x_field(
    category_values: dict[str, list[object]],
    fit_data: dict[str, object],
) -> str:
    """Return the pd-data field used as the fit plot x axis."""
    for field_name in _FIT_X_FIELD_TAGS:
        if field_name in category_values:
            return field_name
    x_data = fit_data['x']
    x_name = str(x_data.get('name') or '')
    if x_name in _FIT_X_FIELD_TAGS:
        return x_name
    return 'two_theta'


def _fit_csv_plot_columns(
    experiment: dict[str, object],
    fit_data: dict[str, object],
) -> dict[str, str]:
    """Return CSV column tags used by the standalone fit figure."""
    x_field = _fit_x_field(_context_category_values(experiment, 'pd_data'), fit_data)
    return {
        'x': _FIT_X_FIELD_TAGS[x_field],
        'meas': '_pd_meas.intensity_total',
        'calc': '_pd_calc.intensity_total',
    }


def _fit_csv_values(
    category_values: dict[str, list[object]],
    field_name: str,
    fallback: list[object],
) -> list[object]:
    """Return category values or fallback values."""
    values = category_values.get(field_name)
    if values is None or all(_is_csv_empty(value) for value in values):
        return fallback
    return values


def _series_values_or_empty(values: object, row_count: int) -> list[object]:
    """Return series values or an empty CSV column."""
    if values is None:
        return _empty_csv_values(row_count)
    return list(values)


def _empty_csv_values(row_count: int) -> list[object]:
    """Return an empty CSV column with ``row_count`` rows."""
    return [''] * row_count


def _write_bragg_csvs(
    expt_id: str,
    experiment: dict[str, object],
    source_experiment: object | None,
    fit_data: dict[str, object],
    out_dir: pathlib.Path,
) -> dict[str, dict[str, str]]:
    """Write one Bragg-position CSV per phase."""
    data_dir = out_dir / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    values = _category_values(source_experiment, experiment, code='refln')
    if values:
        return _write_refln_category_csvs(expt_id, values, data_dir)
    return _write_bragg_tick_set_csvs(expt_id, fit_data, data_dir)


def _write_refln_category_csvs(
    expt_id: str,
    values: dict[str, list[object]],
    data_dir: pathlib.Path,
) -> dict[str, dict[str, str]]:
    """Write reflection-category rows split by phase id."""
    phase_values = values.get('phase_id')
    if phase_values is None:
        return {}

    row_indexes_by_phase: dict[str, list[int]] = {}
    for row_index, phase_value in enumerate(phase_values):
        if _is_csv_empty(phase_value):
            continue
        phase_id = str(phase_value)
        row_indexes_by_phase.setdefault(phase_id, []).append(row_index)

    csvs: dict[str, dict[str, str]] = {}
    x_column = _refln_x_column(values)
    for phase_id, row_indexes in row_indexes_by_phase.items():
        csv_path = data_dir / _bragg_csv_filename(expt_id, phase_id)
        columns = _refln_csv_columns(values, row_indexes)
        _write_csv(csv_path, expt_id, columns)
        csvs[phase_id] = {
            'filename': csv_path.name,
            'x_column': x_column,
        }
    return csvs


def _refln_x_column(values: dict[str, list[object]]) -> str:
    """Return the reflection CSV x column for Bragg ticks."""
    if 'two_theta' in values:
        return '_refln.two_theta'
    if 'time_of_flight' in values:
        return '_refln.time_of_flight'
    return '_refln.two_theta'


def _refln_csv_columns(
    values: dict[str, list[object]],
    row_indexes: list[int],
) -> list[tuple[str, list[object]]]:
    """Return ordered reflection CSV columns."""
    return [
        (
            tag,
            [values.get(field_name, [])[index] for index in row_indexes],
        )
        for field_name, tag in _REFLN_CSV_FIELD_TAGS
        if field_name in values
    ]


def _write_bragg_tick_set_csvs(
    expt_id: str,
    fit_data: dict[str, object],
    data_dir: pathlib.Path,
) -> dict[str, dict[str, str]]:
    """Write fallback Bragg CSVs from plot tick-set data."""
    csvs: dict[str, dict[str, str]] = {}
    for tick_set in fit_data.get('bragg_tick_sets') or ():
        phase_id = str(tick_set.phase_id)
        csv_path = data_dir / _bragg_csv_filename(expt_id, phase_id)
        columns = _bragg_tick_set_columns(tick_set)
        _write_csv(csv_path, expt_id, columns)
        csvs[phase_id] = {
            'filename': csv_path.name,
            'x_column': '_refln.two_theta',
        }
    return csvs


def _bragg_tick_set_columns(tick_set: object) -> list[tuple[str, list[object]]]:
    """Return reflection CSV columns from one Bragg tick set."""
    row_count = len(tick_set.x)
    return [
        ('_refln.id', [str(index + 1) for index in range(row_count)]),
        ('_refln.phase_id', [tick_set.phase_id] * row_count),
        ('_refln.index_h', list(tick_set.h)),
        ('_refln.index_k', list(tick_set.k)),
        ('_refln.index_l', list(tick_set.ell)),
        ('_refln.f_calc', list(tick_set.f_calc)),
        ('_refln.f_squared_calc', list(tick_set.f_squared_calc)),
        ('_refln.two_theta', list(tick_set.x)),
    ]


def _bragg_csv_filename(expt_id: str, phase_id: str) -> str:
    """Return the Bragg-position CSV filename for one phase."""
    return f'{_safe_asset_stem(expt_id)}_{_safe_asset_stem(phase_id)}.csv'


def _bragg_tick_sources(
    fit_data: dict[str, object],
    bragg_csvs: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    """Return template context for Bragg-position CSV sources."""
    sources = []
    for tick_set in fit_data.get('bragg_tick_sets') or ():
        phase_id = str(tick_set.phase_id)
        bragg_csv = bragg_csvs.get(phase_id)
        if bragg_csv is None:
            continue
        sources.append({
            'phase_id': phase_id,
            'csv_filename': bragg_csv['filename'],
            'x_column': bragg_csv['x_column'],
        })
    return sources


def _category_values(
    source_experiment: object | None,
    experiment: dict[str, object],
    *,
    code: str,
) -> dict[str, list[object]]:
    """Return full category values from the project or context."""
    if source_experiment is not None:
        values = _source_category_values(source_experiment, code)
        if values:
            return values
    return _context_category_values(experiment, code)


def _source_category_values(
    source_experiment: object,
    code: str,
) -> dict[str, list[object]]:
    """Return category values from a live experiment object."""
    category = _source_category(source_experiment, code)
    if category is None:
        return {}
    category_values = getattr(category, 'values', None)
    if not callable(category_values):
        return {}
    items = list(category_values())
    if not items:
        return {}
    parameter_rows = [_category_parameters(category, item) for item in items]
    names = [parameter.name for parameter in parameter_rows[0]]
    values = {name: [] for name in names}
    for parameters in parameter_rows:
        for name, parameter in zip(names, parameters, strict=True):
            values[name].append(_raw_value(parameter))
    return values


def _source_category(source_experiment: object, code: str) -> object | None:
    """Return a live experiment category matching ``code``."""
    for category in getattr(source_experiment, 'categories', ()):
        if _source_category_code(category) == code:
            return category
    return None


def _source_category_code(category: object) -> str | None:
    """Return a live category code."""
    identity = getattr(category, '_identity', None)
    category_code = getattr(identity, 'category_code', None)
    if category_code is not None:
        return category_code
    item_type = getattr(category, '_item_type', None)
    return getattr(item_type, '_category_code', None)


def _category_parameters(category: object, item: object) -> list[object]:
    """Return loop parameters for one live category row."""
    loop_parameters = getattr(category, '_cif_loop_parameters', None)
    if callable(loop_parameters):
        return list(loop_parameters(item))
    return list(getattr(item, 'parameters', ()))


def _raw_value(value: object) -> object:
    """Return a descriptor's raw value for CSV output."""
    return getattr(value, 'value', value)


def _context_category_values(
    experiment: dict[str, object],
    code: str,
) -> dict[str, list[object]]:
    """Return category values from a prepared report context."""
    for category in experiment.get('categories') or ():
        if not isinstance(category, dict) or category.get('code') != code:
            continue
        return _context_loop_values(category)
    return {}


def _context_loop_values(category: dict[str, object]) -> dict[str, list[object]]:
    """Return loop values from a prepared category context."""
    columns = category.get('columns') or []
    rows = category.get('rows') or []
    names = [str(column.get('name')) for column in columns if isinstance(column, dict)]
    values = {name: [] for name in names}
    for row in rows:
        if not isinstance(row, dict):
            continue
        cells = row.get('cells') or []
        for name, cell in zip(names, cells, strict=True):
            values[name].append(cell.get('value') if isinstance(cell, dict) else '')
    return values


def _is_csv_empty(value: object) -> bool:
    """Return whether a value should be treated as empty in CSV data."""
    return value is None or (isinstance(value, str) and not value)


def _write_csv(
    path: pathlib.Path,
    expt_id: str,
    columns: list[tuple[str, list[object]]],
) -> None:
    """Write a CSV file after validating column lengths."""
    _validate_fit_csv_columns(expt_id, columns)
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerow([name for name, _values in columns])
        writer.writerows(zip(*(values for _name, values in columns), strict=True))


def _validate_fit_csv_columns(
    expt_id: str,
    columns: list[tuple[str, list[object]]],
) -> None:
    """Raise if fit-data CSV columns have inconsistent lengths."""
    reference_name = columns[0][0]
    expected = len(columns[0][1])
    for name, values in columns[1:]:
        if len(values) == expected:
            continue
        msg = (
            f"Cannot write report CSV for experiment '{expt_id}': "
            f"column '{reference_name}' has length {expected}, but column "
            f"'{name}' has length {len(values)}."
        )
        raise ValueError(msg)


def _tex_number(value: object, digits: int = 6) -> str:
    """Format a number for TeX output."""
    if isinstance(value, bool):
        return _tex_escape(value)
    if isinstance(value, (float, int)):
        return f'{value:.{digits}g}'
    return _tex_escape(value)


def _tex_markup(value: object) -> str:
    """Escape plain text while preserving explicit TeX snippets."""
    if value is None:
        return ''
    text = str(value)
    if '\\' in text or '$' in text:
        return text
    return _tex_escape(text)


def _tex_unit(value: object) -> str:
    """Return TeX-safe unit text for table labels."""
    if value is None:
        return ''
    text = str(value)
    if not text:
        return ''
    if '\\' in text or '$' in text:
        return f'${_tex_unit_math(text.replace("$", ""))}$'
    return _tex_escape(text)


def _tex_unit_math(value: str) -> str:
    """Return unit TeX normalized for math-mode rendering."""
    placeholder = '__EASYDIFFRACTION_ANGSTROM__'
    text = _tex_degree_unit_math(value)
    text = text.replace(r'\mathrm{\AA}', placeholder)
    text = text.replace(r'\AA', r'\mathring{\mathrm{A}}')
    return text.replace(placeholder, r'\mathring{\mathrm{A}}')


def _tex_degree_unit_math(value: str) -> str:
    """Return TeX unit markup with degree symbols named as deg."""
    text = value
    markers = (r'^\circ{}^2', r'^\circ{}^{2}', r'^\circ^2', r'^\circ^{2}')
    for marker in markers:
        text = text.replace(marker, r'\mathrm{deg}^2')
    return text.replace(r'^\circ{}', r'\mathrm{deg}').replace(
        r'^\circ',
        r'\mathrm{deg}',
    )


def _tex_axis_label(value: object) -> str:
    """Return a TeX-safe axis label from Plotly display text."""
    if value is None:
        return ''
    text = str(value)
    text = text.replace('degree', 'deg')
    text = text.replace('⁻¹', '$^{-1}$')
    text = text.replace('²', '$^2$')
    text = text.replace('θ', r'$\theta$')
    text = text.replace('λ', r'$\lambda$')
    text = text.replace('μ', r'$\mu$')
    text = text.replace('Å', r'\AA{}')
    return _tex_markup(text)


def _tex_escape(value: object) -> str:
    """Escape user-provided text for TeX output."""
    if value is None:
        return ''
    if isinstance(value, (list, tuple, set)):
        text = ', '.join(str(item) for item in value if item is not None)
    else:
        text = str(value)
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    escaped = ''.join(_TEX_SPECIAL_CHARS.get(char, char) for char in text)
    return escaped.replace('\n\n', r'\par ').replace('\n', ' ')
