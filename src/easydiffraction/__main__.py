# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import sys

# Ensure UTF-8 output on all platforms (e.g. Windows with cp1252)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import typer

import easydiffraction as ed

app = typer.Typer(add_completion=False)

_PROJECT_COMMAND_NAMES = frozenset({'fit', 'display', 'undo'})
_GLOBAL_COMMAND_NAMES = frozenset({
    'list-tutorials',
    'download-tutorial',
    'download-all-tutorials',
    *_PROJECT_COMMAND_NAMES,
})


def _normalized_cli_args(args: list[str]) -> list[str]:
    """Return CLI args rewritten to support project-first commands."""
    if len(args) < 2:
        return args

    first_arg = args[0]
    if first_arg.startswith('-') or first_arg in _GLOBAL_COMMAND_NAMES:
        return args

    if args[1] not in _PROJECT_COMMAND_NAMES:
        return args

    return [args[1], first_arg, *args[2:]]


def _load_project(project_dir: str) -> object:
    """Load one saved project directory."""
    return ed.Project.load(project_dir)


def _display_project_patterns(project: object) -> None:
    """Render default pattern views for all experiments."""
    for experiment in project.experiments:
        project.display.pattern(expt_name=experiment.name)


def _project_fit_mode(project: object) -> str | None:
    """Return the resolved fitting mode type for one project."""
    return getattr(project.analysis, 'fitting_mode_type', None)


def _project_result_kind(project: object) -> str | None:
    """Return the resolved fit result kind for one project."""
    result_kind = getattr(getattr(project.analysis, 'fit_result', None), 'result_kind', None)
    return getattr(result_kind, 'value', None)


def _display_fit_outputs(project: object) -> None:
    """Render the standard post-fit CLI outputs."""
    if _project_fit_mode(project) != 'sequential':
        project.display.fit.results()
        project.display.fit.correlations()
    _display_project_patterns(project)


def _display_project_outputs(project: object) -> None:
    """Render the typical displays for the loaded project state."""
    if _project_fit_mode(project) == 'sequential':
        project.display.fit.series()
        _display_project_patterns(project)
        return

    project.display.fit.results()
    project.display.fit.correlations()

    if _project_result_kind(project) == 'bayesian':
        if project.rendering.plotter.engine == 'plotly':
            project.display.posterior.pairs()
        project.display.posterior.distribution()
        for experiment in project.experiments:
            project.display.posterior.predictive(expt_name=experiment.name)

    _display_project_patterns(project)


def run_cli(args: list[str] | None = None) -> None:
    """Run the EasyDiffraction CLI with project-first argument support."""
    cli_args = list(sys.argv[1:] if args is None else args)
    app(args=_normalized_cli_args(cli_args))


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(  # noqa: FBT001
        False,  # noqa: FBT003
        '--version',
        '-V',
        help='Show easydiffraction version and exit.',
        is_eager=True,
    ),
) -> None:
    """EasyDiffraction command-line interface."""
    if version:
        ed.show_version()
        raise typer.Exit(code=0)
    # If no subcommand and no option provided, show help and exit 0.
    if ctx.invoked_subcommand is None:
        typer.echo(app.get_help(ctx))
        raise typer.Exit(code=0)
    # Otherwise, let the chosen subcommand execute.


@app.command('list-tutorials')
def list_tutorials() -> None:
    """List available tutorial notebooks."""
    ed.list_tutorials()


@app.command('download-tutorial')
def download_tutorial(
    id: int = typer.Argument(..., help='Tutorial ID to download.'),
    destination: str = typer.Option(
        'tutorials',
        '--destination',
        '-d',
        help='Directory to save the tutorial into.',
    ),
    overwrite: bool = typer.Option(  # noqa: FBT001
        False,  # noqa: FBT003
        '--overwrite',
        '-o',
        help='Overwrite existing file if present.',
    ),
) -> None:
    """Download a specific tutorial notebook by ID."""
    ed.download_tutorial(id=id, destination=destination, overwrite=overwrite)


@app.command('download-all-tutorials')
def download_all_tutorials(
    destination: str = typer.Option(
        'tutorials',
        '--destination',
        '-d',
        help='Directory to save the tutorials into.',
    ),
    overwrite: bool = typer.Option(  # noqa: FBT001
        False,  # noqa: FBT003
        '--overwrite',
        '-o',
        help='Overwrite existing files if present.',
    ),
) -> None:
    """Download all available tutorial notebooks."""
    ed.download_all_tutorials(destination=destination, overwrite=overwrite)


@app.command('fit')
def fit(
    project_dir: str = typer.Argument(
        ...,
        help='Path to the project directory (must contain project.cif).',
    ),
    dry: bool = typer.Option(  # noqa: FBT001
        False,  # noqa: FBT003
        '--dry',
        help='Run fitting without saving results back to the project directory.',
    ),
) -> None:
    """Fit a saved project: easydiffraction PROJECT_DIR fit [--dry]."""
    project = _load_project(project_dir)
    if dry:
        project.info._path = None
    project.analysis.fit()
    _display_fit_outputs(project)


@app.command('display')
def display(
    project_dir: str = typer.Argument(
        ...,
        help='Path to the project directory (must contain project.cif).',
    ),
) -> None:
    """Display the typical outputs for a saved project state."""
    project = _load_project(project_dir)
    _display_project_outputs(project)


@app.command('undo')
def undo(
    project_dir: str = typer.Argument(
        ...,
        help='Path to the project directory (must contain project.cif).',
    ),
) -> None:
    """Undo the last fit for a saved project when fit-history support exists."""
    _load_project(project_dir)
    typer.echo('Undo is not implemented yet. See undo-fit.md ADR.')
    raise typer.Exit(code=1)


if __name__ == '__main__':
    run_cli()
