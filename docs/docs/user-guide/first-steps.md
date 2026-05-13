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
[here](../tutorials/ed-3.ipynb).

### Importing specific parts

Alternatively, you can import specific classes or methods from the
package. For example, you can import the `Project`, `Structure`,
`Experiment` classes and `download_from_repository` method like this:

```python
from easydiffraction import Project
from easydiffraction import Structure
from easydiffraction import Experiment
from easydiffraction import download_from_repository
```

This enables you to use these classes and methods directly without the
package prefix. This is especially useful when you're using only a few
components and want to keep your code clean and concise. In this case,
you can create a project instance like this:

```python
project = Project()
```

A complete tutorial using the `from` syntax can be found
[here](../tutorials/ed-4.ipynb).

## Utility functions

EasyDiffraction also provides several utility functions that can
simplify your workflow. One of them is the `download_from_repository`
function, which allows you to download data files from our remote
repository, making it easy to access and use them while experimenting
with EasyDiffraction.

For example, you can download a data file like this:

```python
import easydiffraction as ed

ed.download_from_repository(
    'hrpt_lbco.xye',
    branch='docs',
    destination='data',
)
```

This command will download the `hrpt_lbco.xye` file from the `docs`
branch of the EasyDiffraction repository and save it in the `data`
directory of your current working directory. This is particularly useful
for quickly accessing example datasets without having to manually
download them.

## Help methods

EasyDiffraction provides several helper methods to display supported
engines for calculation, minimization, and plotting. These methods can
be called on the `Project` instance to display the available options for
different categories.

### Supported calculators

The calculator is automatically selected based on the experiment type.
You can use the experiment `calculation` category to see which
calculation engines are compatible:

```python
project.experiments['hrpt'].calculation.show_calculator_types()
```

This will display a list of supported calculators along with their
descriptions, allowing you to choose the one that best fits your needs.

An example of the output for a Bragg diffraction experiment:

| Calculator | Description                                      |
| ---------- | ------------------------------------------------ |
| cryspy     | CrysPy library for crystallographic calculations |

### Supported minimizers

You can also check the available minimizers using the
`show_minimizer_types()` method:

```python
project.analysis.fit.show_minimizer_types()
```

### Available parameters

EasyDiffraction provides several methods for showing the available
parameters grouped in different categories. For example, you can use:

- `project.display.parameters.all()` – to display all available
  parameters for the analysis step.
- `project.display.parameters.fittable()` – to display only the
  parameters that can be fitted during the analysis.
- `project.display.parameters.free()` – to display the parameters
  that are currently free to be adjusted during the fitting process.

Finally, you can use the
`project.display.parameters.access()` method to get a
brief overview of how to access and modify parameters in the analysis
step, along with their unique identifiers in the CIF format. This can be
particularly useful for users who are new to the EasyDiffraction API or
those who want to quickly understand how to work with parameters in
their projects.

An example of the output for the
`project.display.parameters.access()` method is:

|     | Code variable                                       | Unique ID for CIF          |
| --- | --------------------------------------------------- | -------------------------- |
| 1   | project.structures['lbco'].atom_site['La'].adp_type | lbco.atom_site.La.ADP_type |
| 2   | project.structures['lbco'].atom_site['La'].adp_iso  | lbco.atom_site.La.adp_iso  |
| 3   | project.structures['lbco'].atom_site['La'].fract_x  | lbco.atom_site.La.fract_x  |
| 4   | project.structures['lbco'].atom_site['La'].fract_y  | lbco.atom_site.La.fract_y  |
| ... | ...                                                 | ...                        |
| 59  | project.experiments['hrpt'].peak.broad_gauss_u      | hrpt.peak.broad_gauss_u    |
| 60  | project.experiments['hrpt'].peak.broad_gauss_v      | hrpt.peak.broad_gauss_v    |
| 61  | project.experiments['hrpt'].peak.broad_gauss_w      | hrpt.peak.broad_gauss_w    |

### Supported plotters

To see the available plotters, you can use the `display` category on the
`Project` instance:

```python
project.rendering.show_chart_engines()
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
