---
icon: material/console
---

# :material-console: Command-Line Interface

In addition to the Python API and Jupyter Notebooks, EasyDiffraction
provides a **command-line interface (CLI)**. This is useful for basic
operations without writing Python code.

## Running the CLI

The CLI is invoked as a Python module:

```bash
python -m easydiffraction [COMMAND] [OPTIONS]
```

If you use **Pixi** and have defined the `easydiffraction` task (see
[Installation & Setup](../installation-and-setup/index.md)), you can
use:

```bash
pixi run easydiffraction [COMMAND] [OPTIONS]
```

To see all available commands and options:

```bash
python -m easydiffraction --help
```

## Available Commands

### Show Version

Display the installed EasyDiffraction version:

```bash
python -m easydiffraction --version
```

### List Tutorials

List all available tutorial notebooks:

```bash
python -m easydiffraction list-tutorials
```

### List Example Data

List all available example data files and downloadable project archives:

```bash
python -m easydiffraction list-data
```

The table includes the data ID, file name, record kind, and description.

### Download Example Data

Download a specific example data record by ID:

```bash
python -m easydiffraction download-data 3
```

For downloadable saved projects, the ZIP archive is extracted
automatically, the ZIP file is removed, and the extracted project path
is reported:

```bash
python -m easydiffraction download-data 30
```

This makes it possible to go straight from download to a project-first
CLI command such as:

```bash
python -m easydiffraction EXTRACTED_PROJECT_DIR display
```

Use the extracted path printed by `download-data`.

### Download Tutorials

Download a specific tutorial by ID:

```bash
python -m easydiffraction download-tutorial 1
```

Download all available tutorials:

```bash
python -m easydiffraction download-all-tutorials
```

Both commands accept `--destination` (`-d`) to specify the output
directory (default: `tutorials/`) and `--overwrite` (`-o`) to replace
existing files.

`download-data` also accepts `--destination` (`-d`) and `--overwrite`
(`-o`). For project archives, `--overwrite` replaces the extracted
project directory before downloading and unpacking a fresh copy.

### Fit a Project

Load a saved project and run structural refinement:

```bash
python -m easydiffraction PROJECT_DIR fit
```

`PROJECT_DIR` is the path to a project directory previously created by
`project.save_as()`. It must contain a `project.edifa` file along
with the `structures/`, `experiments/`, and `analysis/` subdirectories.

After fitting, the command displays the fit results and a project
summary. By default, updated parameter values are **saved back** to the
project directory.

If `project.edifa` enables any `_report.*` output flags, the same
save also writes those reports. For example, `_report.html true` writes
the HTML report after the fit, and `_report.tex true` plus
`_report.pdf true` writes the TeX bundle and PDF when a TeX engine is
available.

Use the `--dry` flag to run the fit **without overwriting** the project
files:

```bash
python -m easydiffraction PROJECT_DIR fit --dry
```

EasyDiffraction also accepts the legacy subcommand-first form
`python -m easydiffraction fit PROJECT_DIR`, but the project-first form
is recommended because it makes it easy to rerun the same command and
swap only the action.

### Display a Project

Load a saved project and show the outputs that match its current fit
state and rendering backend:

```bash
python -m easydiffraction PROJECT_DIR display
```

For typical non-sequential projects this includes the latest fit
results, parameter correlations, default pattern views, and when the
saved state is Bayesian also posterior distributions and predictive
checks. Plotly-only views such as posterior pair plots are shown only
when the active chart engine is Plotly.

### Undo the Last Fit

Roll back the most recent fit to the parameter values and uncertainties
captured just before it started:

```bash
python -m easydiffraction PROJECT_DIR undo
```

The command restores each refined parameter to its saved pre-fit
`start_value` / `start_uncertainty`, clears `analysis.fit_results`,
truncates `analysis/results.h5` (the Bayesian sidecar), and **saves the
rolled-back state back** to the project directory by default.

Use the `--dry` flag to preview the rollback **without overwriting** any
file:

```bash
python -m easydiffraction PROJECT_DIR undo --dry
```

Undo is single-level: only the most recently committed fit is
addressable. Calling `undo` a second time, or running it on a project
that has never been fit, prints
`No fit to undo for '<project>'. Project state is unchanged.` and exits
cleanly (status 0). Fit bounds, aliases, constraints, the minimizer
choice, the fit mode, and joint-fit weights are **not** reverted by undo
— only fit output is rolled back.
