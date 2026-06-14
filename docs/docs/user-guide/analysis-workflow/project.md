---
icon: material/archive
---

# :material-archive: Project

The **Project** serves as a container for all data and metadata
associated with a particular data analysis task. It acts as the
top-level entity in EasyDiffraction, ensuring structured organization
and easy access to relevant information. Each project can contain
multiple **experimental datasets**, with each dataset containing
contribution from multiple **structures**.

EasyDiffraction allows you to:

- **Manually create** a new project by specifying its metadata.
- **Load an existing saved project** from its project directory.

Below are instructions on how to set up a project in EasyDiffraction. It
is assumed that you have already imported the `easydiffraction` package,
as described in the [First Steps](../first-steps.md) section.

## Creating a Project Manually

You can manually create a new project and specify its short **name**,
**title** and **description**. All these parameters are optional.

```py
# Create a new project
project = ed.Project(name='lbco_hrpt')

# Define project metadata
project.metadata.title = 'La0.5Ba0.5CoO3 from neutron diffraction at HRPT@PSI'
project.metadata.description = """This project demonstrates a standard refinement
of La0.5Ba0.5CoO3, which crystallizes in a perovskite-type structure, using
neutron powder diffraction data collected in constant wavelength mode at the
HRPT diffractometer (PSI)."""
```

## Saving a Project

Saving the initial project requires specifying the directory path:

```python
project.save_as(dir_path='lbco_hrpt')
```

If working in the interactive mode in a Jupyter notebook or similar
environment, you can also save the project after every significant
change. This is useful for keeping track of changes and ensuring that
your work is not lost. If you already saved the project with `save_as`,
you can just call the `save`:

```python
project.save()
```

## Loading a Saved Project

If you have an existing saved project, load it from the project
directory created by `project.save_as()` or `project.save()`. This is
useful for continuing a previous session or reusing a downloaded saved
project.

```python
project = ed.Project.load('lbco_hrpt')
```

## Project Structure

The example below illustrates a typical **project structure** for a
**constant-wavelength powder neutron diffraction** experiment:

<!-- prettier-ignore-start -->

<div class="cif">
<pre>
📁 <span class="red"><b>La0.5Ba0.5CoO3</b></span>     - project root
├── 📄 <span class="orange"><b>project.edifa</b></span> - project configuration
├── 📁 structures  - structures
│   ├── 📄 <span class="orange"><b>lbco.edifa</b></span> - LBCO
│   └── ...
├── 📁 experiments - experiments
│   ├── 📄 <span class="orange"><b>hrpt.edifa</b></span> - HRPT pattern
│   └── ...
├── 📁 analysis    - analysis
│   ├── 📄 <span class="orange"><b>analysis.edifa</b></span> - fit state
│   └── 📄 <span class="orange"><b>results.h5</b></span>   - Bayesian arrays
└── 📁 reports     - reports
    ├── 📄 <span class="orange"><b>La0.5Ba0.5CoO3.cif</b></span>  - IUCr
    └── 📄 <span class="orange"><b>La0.5Ba0.5CoO3.html</b></span> - HTML
</pre>
</div>

<!-- prettier-ignore-end -->

## Project Files

Below is a representative project example stored in the `La0.5Ba0.5CoO3`
directory, showing the main files created by a typical workflow.

!!! warning "Important"

    If you save the project right after creating it, the project directory will
    only contain the `project.edifa` file. The other folders and files will be
    created as you add structures, experiments, and set up the analysis. The
    reports folder is created only when at least one of
    `project.report.cif`, `project.report.html`, `project.report.tex`,
    or `project.report.pdf` is set to `True` before `project.save()`.

### 1. <span class="orange">project.edifa</span>

This file stores project-level metadata and display configuration.

<!-- prettier-ignore-start -->

<div class="cif">
<pre>
<span class="blue"><b>_edifa</b>.schema_name</span>    EasyDiffraction
<span class="blue"><b>_edifa</b>.schema_version</span> 1

<span class="blue"><b>_metadata</b>.name</span>          lbco_hrpt
<span class="blue"><b>_metadata</b>.title</span>         "La0.5Ba0.5CoO3 from neutron diffraction at HRPT@PSI"
<span class="blue"><b>_metadata</b>.description</span>   "neutrons, powder, constant wavelength, HRPT@PSI"
<span class="blue"><b>_metadata</b>.created</span>       "18 May 2026 10:15:00"
<span class="blue"><b>_metadata</b>.last_modified</span> "18 May 2026 10:20:00"

<span class="blue"><b>_rendering_plot</b>.type</span>      auto
<span class="blue"><b>_report</b>.cif</span>               false
<span class="blue"><b>_report</b>.html</span>              true
<span class="blue"><b>_report</b>.tex</span>               false
<span class="blue"><b>_report</b>.pdf</span>               false
<span class="blue"><b>_report</b>.html_offline</span>      false
<span class="blue"><b>_rendering_table</b>.type</span>     auto
<span class="blue"><b>_rendering_structure</b>.type</span> auto
<span class="blue"><b>_structure_view</b>.show_labels</span> false
<span class="blue"><b>_structure_style</b>.atom_view</span> covalent
<span class="blue"><b>_structure_style</b>.color_scheme</span> jmol
<span class="blue"><b>_verbosity</b>.fit</span>         full
</pre>
</div>

<!-- prettier-ignore-end -->

### 2. structures / <span class="orange">lbco.edifa</span>

This file contains crystallographic information associated with the
structure model, including **space group**, **unit cell parameters**,
and **atomic positions**.

