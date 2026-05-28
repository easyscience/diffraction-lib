# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Render project reports as HTML."""

from __future__ import annotations

import pathlib
import shutil
from importlib.resources import as_file
from importlib.resources import files

from jinja2 import Environment
from jinja2 import PackageLoader

_TEMPLATE_NAME = 'html/report.html.j2'
_MATHJAX_FILENAME = 'mathjax-tex-mml-chtml.js'


def html_report_path(
    project: object,
    path: str | pathlib.Path | None = None,
) -> pathlib.Path:
    """
    Return the target HTML report path for a project.

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
    return pathlib.Path(project_path) / 'reports' / f'{project_name}.html'


def render_html_report(
    context: dict[str, object],
    *,
    offline: bool = False,
) -> str:
    """
    Render a report data context as HTML.

    Parameters
    ----------
    context : dict[str, object]
        Data returned by ``Report.data_context()``.
    offline : bool, default=False
        Whether Plotly figures should embed JavaScript assets.

    Returns
    -------
    str
        Complete HTML document.
    """
    template_context = dict(context)
    template_context['html_offline'] = offline
    template_context['stylesheet'] = _stylesheet_text()
    template_context['fit_figures'] = _fit_figure_html_context(
        context,
        offline=offline,
    )
    return _environment().get_template(_TEMPLATE_NAME).render(**template_context)


def save_html_report(
    project: object,
    context: dict[str, object],
    *,
    offline: bool = False,
    path: str | pathlib.Path | None = None,
) -> pathlib.Path:
    """
    Write an HTML report and any required local assets.

    Parameters
    ----------
    project : object
        Project instance.
    context : dict[str, object]
        Data returned by ``Report.data_context()``.
    offline : bool, default=False
        Whether local HTML assets should be copied next to the report.
    path : str | pathlib.Path | None, default=None
        Explicit report path.

    Returns
    -------
    pathlib.Path
        Path of the written HTML report.
    """
    output_path = html_report_path(project, path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_html_report(context, offline=offline),
        encoding='utf-8',
    )
    if offline:
        _copy_mathjax(output_path.parent)
    return output_path


def _environment() -> Environment:
    """Return the Jinja environment for report templates."""
    return Environment(
        loader=PackageLoader('easydiffraction.report', 'templates'),
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def _stylesheet_text() -> str:
    """Return the embedded report stylesheet."""
    stylesheet = files('easydiffraction.report').joinpath(
        'templates',
        'html',
        'style.css',
    )
    return stylesheet.read_text(encoding='utf-8')


def _copy_mathjax(report_dir: pathlib.Path) -> None:
    """Copy the vendored MathJax bundle next to an HTML report."""
    vendor_dir = report_dir / 'vendor'
    vendor_dir.mkdir(parents=True, exist_ok=True)
    resource = files('easydiffraction.report').joinpath(
        'templates',
        'html',
        'vendor',
        _MATHJAX_FILENAME,
    )
    with as_file(resource) as source_path:
        shutil.copy2(source_path, vendor_dir / _MATHJAX_FILENAME)


def _fit_figure_html_context(
    context: dict[str, object],
    *,
    offline: bool,
) -> dict[str, str]:
    """Return fit figure HTML snippets by experiment id."""
    include_plotlyjs: bool | str = True if offline else 'cdn'
    rendered: dict[str, str] = {}
    for experiment in _experiment_contexts(context):
        fit_data = experiment.get('fit_data')
        if fit_data is None:
            continue
        experiment_id = str(experiment.get('id') or 'experiment')
        figure = _fit_data_figure(experiment_id, fit_data)
        rendered[experiment_id] = _figure_html(
            figure,
            include_plotlyjs=include_plotlyjs,
        )
        include_plotlyjs = False
    return rendered


def _fit_data_figure(experiment_id: str, fit_data: dict[str, object]) -> object:
    """Build a Plotly fit figure from one fit-data payload."""
    go = _plotly_go()
    x_data = fit_data['x']
    series = fit_data['series']
    x_values = _value_list(x_data['values'])
    y_meas = _value_list(series['meas']['values'])
    y_calc = _value_list(series['calc']['values'])
    y_diff = _value_list(series['diff']['values'])
    _validate_same_length(experiment_id, 'meas', x_values, y_meas)
    _validate_same_length(experiment_id, 'calc', x_values, y_calc)
    _validate_same_length(experiment_id, 'diff', x_values, y_diff)

    measured_trace = {
        'x': x_values,
        'y': y_meas,
        'mode': 'markers',
        'name': series['meas']['label'],
    }
    y_meas_su = series['meas']['su']
    if y_meas_su is not None:
        su_values = _value_list(y_meas_su)
        _validate_same_length(experiment_id, 'meas_su', x_values, su_values)
        measured_trace['error_y'] = {
            'type': 'data',
            'array': su_values,
            'visible': True,
        }

    fig = go.Figure()
    fig.add_trace(go.Scatter(**measured_trace))
    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=y_calc,
            mode='lines',
            name=series['calc']['label'],
        )
    )
    bkg = series['bkg']
    if bkg is not None:
        y_bkg = _value_list(bkg['values'])
        _validate_same_length(experiment_id, 'bkg', x_values, y_bkg)
        fig.add_trace(
            go.Scatter(
                x=x_values,
                y=y_bkg,
                mode='lines',
                name=bkg['label'],
            )
        )
    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=y_diff,
            mode='lines',
            line={'dash': 'dash'},
            name=series['diff']['label'],
        )
    )
    _configure_fit_figure(
        fig,
        experiment_id=experiment_id,
        x_title=_axis_title(x_data),
    )
    return fig


def _figure_html(figure: object, *, include_plotlyjs: bool | str) -> str:
    """Return an HTML snippet for one figure-like object."""
    to_html = getattr(figure, 'to_html', None)
    if callable(to_html):
        return to_html(full_html=False, include_plotlyjs=include_plotlyjs)
    return str(figure)


def _configure_fit_figure(
    fig: object,
    *,
    experiment_id: str,
    x_title: str,
) -> None:
    """Apply shared report-figure layout."""
    fig.update_layout(
        template='plotly_white',
        title=f'Measured vs calculated: {experiment_id}',
        xaxis_title=x_title,
        yaxis_title='Intensity',
        height=440,
        margin={'l': 64, 'r': 24, 't': 64, 'b': 56},
        legend={'orientation': 'h', 'yanchor': 'bottom', 'y': 1.02},
    )


def _axis_title(x_data: dict[str, object]) -> str:
    """Return a display axis title for fit figures."""
    units = x_data['display_units']
    if units:
        return f"{x_data['display_name']} ({units})"
    return str(x_data['display_name'])


def _validate_same_length(
    experiment_id: str,
    column_name: str,
    x_values: list[object],
    y_values: list[object],
) -> None:
    """Raise if fit-data arrays have inconsistent lengths."""
    if len(x_values) == len(y_values):
        return
    msg = (
        f"Cannot build report figure for experiment '{experiment_id}': "
        f"column 'x' has length {len(x_values)}, but column "
        f"'{column_name}' has length {len(y_values)}."
    )
    raise ValueError(msg)


def _value_list(values: object) -> list[object]:
    """Return a list suitable for Plotly and length validation."""
    return list(values)


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


def _plotly_go() -> object:
    """Return Plotly graph objects for report figures."""
    import plotly.graph_objects as go  # noqa: PLC0415

    return go
