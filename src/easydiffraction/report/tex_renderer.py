# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Render project reports as LaTeX source bundles."""

from __future__ import annotations

import pathlib
from importlib.resources import files

from jinja2 import Environment
from jinja2 import PackageLoader

_TEMPLATE_NAME = 'tex/iucr.tex.j2'
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
_BROWSER_HINT = (
    'Kaleido v1 requires Chrome/Chromium for static image export. Use '
    'an installed Chrome, Chromium, or Edge browser, or run '
    '`python -c "import kaleido; kaleido.get_chrome()"` once to '
    'download Kaleido-managed Chromium, then re-run report generation.'
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
    template_context['tex'] = {
        'fit_figure_paths': _fit_figure_paths(context),
    }
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
    figures_dir = tex_dir / 'figures'
    styles_dir = tex_dir / 'styles'

    tex_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    styles_dir.mkdir(parents=True, exist_ok=True)

    figure_paths = _write_fit_figures(context, figures_dir)
    template_context = dict(context)
    template_context['tex'] = {'fit_figure_paths': figure_paths}
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


def _fit_figure_paths(context: dict[str, object]) -> dict[str, str]:
    """Return relative TeX paths for fit figures."""
    return {
        experiment_id: f'figures/{filename}'
        for experiment_id, filename in _fit_figure_filenames(context).items()
    }


def _write_fit_figures(
    context: dict[str, object],
    figures_dir: pathlib.Path,
) -> dict[str, str]:
    """Write fit figures as vector PDFs and return relative paths."""
    figures = _fit_figures(context)
    filenames = _fit_figure_filenames(context)
    figure_paths = {}
    for experiment_id, figure in figures.items():
        filename = filenames[experiment_id]
        output_path = figures_dir / filename
        _write_plotly_figure(figure, output_path, experiment_id=experiment_id)
        figure_paths[experiment_id] = f'figures/{filename}'
    return figure_paths


def _fit_figure_filenames(context: dict[str, object]) -> dict[str, str]:
    """Return collision-safe filenames for fit figures."""
    used: set[str] = set()
    filenames = {}
    for experiment_id in _fit_figures(context):
        stem = _safe_file_stem(experiment_id)
        filename = f'fit_{stem}.pdf'
        suffix = 2
        while filename in used:
            filename = f'fit_{stem}_{suffix}.pdf'
            suffix += 1
        used.add(filename)
        filenames[experiment_id] = filename
    return filenames


def _fit_figures(context: dict[str, object]) -> dict[str, object]:
    """Return figure objects keyed by experiment id."""
    figures = context.get('figures')
    if not isinstance(figures, dict):
        return {}

    fit_figures = figures.get('fit_per_experiment')
    if not isinstance(fit_figures, dict):
        return {}

    return {
        str(experiment_id): figure
        for experiment_id, figure in fit_figures.items()
        if figure is not None
    }


def _write_plotly_figure(
    figure: object,
    output_path: pathlib.Path,
    *,
    experiment_id: str,
) -> None:
    """Write one Plotly-like figure to PDF."""
    write_image = getattr(figure, 'write_image', None)
    if not callable(write_image):
        msg = (
            f"Report figure for experiment '{experiment_id}' does not provide "
            'write_image().'
        )
        raise TypeError(msg)

    try:
        write_image(str(output_path))
    except Exception as exc:
        msg = (
            f"Could not export report figure for experiment '{experiment_id}' "
            f"to '{output_path}'. {_BROWSER_HINT}"
        )
        raise RuntimeError(msg) from exc


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


def _safe_file_stem(value: object) -> str:
    """Return a filesystem-safe stem for generated report assets."""
    text = str(value)
    safe = ''.join(
        char if char.isalnum() or char in {'-', '_', '.'} else '_' for char in text
    )
    return safe.strip('._-') or 'figure'


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
