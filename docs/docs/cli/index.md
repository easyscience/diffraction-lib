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

### Fit a Project

Load a saved project and run structural refinement:

```bash
python -m easydiffraction fit PROJECT_DIR
```

`PROJECT_DIR` is the path to a project directory previously created by
`project.save_as()`. It must contain a `project.cif` file along with the
`structures/`, `experiments/`, and `analysis/` subdirectories.

After fitting, the command displays the fit results and a project
summary. By default, updated parameter values are **saved back** to the
project directory.

Use the `--dry` flag to run the fit **without overwriting** the project
files:

```bash
python -m easydiffraction fit PROJECT_DIR --dry
```