<!-- prettier-ignore-start -->

<div class="cif">
<pre>
data_<span class="red"><b>lbco</b></span>

<span class="blue"><b>_space_group</b>.name_H-M_alt</span>              "P m -3 m"
<span class="blue"><b>_space_group</b>.IT_coordinate_system_code</span> 1

<span class="blue"><b>_cell</b>.length_a</span>      3.8909(1)
<span class="blue"><b>_cell</b>.length_b</span>      3.8909
<span class="blue"><b>_cell</b>.length_c</span>      3.8909
<span class="blue"><b>_cell</b>.angle_alpha</span>  90
<span class="blue"><b>_cell</b>.angle_beta</span>   90
<span class="blue"><b>_cell</b>.angle_gamma</span>  90

loop_
<span class="green"><b>_atom_site</b>.id</span>
<span class="green"><b>_atom_site</b>.type_symbol</span>
<span class="green"><b>_atom_site</b>.fract_x</span>
<span class="green"><b>_atom_site</b>.fract_y</span>
<span class="green"><b>_atom_site</b>.fract_z</span>
<span class="green"><b>_atom_site</b>.Wyckoff_symbol</span>
<span class="green"><b>_atom_site</b>.occupancy</span>
<span class="green"><b>_atom_site</b>.ADP_type</span>
<span class="green"><b>_atom_site</b>.B_iso_or_equiv</span>
La La   0   0   0     a   0.5  Biso 0.4958
Ba Ba   0   0   0     a   0.5  Biso 0.4943
Co Co   0.5 0.5 0.5   b   1    Biso 0.2567
O  O    0   0.5 0.5   c   1    Biso 1.4041
</pre>
</div>

<!-- prettier-ignore-end -->

### 3. experiments / <span class="orange">hrpt.edifa</span>

This file contains the **experiment type**, **calculation engine**,
**instrumental parameters**, **peak parameters**, **associated phases**,
**background parameters** and **measured diffraction data**.

<!-- prettier-ignore-start -->

<div class="cif">
<pre>
data_<span class="red"><b>hrpt</b></span>

<span class="blue"><b>_experiment_type</b>.beam_mode</span>        "constant wavelength"
<span class="blue"><b>_experiment_type</b>.radiation_probe</span>  neutron
<span class="blue"><b>_experiment_type</b>.sample_form</span>      powder
<span class="blue"><b>_experiment_type</b>.scattering_type</span>  bragg

<span class="blue"><b>_calculator</b>.type</span> cryspy

<span class="blue"><b>_instrument</b>.setup_wavelength</span>        1.494
<span class="blue"><b>_instrument</b>.calib_twotheta_offset</span> 0.6225(4)

<span class="blue"><b>_peak</b>.broad_gauss_u</span>    0.0834
<span class="blue"><b>_peak</b>.broad_gauss_v</span>   -0.1168
<span class="blue"><b>_peak</b>.broad_gauss_w</span>    0.123
<span class="blue"><b>_peak</b>.broad_lorentz_x</span>  0
<span class="blue"><b>_peak</b>.broad_lorentz_y</span>  0.0797

loop_
<span class="green"><b>_linked_structure</b>.structure_id</span>
<span class="green"><b>_linked_structure</b>.scale</span>
lbco 9.0976(3)

loop_
<span class="green"><b>_background</b>.id</span>
<span class="green"><b>_background</b>.position</span>
<span class="green"><b>_background</b>.intensity</span>
1  10  174.3
2  20  159.8
3  30  167.9
4  50  166.1
5  70  172.3
6  90  171.1

loop_
<span class="green"><b>_data</b>.id</span>
<span class="green"><b>_data</b>.two_theta</span>
<span class="green"><b>_data</b>.intensity_meas</span>
<span class="green"><b>_data</b>.intensity_meas_su</span>
1  10.00  167  12.6
2  10.05  157  12.5
3  10.10  187  13.3
4  10.15  197  14.0
5  10.20  164  12.5
6  10.25  171  13.0
...
164.60  153  20.7
164.65  173  30.1
164.70  187  27.9
164.75  175  38.2
164.80  168  30.9
164.85  109  41.2
</pre>
</div>

<!-- prettier-ignore-end -->

### 4. analysis / <span class="orange">analysis.edifa</span>

This file contains settings used for data analysis, including the choice
of **calculation** and **fitting** engines, as well as user defined
**constraints**.

<!-- prettier-ignore-start -->

<div class="cif">
<pre>
<span class="blue"><b>_fitting_mode</b>.type</span>              single
<span class="blue"><b>_minimizer</b>.type</span>                 lmfit

loop_
<span class="green"><b>_alias</b>.label</span>
<span class="green"><b>_alias</b>.parameter_unique_name</span>
biso_La  lbco.atom_site.La.B_iso_or_equiv
biso_Ba  lbco.atom_site.Ba.B_iso_or_equiv
occ_La   lbco.atom_site.La.occupancy
occ_Ba   lbco.atom_site.Ba.occupancy

loop_
<span class="green"><b>_constraint</b>.id</span>
<span class="green"><b>_constraint</b>.expression</span>
biso_Ba  "biso_Ba = biso_La"
occ_Ba   "occ_Ba = 1 - occ_La"
</pre>
</div>

<!-- prettier-ignore-end -->

When a Bayesian fit stores persisted posterior or predictive arrays, the
same `analysis/` directory also contains `results.h5`.

<br>

---

Now that the Project has been defined, you can proceed to the next step:
[Structure](model.md).
