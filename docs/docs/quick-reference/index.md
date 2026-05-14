---
icon: material/clipboard-text-outline
---

# :material-clipboard-text-outline: Quick Reference

This page is a short refresher for day-to-day EasyDiffraction work. It
collects the commands you are most likely to need when returning to a
project, preparing a quick refinement, or checking how to inspect
parameters and results.

For complete explanations, use the [User Guide](../user-guide/index.md)
and [Tutorials](../tutorials/index.md).

## Start a Session

Import the package and create or load a project:

```python
import easydiffraction as ed

project = ed.Project(name='lbco_hrpt')
```

```python
from easydiffraction import Project

project = Project.load('lbco_hrpt')
```

Check the installed version:

```python
ed.show_version()
```

## Get Example Data

Download a dataset by ID into a local directory:

```python
structure_path = ed.download_data(id=1, destination='data')
data_path = ed.download_data(id=3, destination='data')
```

For tutorial notebooks:

```python
ed.list_tutorials()
ed.download_tutorial(id=1, destination='tutorials')
ed.download_all_tutorials(destination='tutorials')
```

## Build a Project

Load a structure from CIF:

```python
project.structures.add_from_cif_path(structure_path)
project.structures.show_names()

structure = project.structures['lbco']
```

Create a structure directly:

```python
project.structures.create(name='lbco')
structure = project.structures['lbco']

structure.space_group.name_h_m = 'P m -3 m'
structure.space_group.it_coordinate_system_code = '1'
structure.cell.length_a = 3.88
```

Add an atom site:

```python
structure.atom_sites.create(
    label='O',
    type_symbol='O',
    fract_x=0,
    fract_y=0.5,
    fract_z=0.5,
    wyckoff_letter='c',
    adp_iso=0.5,
)
```

Load an experiment from measured data:

```python
project.experiments.add_from_data_path(
    name='hrpt',
    data_path=data_path,
    sample_form='powder',
    beam_mode='constant wavelength',
    radiation_probe='neutron',
)

experiment = project.experiments['hrpt']
```

Set common experiment parameters:

```python
experiment.instrument.setup_wavelength = 1.494
experiment.instrument.calib_twotheta_offset = 0.6

experiment.peak.broad_gauss_u = 0.1
experiment.peak.broad_gauss_v = -0.1
experiment.peak.broad_gauss_w = 0.1
experiment.peak.broad_lorentz_y = 0.1
```

Add background points and excluded regions:

```python
experiment.background.create(id='1', x=10, y=170)
experiment.background.create(id='2', x=30, y=170)

experiment.excluded_regions.create(id='1', start=0, end=5)
experiment.excluded_regions.create(id='2', start=165, end=180)
```

Link a structure to an experiment:

```python
experiment.linked_phases.create(id='lbco', scale=10.0)
```

## Inspect the Project

Show names, CIF text, and plotting options:

```python
project.structures.show_names()
project.experiments.show_names()

structure.show_as_cif()
experiment.show_as_cif()

project.display.show_pattern_options(expt_name='hrpt')
```

Open the main display views:

```python
project.display.pattern(expt_name='hrpt')
project.display.parameters.all()
project.display.parameters.fittable()
project.display.parameters.free()
project.display.parameters.access()
project.display.parameters.cif_uids()
```

## Show Tables and Select Types

EasyDiffraction uses two related display patterns:

- `show_*()` usually lists supported choices or displays a current
  configuration.
- `.show()` on a loop-style object usually prints rows you have already
  created.

Show created loop contents:

```python
experiment.background.show()
experiment.excluded_regions.show()
project.analysis.constraints.show()
```

List supported type choices. The current selection is marked in the
output:

```python
experiment.show_peak_profile_types()
experiment.show_background_types()
experiment.calculation.show_calculator_types()

project.analysis.fit.show_modes()
project.analysis.fit.show_minimizer_types()

project.rendering.show_chart_engines()
project.rendering.show_table_engines()
project.rendering.show_config()
```

