# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Render project reports as LaTeX source bundles."""

from __future__ import annotations

import csv
import pathlib
import shutil
from importlib.resources import files

from jinja2 import Environment
from jinja2 import PackageLoader
from jinja2 import select_autoescape

from easydiffraction.report.fit_plot import fit_bragg_tick_styles
from easydiffraction.report.fit_plot import fit_plot_axis_styles
from easydiffraction.report.fit_plot import fit_plot_geometry
from easydiffraction.report.fit_plot import fit_plot_ranges
from easydiffraction.report.fit_plot import fit_plot_styles

_TEMPLATE_NAME = 'tex/report.tex.j2'
_FIGURE_TEMPLATE_NAME = 'tex/figure.tex.j2'
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
    template_context['tex'] = _tex_context(
        context,
        fit_csv_paths=_fit_csv_paths(context),
        fit_figure_paths=_fit_figure_paths(context),
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
    styles_dir = tex_dir / 'styles'

    _prepare_tex_bundle(tex_dir)
    styles_dir.mkdir(parents=True, exist_ok=True)

    template_context = dict(context)
    fit_asset_paths = _write_fit_assets(context, tex_dir)
    template_context['tex'] = _tex_context(
        context,
        fit_csv_paths=fit_asset_paths['csv'],
        fit_figure_paths=fit_asset_paths['figure'],
    )
    output_path.write_text(
        _render_prepared_context(template_context),
        encoding='utf-8',
    )
    _copy_style_files(styles_dir)
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
    context: dict[str, object],
    out_dir: pathlib.Path,
) -> dict[str, dict[str, str]]:
    """Write fit-data CSV and figure TeX files."""
    csv_paths: dict[str, str] = {}
    figure_paths: dict[str, str] = {}
    for experiment in _experiment_contexts(context):
        fit_data = experiment.get('fit_data')
        if fit_data is None:
            continue
        experiment_id = str(experiment.get('id') or 'experiment')
        csv_path = _write_fit_csv(experiment_id, fit_data, out_dir)
        figure_path = _write_fit_figure_tex(
            experiment=experiment,
            csv_path=csv_path,
            out_dir=out_dir,
        )
        csv_paths[experiment_id] = f'data/{csv_path.name}'
        figure_paths[experiment_id] = f'data/{figure_path.stem}.pdf'
    return {'csv': csv_paths, 'figure': figure_paths}


def _tex_context(
    context: dict[str, object],
    *,
    fit_csv_paths: dict[str, str],
    fit_figure_paths: dict[str, str],
) -> dict[str, object]:
    """Return TeX-specific render context."""
    return {
        'fit_csv_paths': fit_csv_paths,
        'fit_figure_paths': fit_figure_paths,
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
        experiment_id = str(experiment.get('id') or 'experiment')
        ranges[experiment_id] = fit_plot_ranges(fit_data)
    return ranges


def _write_fit_csv(
    expt_id: str,
    fit_data: dict[str, object],
    out_dir: pathlib.Path,
) -> pathlib.Path:
    """Write one fit-data CSV file under ``out_dir / 'data'``."""
    data_dir = out_dir / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    csv_path = data_dir / _fit_csv_filename(expt_id)
    columns = _fit_csv_columns(expt_id, fit_data)
    _validate_fit_csv_columns(expt_id, columns)
    with csv_path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerow([name for name, _values in columns])
        writer.writerows(zip(*(values for _name, values in columns), strict=True))
    return csv_path


def _write_fit_figure_tex(
    *,
    experiment: dict[str, object],
    csv_path: pathlib.Path,
    out_dir: pathlib.Path,
) -> pathlib.Path:
    """Write one standalone pgfplots TeX figure."""
    data_dir = out_dir / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    experiment_id = str(experiment.get('id') or 'experiment')
    fit_data = experiment['fit_data']
    figure_path = data_dir / f'{_fit_asset_stem(experiment_id)}.tex'
    template_context = {
        'experiment': experiment,
        'fit_data': fit_data,
        'csv_filename': csv_path.name,
        'geometry': fit_plot_geometry(fit_data),
        'ranges': fit_plot_ranges(fit_data),
        'axis_styles': fit_plot_axis_styles(),
        'styles': fit_plot_styles(),
        'bragg_styles': fit_bragg_tick_styles(),
    }
    figure_path.write_text(
        _environment().get_template(_FIGURE_TEMPLATE_NAME).render(
            **template_context,
        ),
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
        paths[experiment_id] = f'data/{_fit_asset_stem(experiment_id)}.pdf'
    return paths


def _experiment_contexts(context: dict[str, object]) -> list[dict[str, object]]:
    """Return experiment contexts from a report context."""
    experiments = context.get('experiments')
    if not isinstance(experiments, list):
        return []
    return [
        experiment
        for experiment in experiments
        if isinstance(experiment, dict)
    ]


def _fit_csv_filename(expt_id: str) -> str:
    """Return a filesystem-safe fit-data CSV filename."""
    return f'{_fit_asset_stem(expt_id)}.csv'


def _fit_asset_stem(expt_id: str) -> str:
    """Return a filesystem-safe fit-data asset stem."""
    safe_id = ''.join(
        char if char.isascii() and (char.isalnum() or char in {'-', '_'}) else '_'
        for char in expt_id
    ).strip('_')
    if not safe_id:
        safe_id = 'experiment'
    return f'fit_{safe_id}'


def _fit_csv_columns(
    expt_id: str,
    fit_data: dict[str, object],
) -> list[tuple[str, list[object]]]:
    """Return ordered CSV columns for one fit-data payload."""
    x_data = fit_data['x']
    series = fit_data['series']
    meas = series['meas']
    calc = series['calc']
    diff = series['diff']

    columns = [
        ('x', list(x_data['values'])),
        ('meas', list(meas['values'])),
    ]
    if meas['su'] is not None:
        columns.append(('meas_su', list(meas['su'])))
    columns.extend(
        [
            ('calc', list(calc['values'])),
            ('diff', list(diff['values'])),
        ]
    )
    _validate_fit_csv_columns(expt_id, columns)
    return columns


def _validate_fit_csv_columns(
    expt_id: str,
    columns: list[tuple[str, list[object]]],
) -> None:
    """Raise if fit-data CSV columns have inconsistent lengths."""
    expected = len(columns[0][1])
    for name, values in columns[1:]:
        if len(values) == expected:
            continue
        msg = (
            f"Cannot write report CSV for experiment '{expt_id}': "
            f"column 'x' has length {expected}, but column "
            f"'{name}' has length {len(values)}."
        )
        raise ValueError(msg)


def _copy_style_files(styles_dir: pathlib.Path) -> None:
    """Copy vendored LaTeX style files into a report bundle."""
    source = files('easydiffraction.report').joinpath(
        'templates',
        'tex',
        'styles',
    )
    for resource in source.iterdir():
        if resource.is_file():
            (styles_dir / resource.name).write_bytes(resource.read_bytes())


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
