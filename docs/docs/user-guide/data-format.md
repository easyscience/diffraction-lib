# Data Format

Before starting the data analysis workflow, it is important to define
the **data formats** used in EasyDiffraction.

## Edi Projects And CIF Data

Each software package typically uses its own **data format** and
**parameter names** for storing and sharing data. EasyDiffraction uses
**Edi** for saved project state and **Crystallographic Information File
(CIF)** for crystallographic input and strict report export.

!!! note "Pronunciation"

    **Edi** is the short name for EasyDiffraction, pronounced **"eddie"**
    (/ˈɛdi/). It is the same short form you use in code
    (`import easydiffraction as edi`) and the suffix on saved files
    (`.edi`). Write it as a word — lowercase `edi` for the extension and
    `_edi.*` keys, capitalised `Edi` at the start of a sentence — not as
    an all-caps acronym.

Edi uses CIF-like syntax, but its keys are chosen for EasyDiffraction's
Python-facing project model. CIF remains the standard exchange format
used by crystallography and materials science. It provides both a
human-readable syntax and dictionaries that define the meaning of each
parameter.

These dictionaries are maintained by the
[International Union of Crystallography (IUCr)](https://www.iucr.org).  
The base dictionary, **coreCIF**, contains the most common parameters in
crystallography. The **pdCIF** dictionary covers parameters specific to
powder diffraction, **magCIF** is used for magnetic structure analysis.

As most crystallographic parameters needed for diffraction data analysis
are already covered by IUCr dictionaries, EasyDiffraction follows those
dictionaries for CIF import and report output where they fit. Edi uses
the same names when they are already clear, and uses
EasyDiffraction-owned names where the project API is clearer.

The key advantage of CIF is standardized naming for scientific exchange.
The key advantage of Edi is that saved projects round-trip the
EasyDiffraction project model without overloading report CIF as project
state.

The [Parameters](parameters.md) section lists Python access paths, Edi
keys, and CIF keys side by side.

## Format Comparison

Below, we compare **CIF** with another common data format in
programming: **JSON**.

### Scientific Journals

Let's assume the following structural data for La₀.₅Ba₀.₅CoO₃ (LBCO), as
reported in a scientific publication. These parameters are to be refined
during diffraction data analysis:

Table 1. Crystallographic data. Space group: _Pm3̅m_.

| Parameter | Value  |
| --------- | ------ |
| a         | 3.8909 |
| b         | 3.8909 |
| c         | 3.8909 |
| alpha     | 90.0   |
| beta      | 90.0   |
| gamma     | 90.0   |

Table 2. Atomic coordinates (_x_, _y_, _z_), occupancies (occ) and
isotropic displacement parameters (_Biso_)

| Label | Type | x   | y   | z   | occ | Biso   |
| ----- | ---- | --- | --- | --- | --- | ------ |
| La    | La   | 0   | 0   | 0   | 0.5 | 0.4958 |
| Ba    | Ba   | 0   | 0   | 0   | 0.5 | 0.4943 |
| Co    | Co   | 0.5 | 0.5 | 0.5 | 1.0 | 0.2567 |
| O     | O    | 0   | 0.5 | 0.5 | 1.0 | 1.4041 |

### CIF

The data above would be represented in CIF as follows:

<!-- prettier-ignore-start -->

<div class="cif">
<pre>
data_<span class="red"><b>lbco</b></span>

<span class="blue"><b>_space_group</b>.name_H-M_alt</span>              "P m -3 m"
<span class="blue"><b>_space_group</b>.IT_coordinate_system_code</span> 1

<span class="blue"><b>_cell</b>.length_a</span>      3.8909
<span class="blue"><b>_cell</b>.length_b</span>      3.8909
<span class="blue"><b>_cell</b>.length_c</span>      3.8909
<span class="blue"><b>_cell</b>.angle_alpha</span>  90
<span class="blue"><b>_cell</b>.angle_beta</span>   90
<span class="blue"><b>_cell</b>.angle_gamma</span>  90

loop_
<span class="green"><b>_atom_site</b>.label</span>
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

Here, unit cell parameters are grouped under the `_cell` category, and
atomic positions under the `_atom_site` category. The `loop_` keyword
indicates that multiple rows follow for the listed parameters. Each atom
is identified using `_atom_site.label`.

### JSON

Representing the same data in **JSON** results in a format that is more
verbose and less human-readable, especially for large datasets. JSON is
ideal for structured data in programming environments, whereas CIF is
better suited for human-readable crystallographic data.

```json
{
  "lbco": {
    "space_group": {
      "name_H-M_alt": "P m -3 m",
      "IT_coordinate_system_code": 1
    },
    "cell": {
      "length_a": 3.8909,
      "length_b": 3.8909,
      "length_c": 3.8909,
      "angle_alpha": 90,
      "angle_beta": 90,
      "angle_gamma": 90
    },
    "atom_site": [
      {
        "label": "La",
        "type_symbol": "La",
        "fract_x": 0,
        "fract_y": 0,
        "fract_z": 0,
        "occupancy": 0.5,
        "B_iso_or_equiv": 0.4958
      },
      {
        "label": "Ba",
        "type_symbol": "Ba",
        "fract_x": 0,
        "fract_y": 0,
        "fract_z": 0,
        "occupancy": 0.5,
        "B_iso_or_equiv": 0.4943
      },
      {
        "label": "Co",
        "type_symbol": "Co",
        "fract_x": 0.5,
        "fract_y": 0.5,
        "fract_z": 0.5,
        "occupancy": 1.0,
        "B_iso_or_equiv": 0.2567
      },
      {
        "label": "O",
        "type_symbol": "O",
        "fract_x": 0,
        "fract_y": 0.5,
        "fract_z": 0.5,
        "occupancy": 1.0,
        "B_iso_or_equiv": 1.4041
      }
    ]
  }
}
```

## Experiment Definition

The previous example described the **structure** (crystallographic
model), but how is the **experiment** itself represented?

The experiment is saved in Edi. For example, line-segment background
intensity in a powder diffraction experiment is represented as:

<!-- prettier-ignore-start -->

<div class="cif">
<pre>
loop_
<span class="green"><b>_background</b>.position</span>
<span class="green"><b>_background</b>.intensity</span>

 10.0  174.3
 20.0  159.8
 30.0  167.9
 ...
</pre>
</div>

<!-- prettier-ignore-end -->

More details on how to define the experiment are provided in the
[Experiment](analysis-workflow/experiment.md) section.

## Other Input/Output Blocks

EasyDiffraction saves projects as a directory of Edi files and sidecars:

- `project.edi`: project metadata and display/report configuration
- `structures/<structure>.edi`: structure models
- `experiments/<experiment>.edi`: experiment setup and data
- `analysis/analysis.edi`: fitting and analysis settings
- `analysis/results.csv` and `analysis/results.h5`: fit result sidecars
- `reports/<project>.*`: generated reports when enabled through
  `project.report`

Examples for each block are provided in the
[Analysis Workflow](analysis-workflow/index.md) and
[Tutorials](../tutorials/index.md).

## Other Data Formats

EasyDiffraction also supports plain text files for importing measured
data. The meaning of the columns depends on the experiment type.

For example, in a standard constant-wavelength powder diffraction
experiment:

- Column 1: 2θ angle
- Column 2: intensity
- Column 3: standard uncertainty of the intensity

More details on supported input formats are provided in the
[Experiment](analysis-workflow/experiment.md) section.
