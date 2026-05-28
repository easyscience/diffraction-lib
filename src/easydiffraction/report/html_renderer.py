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
    template_context['figures'] = _figure_html_context(
        context.get('figures'),
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


def _figure_html_context(
    figures: object,
    *,
    offline: bool,
) -> dict[str, object]:
    """Return HTML snippets for figure slots."""
    if not isinstance(figures, dict):
        return {'fit_per_experiment': {}}

    return {
        'fit_per_experiment': _figure_map_html(
            figures.get('fit_per_experiment'),
            offline=offline,
        ),
    }


def _figure_map_html(figures: object, *, offline: bool) -> dict[str, str]:
    """Convert one figure mapping into HTML snippets."""
    if not isinstance(figures, dict):
        return {}

    include_plotlyjs: bool | str = True if offline else 'cdn'
    rendered: dict[str, str] = {}
    for key, figure in figures.items():
        rendered[str(key)] = _figure_html(figure, include_plotlyjs=include_plotlyjs)
        include_plotlyjs = False
    return rendered


def _figure_html(figure: object, *, include_plotlyjs: bool | str) -> str:
    """Return an HTML snippet for one figure-like object."""
    to_html = getattr(figure, 'to_html', None)
    if callable(to_html):
        return to_html(full_html=False, include_plotlyjs=include_plotlyjs)
    return str(figure)