Change the active type by assigning the corresponding `*_type` property:

```python
experiment.peak_profile_type = 'pseudo-voigt'
experiment.background_type = 'line-segment'
experiment.calculation.calculator_type = 'cryspy'

project.analysis.fit.mode = 'single'
project.analysis.fit.minimizer_type = 'lmfit'

project.rendering.chart_engine = 'plotly'
project.rendering.table_engine = 'rich'
```

For single-crystal experiments, extinction uses the same pattern:

```python
experiment.show_extinction_types()
experiment.extinction_type = 'becker-coppens'
```

## Find Commands with Help

Use help methods when you do not remember the exact command. The most
useful starting points are the project-level display and analysis
facades:

```python
project.display.help()
project.display.parameters.help()
project.display.fit.help()
project.analysis.help()
```

Drill into project collections to see what they contain:

```python
project.structures.help()
project.experiments.help()
```

Then inspect one structure or experiment:

```python
structure = project.structures['lbco']
experiment = project.experiments['hrpt']

structure.help()
experiment.help()
```

Category-level help shows available parameters and methods. This is
often the fastest way to remember exact names:

```python
structure.cell.help()
structure.atom_sites.help()
structure.atom_sites['O'].help()

experiment.instrument.help()
experiment.peak.help()
experiment.background.help()
experiment.background['1'].help()
```

Individual parameters also expose help. Use this when you need to check
whether a parameter is writable, free, constrained, or has fit bounds:

```python
structure.cell.length_a.help()
structure.atom_sites['O'].adp_iso.help()

experiment.instrument.calib_twotheta_offset.help()
experiment.linked_phases['lbco'].scale.help()
```

The usual navigation pattern is:

```text
project → structures/experiments → structure/experiment → category → item → parameter
```

## Refine Parameters

Mark parameters as free:

```python
structure.cell.length_a.free = True
structure.atom_sites['O'].adp_iso.free = True

experiment.instrument.calib_twotheta_offset.free = True
experiment.peak.broad_gauss_u.free = True
experiment.background['1'].y.free = True
experiment.linked_phases['lbco'].scale.free = True
```

Choose calculators and minimizers:

```python
experiment.calculation.show_calculator_types()
experiment.calculation.calculator_type = 'cryspy'

project.analysis.fit.show_modes()
project.analysis.fit.mode = 'single'

project.analysis.fit.show_minimizer_types()
project.analysis.fit.minimizer_type = 'lmfit'
```

Run a fit and inspect the result:

```python
project.analysis.fit()

project.display.fit.results()
project.display.fit.correlations()
project.display.pattern(expt_name='hrpt')
```

## Add Simple Constraints

Create aliases from parameter objects, then define a constraint
expression using those aliases:

```python
project.analysis.aliases.create(
    label='biso_la',
    param=project.structures['lbco'].atom_sites['La'].adp_iso,
)
project.analysis.aliases.create(
    label='biso_ba',
    param=project.structures['lbco'].atom_sites['Ba'].adp_iso,
)

project.analysis.constraints.create(expression='biso_ba = biso_la')
```

Show the created constraints:

```python
project.analysis.constraints.show()
```

Then fit again:

```python
project.analysis.fit()
project.display.fit.results()
```

## Save and Reuse Work

Save a project directory for later:

```python
project.save_as(dir_path='lbco_hrpt')
project.save()
```

Load it again:

```python
project = ed.Project.load('lbco_hrpt')
```

Run a saved project from the command line:

```bash
python -m easydiffraction fit lbco_hrpt
python -m easydiffraction fit lbco_hrpt --dry
```

## Command-Line Reminders

```bash
python -m easydiffraction --help
python -m easydiffraction --version
python -m easydiffraction list-tutorials
python -m easydiffraction download-tutorial 1 --destination tutorials
python -m easydiffraction download-all-tutorials --destination tutorials
python -m easydiffraction fit PROJECT_DIR
```
