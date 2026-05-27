# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Render project reports as LaTeX source bundles."""

from __future__ import annotations

import pathlib
from importlib.resources import files

from jinja2 import Environment
from jinja2 import PackageLoader

_TEMPLATE_NAME = 'tex/report.tex.j2'
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
    template_context['tex'] = {'fit_figure_paths': {}}
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

    tex_dir.mkdir(parents=True, exist_ok=True)
    styles_dir.mkdir(parents=True, exist_ok=True)

    template_context = dict(context)
    template_context['tex'] = {'fit_figure_paths': {}}
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
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    environment.filters['tex'] = _tex_escape
    environment.filters['tex_number'] = _tex_number
    return environment


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
