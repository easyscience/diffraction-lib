# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Typer command-line interface for the EasyDiffraction library."""

from __future__ import annotations

import sys

# Ensure UTF-8 output on all platforms (e.g. Windows with cp1252)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import typer

import easydiffraction as edi

app = typer.Typer(add_completion=False)

_MIN_PROJECT_FIRST_ARG_COUNT = 2
_PROJECT_COMMAND_NAMES = frozenset({'fit', 'display', 'undo'})
_GLOBAL_COMMAND_NAMES = frozenset({
    'list-data',
    'download-data',
    'list-tutorials',
    'download-tutorial',
    'download-all-tutorials',
    *_PROJECT_COMMAND_NAMES,
})


def _normalized_cli_args(args: list[str]) -> list[str]:
    """Return CLI args rewritten to support project-first commands."""
    if len(args) < _MIN_PROJECT_FIRST_ARG_COUNT:
        return args

    first_arg = args[0]
    if first_arg.startswith('-') or first_arg in _GLOBAL_COMMAND_NAMES:
        return args

    if args[1] not in _PROJECT_COMMAND_NAMES:
        return args

    return [args[1], first_arg, *args[2:]]


def _load_project(project_dir: str) -> object:
    """Load one saved project directory."""
    return edi.Project.load(project_dir)


def _display_project_patterns(project: object) -> None:
    """Render default pattern views for all experiments."""
    for experiment in project.experiments:
        project.display.pattern(expt_name=experiment.name)


def _project_fit_mode(project: object) -> str | None:
    """Return the resolved fitting mode type for one project."""
    fitting_mode = getattr(project.analysis, 'fitting_mode', None)
    return getattr(fitting_mode, 'type', None)


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
        if project.rendering_plot.plotter.engine == 'plotly':
            project.display.posterior.pairs()
        project.display.posterior.distribution()
        for experiment in project.experiments:
            project.display.posterior.predictive(expt_name=experiment.name)

    _display_project_patterns(project)


def _project_name(project: object, fallback: str) -> str:
    """Return a display name for one project."""
    name = getattr(project, 'name', None)
    return str(name) if name else fallback


def _display_undo_summary(
    *,
    project: object,
    project_dir: str,
    dry: bool,
) -> None:
    """Run undo and render its command-line summary."""
    project_name = _project_name(project, project_dir)
    outcome = project.analysis.undo_fit()

    if outcome.was_no_op:
        typer.echo(f"No fit to undo for '{project_name}'. Project state is unchanged.")
        return

    restored_count = len(outcome.restored_parameter_names)
    if dry:
        typer.echo(f"Would undo last fit for '{project_name}' (dry run, no files written):")
        typer.echo(f'  - {restored_count} parameters would be restored to pre-fit values')
        if outcome.cleared_fit_result:
            typer.echo('  - analysis.fit_results would be cleared')
        if outcome.cleared_sidecar:
            typer.echo('  - analysis/mcmc.h5 (Bayesian sidecar) would be cleared')
        return

    typer.echo(f"Undoing last fit for '{project_name}'...")
    typer.echo(f'✅ Restored {restored_count} parameters to their pre-fit values.')
    if outcome.cleared_fit_result:
        typer.echo('✅ Cleared analysis.fit_results.')
    if outcome.cleared_sidecar:
        typer.echo('✅ Cleared analysis/mcmc.h5 (Bayesian sidecar).')
    project.save()
    typer.echo(f'✅ Saved project to {project_dir}.')


def run_cli(args: list[str] | None = None) -> None:
    """
    Run the EasyDiffraction CLI with project-first argument support.
    """
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
        edi.show_version()
        raise typer.Exit(code=0)
    # If no subcommand and no option provided, show help and exit 0.
    if ctx.invoked_subcommand is None:
        typer.echo(app.get_help(ctx))
        raise typer.Exit(code=0)
    # Otherwise, let the chosen subcommand execute.


@app.command('list-data')
def list_data() -> None:
    """List available example data and project archives."""
    edi.list_data()


@app.command('list-tutorials')
def list_tutorials() -> None:
    """List available tutorial notebooks."""
    edi.list_tutorials()


@app.command('download-data')
def download_data(
    name: str = typer.Argument(
        ...,
        help="Dataset name (e.g. 'meas-lbco-hrpt') or a list-data row number.",
    ),
    destination: str = typer.Option(
        'data',
        '--destination',
        '-d',
        help='Directory to save the data or extracted project into.',
    ),
    overwrite: bool = typer.Option(  # noqa: FBT001
        False,  # noqa: FBT003
        '--overwrite',
        '-o',
        help='Overwrite an existing file or extracted project if present.',
    ),
) -> None:
    """Download one dataset by its name."""
    edi.download_data(name, destination=destination, overwrite=overwrite)


def _selected_tutorial_formats(*, ipynb: bool, py: bool) -> list[str]:
    """
    Return the formats to download; default to notebook if none set.
    """
    formats = []
    if ipynb:
        formats.append('ipynb')
    if py:
        formats.append('py')
    return formats or ['ipynb']


@app.command('download-tutorial')
def download_tutorial(
    name: str = typer.Argument(
        ...,
        help="Tutorial name (e.g. 'refine-lbco-hrpt-from-cif') or a list-tutorials row number.",
    ),
    destination: str = typer.Option(
        'tutorials',
        '--destination',
        '-d',
        help='Directory to save the tutorial into.',
    ),
    ipynb: bool = typer.Option(  # noqa: FBT001
        False,  # noqa: FBT003
        '--ipynb',
        help='Download the Jupyter notebook (.ipynb). Default when no format flag is given.',
    ),
    py: bool = typer.Option(  # noqa: FBT001
        False,  # noqa: FBT003
        '--py',
        help='Download the plain-Python script (.py). Combine with --ipynb to get both.',
    ),
    overwrite: bool = typer.Option(  # noqa: FBT001
        False,  # noqa: FBT003
        '--overwrite',
        '-o',
        help='Overwrite existing file if present.',
    ),
) -> None:
    """Download a tutorial by its name as a notebook and/or script."""
    for file_format in _selected_tutorial_formats(ipynb=ipynb, py=py):
        edi.download_tutorial(
            name,
            destination=destination,
            file_format=file_format,
            overwrite=overwrite,
        )


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
    edi.download_all_tutorials(destination=destination, overwrite=overwrite)


@app.command('display')
def display(
    project_dir: str = typer.Argument(
        ...,
        help='Path to the project directory (must contain project.edi).',
    ),
) -> None:
    """Display the typical outputs for a saved project state."""
    project = _load_project(project_dir)
    _display_project_outputs(project)


@app.command('fit')
def fit(
    project_dir: str = typer.Argument(
        ...,
        help='Path to the project directory (must contain project.edi).',
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
        project.metadata._path = None
    project.analysis.fit()
    if not dry:
        project.save()
    _display_fit_outputs(project)


@app.command('undo')
def undo(
    project_dir: str = typer.Argument(
        ...,
        help='Path to the project directory (must contain project.edi).',
    ),
    dry: bool = typer.Option(  # noqa: FBT001
        False,  # noqa: FBT003
        '--dry',
        help='Undo fitting without saving results back to the project directory.',
    ),
) -> None:
    """Undo the last fit: easydiffraction PROJECT_DIR undo [--dry]."""
    project = _load_project(project_dir)
    _display_undo_summary(project=project, project_dir=project_dir, dry=dry)


if __name__ == '__main__':
    run_cli()
