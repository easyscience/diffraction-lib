---
icon: material/puzzle
---

# :material-puzzle: Model

The **Model** in EasyDiffraction represents the **crystallographic structure**
used to calculate the diffraction pattern. This pattern is then fitted to
the **experimental data** to analyze and refine the structural parameters.

EasyDiffraction allows you to:

- **Manually define** a new model by specifying crystallographic parameters.
- **Load an existing model** from a **CIF file**.

Below, you will find instructions on how to define and manage crystallographic
models in EasyDiffraction. It is assumed that you have already created a 
`project` object, as described in the [Project](project.md) section.

## Defining a Model Manually

You can manually define a model by specifying the **space group**,
**unit cell**, and **atom site** parameters. Here's an example of how to
create a model for **NaCl**:

```python
# Add a sample model with default parameters
# The sample model name is used then to refer to the model
project.sample_models.add(name='nacl')

# Set space group
project.sample_models['nacl'].space_group.name_h_m = 'F m -3 m'

# Define unit cell parameters
project.sample_models['nacl'].cell.length_a = 5.691694

# Add atomic sites
project.sample_models['nacl'].atom_sites.append(label='Na',
                                                type_symbol='Na',
                                                fract_x=0,
                                                fract_y=0,
                                                fract_z=0,
                                                occupancy=1,
                                                b_iso_or_equiv=0.5)
project.sample_models['nacl'].atom_sites.append(label='Cl',
                                                type_symbol='Cl',
                                                fract_x=0,
                                                fract_y=0,
                                                fract_z=0.5,
                                                occupancy=1,
                                                b_iso_or_equiv=0.5)
```

## Loading a Model from a CIF File

Instead of defining the model manually, you can load a crystallographic information file (CIF) directly:

```python
# Load a phase from a CIF file
job.add_phase_from_file('data/lbco.cif')
```

## Listing Defined Phases

To check which phases have been added to the `project`, use:

```python
# Show defined sample models
project.sample_models.show_names()
```

Expected output:

```
Defined sample models 🧩
['nacl', 'lbco']
```

## Viewing a Phase as a CIF

To inspect a phase in CIF format, use:

```python
# Show sample model as CIF
project.sample_models['lbco'].show_as_cif()
```

Example output:

```
Sample model 🧩 'lbco' as cif
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

Now that the Model has been defined, you can proceed to the next step:
[Experiment](experiment.md).
