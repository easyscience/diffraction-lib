# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Render project reports as HTML."""

from __future__ import annotations

import pathlib
import shutil
from importlib.resources import as_file
from importlib.resources import files

import numpy as np
from jinja2 import Environment
from jinja2 import PackageLoader

from easydiffraction.display.plotters.base import PowderMeasVsCalcSpec
from easydiffraction.display.plotters.plotly import PlotlyPlotter
from easydiffraction.display.plotting import DEFAULT_BRAGG_ROW
from easydiffraction.display.plotting import DEFAULT_RESID_HEIGHT
from easydiffraction.report.style import report_style_context

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
    template_context['report_style'] = report_style_context()
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
    report_style = report_style_context()
    rendered: dict[str, str] = {}
    for experiment in _experiment_contexts(context):
        fit_data = experiment.get('fit_data')
        if fit_data is None:
            continue
        experiment_id = str(experiment.get('id') or 'experiment')
        figure = _fit_data_figure(experiment_id, fit_data, experiment)
        rendered[experiment_id] = _figure_html(
            figure,
            include_plotlyjs=include_plotlyjs,
            report_style=report_style,
        )
        include_plotlyjs = False
    return rendered


def _fit_data_figure(
    experiment_id: str,
    fit_data: dict[str, object],
    experiment: dict[str, object],
) -> object:
    """Build a Plotly fit figure from one fit-data payload."""
    x_data = fit_data['x']
    series = fit_data['series']
    x_values = _value_list(x_data['values'])
    y_meas = _value_list(series['meas']['values'])
    y_calc = _value_list(series['calc']['values'])
    y_diff = _value_list(series['diff']['values'])
    _validate_same_length(experiment_id, 'meas', x_values, y_meas)
    _validate_same_length(experiment_id, 'calc', x_values, y_calc)
    _validate_same_length(experiment_id, 'diff', x_values, y_diff)

    y_meas_su = None
    y_meas_su_data = series['meas']['su']
    if y_meas_su_data is not None:
        y_meas_su = _value_list(y_meas_su_data)
        _validate_same_length(experiment_id, 'meas_su', x_values, y_meas_su)

    y_bkg = None
    bkg = series['bkg']
    if bkg is not None:
        y_bkg = _value_list(bkg['values'])
        _validate_same_length(experiment_id, 'bkg', x_values, y_bkg)

    if x_data.get('name') == 'intensity_calc':
        return _single_crystal_fit_data_figure(
            experiment_id=experiment_id,
            fit_data=fit_data,
            x_values=x_values,
            y_meas=y_meas,
            y_meas_su=y_meas_su,
        )

    return PlotlyPlotter().build_powder_meas_vs_calc_figure(
        plot_spec=PowderMeasVsCalcSpec(
            x=np.asarray(x_values, dtype=float),
            y_meas=np.asarray(y_meas, dtype=float),
            y_calc=np.asarray(y_calc, dtype=float),
            y_resid=np.asarray(y_diff, dtype=float),
            bragg_tick_sets=tuple(fit_data.get('bragg_tick_sets') or ()),
            axes_labels=list(fit_data.get('axes_labels') or [_axis_title(x_data), 'Intensity']),
            title=_fit_figure_title(experiment_id, experiment),
            residual_height_fraction=DEFAULT_RESID_HEIGHT,
            bragg_peaks_height_fraction=DEFAULT_BRAGG_ROW,
            y_bkg=np.asarray(y_bkg, dtype=float) if y_bkg is not None else None,
            y_meas_su=(
                np.asarray(y_meas_su, dtype=float)
                if y_meas_su is not None
                else None
            ),
        )
    )


def _single_crystal_fit_data_figure(
    *,
    experiment_id: str,
    fit_data: dict[str, object],
    x_values: list[object],
    y_meas: list[object],
    y_meas_su: list[object] | None,
) -> object:
    """Build a single-crystal Plotly report figure."""
    y_meas_array = np.asarray(y_meas, dtype=float)
    if y_meas_su is None:
        y_meas_su_array = np.zeros_like(y_meas_array)
    else:
        y_meas_su_array = np.asarray(y_meas_su, dtype=float)

    return PlotlyPlotter().build_single_crystal_figure(
        x_calc=np.asarray(x_values, dtype=float),
        y_meas=y_meas_array,
        y_meas_su=y_meas_su_array,
        axes_labels=list(fit_data.get('axes_labels') or ['I²calc', 'I²meas']),
        title=f"Measured vs Calculated data for experiment 🔬 '{experiment_id}'",
    )


def _fit_figure_title(experiment_id: str, experiment: dict[str, object]) -> str:
    """Return a report title matching the direct plotting API."""
    experiment_type = experiment.get('type')
    if _is_powder_bragg_context(experiment_type):
        return f"Measured vs Calculated data for experiment 🔬 '{experiment_id}'"
    return f'Measured vs calculated: {experiment_id}'


def _is_powder_bragg_context(experiment_type: object) -> bool:
    if not isinstance(experiment_type, dict):
        return False
    return (
        experiment_type.get('sample_form') == 'powder'
        and experiment_type.get('scattering_type') == 'bragg'
    )


def _figure_html(
    figure: object,
    *,
    include_plotlyjs: bool | str,
    report_style: dict[str, object],
) -> str:
    """Return an HTML snippet for one figure-like object."""
    to_html = getattr(figure, 'to_html', None)
    if callable(to_html):
        return PlotlyPlotter.serialize_html(
            figure,
            include_plotlyjs=include_plotlyjs,
            force_template='plotly_white',
            axis_frame_color=str(report_style['axis_hex']),
            grid_color=str(report_style['chart_grid_hex']),
        )
    return str(figure)


def _axis_title(x_data: dict[str, object]) -> str:
    """Return a display axis title for fit figures."""
    units = x_data.get('display_units')
    if units:
        return f"{x_data.get('display_name')} ({units})"
    return str(x_data.get('display_name') or '')


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
