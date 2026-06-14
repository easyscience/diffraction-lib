# First Steps

This section introduces the basic usage of the EasyDiffraction Python
API. You'll learn how to import the package, use core classes and
utility functions, and access built-in helper methods to streamline
diffraction data analysis workflows.

## Importing EasyDiffraction

### Importing the entire package

To start using EasyDiffraction, first import the package in your Python
script or Jupyter Notebook. This can be done with the following command:

```python
import easydiffraction
```

Alternatively, you can import it with an alias to avoid naming conflicts
and for convenience:

```python
import easydiffraction as ed
```

The latter syntax allows you to access all the modules and classes
within the package using the `ed` prefix. For example, you can create a
project instance like this:

```python
project = ed.Project()
```

A complete tutorial using the `import` syntax can be found
[here](../tutorials/refine-lbco-hrpt-report.ipynb).

### Importing specific parts

Alternatively, you can import specific classes or methods from the
package. For example, you can import the `Project`, `StructureFactory`,
`ExperimentFactory` classes and `download_data` method like this:

```python
from easydiffraction import Project
from easydiffraction import StructureFactory
from easydiffraction import ExperimentFactory
from easydiffraction import download_data
```

This enables you to use these classes and methods directly without the
package prefix. This is especially useful when you're using only a few
components and want to keep your code clean and concise. In this case,
you can create a project instance like this:

```python
project = Project()
```

A complete tutorial using the `from` syntax can be found
[here](../tutorials/refine-pbso4-joint.ipynb).

## Utility functions

EasyDiffraction also provides several utility functions that can
simplify your workflow. One of them is the `download_data` function,
which allows you to download example datasets by their slug from our
remote repository, making it easy to access and use them while
experimenting with EasyDiffraction.

You can list the available datasets and their slugs with `list_data()`,
then download one like this:

```python
import easydiffraction as ed

ed.list_data()

data_path = ed.download_data('meas-lbco-hrpt', destination='data')
```

This command downloads the `measured/lbco-hrpt` dataset and saves it in
the `data` directory of your current working directory, returning the
full path to the downloaded file. This is particularly useful for
quickly accessing example datasets without having to manually download
them.

## Help methods

EasyDiffraction provides several helper methods to display supported
engines for calculation, minimization, and plotting. These methods can
be called on the `Project` instance to display the available options for
different categories.

### Supported calculators

The calculator is automatically selected based on the experiment type.
Use the experiment `calculator` category to see which calculation
engines are compatible:

```python
project.experiments['hrpt'].calculator.show_supported()
```

This will display a list of supported calculators along with their
descriptions, allowing you to choose the one that best fits your needs.

An example of the output for a Bragg diffraction experiment:

| Calculator | Description                                      |
| ---------- | ------------------------------------------------ |
| cryspy     | CrysPy library for crystallographic calculations |

### Supported minimizers

You can also check the available minimizers from the active minimizer
category:

```python
project.analysis.minimizer.show_supported()
```

### Available parameters

EasyDiffraction provides several methods for showing the available
parameters grouped in different categories. For example, you can use:

- `project.display.parameters.all()` – to display all available
  parameters for the analysis step.
- `project.display.parameters.fittable()` – to display only the
  parameters that can be fitted during the analysis.
- `project.display.parameters.free()` – to display the parameters that
  are currently free to be adjusted during the fitting process.

Finally, you can use the `project.display.parameters.access()` method to
get a brief overview of how to access and modify parameters in the
analysis step, along with their unique identifiers in the CIF format.
This can be particularly useful for users who are new to the
EasyDiffraction API or those who want to quickly understand how to work
with parameters in their projects.

An example of the output for the `project.display.parameters.access()`
method is:

|     | Code variable                                        | Unique ID for CIF          |
| --- | ---------------------------------------------------- | -------------------------- |
| 1   | project.structures['lbco'].atom_sites['La'].adp_type | lbco.atom_site.La.ADP_type |
| 2   | project.structures['lbco'].atom_sites['La'].adp_iso  | lbco.atom_site.La.adp_iso  |
| 3   | project.structures['lbco'].atom_sites['La'].fract_x  | lbco.atom_site.La.fract_x  |
| 4   | project.structures['lbco'].atom_sites['La'].fract_y  | lbco.atom_site.La.fract_y  |
| ... | ...                                                  | ...                        |
| 59  | project.experiments['hrpt'].peak.broad_gauss_u       | hrpt.peak.broad_gauss_u    |
| 60  | project.experiments['hrpt'].peak.broad_gauss_v       | hrpt.peak.broad_gauss_v    |
| 61  | project.experiments['hrpt'].peak.broad_gauss_w       | hrpt.peak.broad_gauss_w    |

### Supported plotters

To see the available plotters, use the project rendering categories:

```python
project.rendering_plot.show_supported()
project.rendering_table.show_supported()
```

An example of the output is:

| Engine       | Description                                |
| ------------ | ------------------------------------------ |
| asciichartpy | Console ASCII line charts                  |
| plotly       | Interactive browser-based graphing library |

## Data analysis workflow

Once the EasyDiffraction package is imported, you can proceed with the
**data analysis**. This step can be split into several sub-steps, such
as creating a project, defining structures, adding experimental data,
etc.

EasyDiffraction provides a **Python API** that allows you to perform
these steps programmatically in a certain linear order. This is
especially useful for users who prefer to work in a script or Jupyter
Notebook environment. The API is designed to be intuitive and easy to
use, allowing you to focus on the analysis rather than low-level
implementation details.

Because this workflow is an important part of the EasyDiffraction
package, it is described in detail in the separate
[Analysis Workflow](analysis-workflow/index.md) section of the
documentation.
