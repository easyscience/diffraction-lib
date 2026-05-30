---
icon: material/puzzle
---

# :material-puzzle: Structure

The **Structure** in EasyDiffraction represents the **crystallographic
structure** used to calculate the diffraction pattern, which is then
fitted to the **experimentally measured data** to refine the structural
parameters.

EasyDiffraction allows you to:

- **Load an existing model** from a file (**CIF** format).
- **Manually define** a new structure by specifying crystallographic
  parameters.

Below, you will find instructions on how to define and manage
crystallographic models in EasyDiffraction. It is assumed that you have
already created a `project` object, as described in the
[Project](project.md) section.

## Adding a Model from CIF

This is the most straightforward way to define a structure in
EasyDiffraction. If you have a crystallographic information file (CIF)
for your structure, you can add it to your project using the
`add_from_cif_path` method of the `project.structures` collection. In
this case, the name of the model will be taken from CIF.

```python
# Load a phase from a CIF file
project.structures.add_from_cif_path('data/lbco.cif')
```

Accessing the model after loading it will be done through the
`structures` collection of the `project` instance. The name of the model
will be the same as the data block id in the CIF file. For example, if
the CIF file contains a data block with the id `lbco`,

<!-- prettier-ignore-start -->

<div class="cif">
<pre>
data_<span class="red"><b>lbco</b></span>

<span class="blue"><b>_space_group</b>.name_H-M_alt</span>  "P m -3 m"
...
</pre>
</div>

<!-- prettier-ignore-end -->

you can access it in the code as follows:

```python
# Access the structure by its name
project.structures['lbco']
```

## Defining a Model Manually

If you do not have a CIF file or prefer to define the model manually,
you can use the `create` method of the `structures` object of the
`project` instance. In this case, you will need to specify the name of
the model, which will be used to reference it later.

```python
# Add a structure with default parameters
# The structure name is used to reference it later.
project.structures.create(name='nacl')
```

The `add` method creates a new structure with default parameters. You
can then modify its parameters to match your specific crystallographic
structure. All parameters are grouped into the following categories,
which makes it easier to manage the model:

1. **Space Group Category**: Defines the symmetry of the crystal
   structure.
2. **Cell Category**: Specifies the dimensions and angles of the unit
   cell.
3. **Atom Sites Category**: Describes the positions and properties of
   atoms within the unit cell.

### 1. Space Group Category { #space-group-category }

```python
# Set space group
project.structures['nacl'].space_group.name_h_m = 'F m -3 m'
```

### 2. Cell Category { #cell-category }

```python
# Define unit cell parameters
project.structures['nacl'].cell.length_a = 5.691694
```

### 3. Atom Sites Category { #atom-sites-category }

```python
# Add atomic sites
project.structures['nacl'].atom_sites.create(
    label='Na',
    type_symbol='Na',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    occupancy=1,
    adp_iso=0.5,
)
project.structures['nacl'].atom_sites.create(
    label='Cl',
    type_symbol='Cl',
    fract_x=0,
    fract_y=0,
    fract_z=0.5,
    occupancy=1,
    adp_iso=0.5,
)
```

## Listing Defined Models

To check which structures have been added to the `project`, use:

```python
# Show defined structures
project.structures.show_names()
```

Expected output:

```
Defined structures 🧩
['lbco', 'nacl']
```

## Viewing a Model as CIF

To inspect a structure in CIF format, use:

```python
# Show structure as CIF
project.structures['lbco'].show_as_cif()
```

Example output:

```
Structure 🧩 'lbco' as cif
╒═══════════════════════════════════════════╕
│ data_lbco                                 │
│                                           │
│ _space_group.IT_coordinate_system_code  1 │
│ _space_group.name_H-M_alt  "P m -3 m"     │
│                                           │
│ _cell.angle_alpha  90                     │
│ _cell.angle_beta  90                      │
│ _cell.angle_gamma  90                     │
│ _cell.length_a  3.88                      │
│ _cell.length_b  3.88                      │
│ _cell.length_c  3.88                      │
│                                           │
│ loop_                                     │
│ _atom_site.ADP_type                       │
│ _atom_site.B_iso_or_equiv                 │
│ _atom_site.fract_x                        │
│ _atom_site.fract_y                        │
│ _atom_site.fract_z                        │
│ _atom_site.label                          │
│ _atom_site.occupancy                      │
│ _atom_site.type_symbol                    │
│ _atom_site.Wyckoff_letter                 │
│ Biso 0.5 0.0 0.0 0.0 La 0.5 La a          │
│ Biso 0.5 0.0 0.0 0.0 Ba 0.5 Ba a          │
│ Biso 0.5 0.5 0.5 0.5 Co 1.0 Co b          │
│ Biso 0.5 0.0 0.5 0.5 O 1.0 O c            │
╘═══════════════════════════════════════════╛
```

## Viewing a Model in 3D

EasyDiffraction can render a defined structure as an interactive 3D view.
The renderer engine is chosen through `project.rendering_structure`. The default `auto`
engine resolves to the interactive Three.js view in Jupyter and the
terminal-friendly ASCII schematic in a console — mirroring how
`project.rendering_plot` and `project.rendering_table` pick their environment defaults.

```python
# List the available renderer engines
project.rendering_structure.show_supported()

# Override the automatic choice if desired ('auto', 'threejs', 'ascii')
project.rendering_structure.type = 'auto'
```

Visual styling — independent of the per-element data — is configured on
`project.style`:

```python
# List the accepted style settings
project.style.show_supported()

# Choose how atoms are depicted, sized, and coloured
project.style.atom_shape = 'ball'  # 'ball' or 'ortep'
project.style.radius_model = 'covalent'  # 'vdw', 'covalent', 'ionic', 'atomic'
project.style.color_scheme = 'jmol'  # 'jmol' or 'vesta'
project.style.atom_scale = 0.3  # overall ball size (square-root compressed)
```

Bonds are generated automatically between atoms whose separation falls
within the per-structure cutoffs stored on `structure.geom` (the standard
cif_core `_geom` parameters):

```python
# Tune the per-structure bond-generation cutoffs (angstrom)
project.structures['lbco'].geom.min_bond_distance_cutoff = 0.5
project.structures['lbco'].geom.bond_distance_incr = 0.25
```

Draw the structure through `project.display`, mirroring
`project.display.pattern()`:

```python
# List which features the data and active engine can draw
project.display.show_structure_options(struct_name='lbco')

# Draw the structure (include='auto' shows every available feature)
project.display.structure(struct_name='lbco')

# Or request a specific set of features
project.display.structure(
    struct_name='lbco',
    include=('atoms', 'bonds', 'cell'),
)
```

The same interactive view is embedded automatically in the HTML report
(see the [Report](report.md) section).

## Saving a Model

Saving the project, as described in the [Project](project.md) section,
will also save the model. Each model is saved as a separate CIF file in
the `structures` subdirectory of the project directory. The project file
contains references to these files.

Below is an example of the saved CIF file for the `lbco` model:

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
<span class="green"><b>_atom_site</b>.Wyckoff_letter</span>
<span class="green"><b>_atom_site</b>.occupancy</span>
<span class="green"><b>_atom_site</b>.adp_type</span>
<span class="green"><b>_atom_site</b>.B_iso_or_equiv</span>
La La   0   0   0     a   0.5  Biso 0.4958
Ba Ba   0   0   0     a   0.5  Biso 0.4943
Co Co   0.5 0.5 0.5   b   1    Biso 0.2567
O  O    0   0.5 0.5   c   1    Biso 1.4041
</pre>
</div>

<!-- prettier-ignore-end -->

<br>

---

Now that the crystallographic model has been defined and added to the
project, you can proceed to the next step: [Experiment](experiment.md).
