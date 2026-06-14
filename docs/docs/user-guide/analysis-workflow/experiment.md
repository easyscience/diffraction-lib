---
icon: material/microscope
---

# :material-microscope: Experiment

An **Experiment** in EasyDiffraction includes the measured diffraction
data along with all relevant parameters that describe the experimental
setup and associated conditions. This can include information about the
instrumental resolution, peak shape, background, etc.

## Defining an Experiment

EasyDiffraction allows you to:

- **Load an existing experiment** from a file (**CIF** format). Both the
  metadata and measured data are expected to be in CIF format.
- **Manually define** a new experiment by specifying its type, other
  necessary experimental parameters, as well as load measured data. This
  is useful when you want to create an experiment from scratch or when
  you have a measured data file in a non-CIF format (e.g., `.xye`,
  `.xy`).

Below, you will find instructions on how to define and manage
experiments in EasyDiffraction. It is assumed that you have already
created a `project` object, as described in the [Project](project.md)
section as well as defined its `structures`, as described in the
[Structure](model.md) section.

### Adding from CIF

This is the most straightforward way to define an experiment in
EasyDiffraction. If you have a crystallographic information file (CIF)
for your experiment, that contains both the necessary information
(metadata) about the experiment as well as the measured data, you can
add it to your `project.experiments` collection using the
`add_from_cif_path` method. In this case, the name of the experiment
will be taken from CIF.

```python
# Load an experiment from a CIF file
project.experiments.add_from_cif_path('data/hrpt_300K.cif')
```

You can also pass the content of the CIF file as a string using the
`add_from_cif_str` method:

```python
# Add an experiment from a CIF string
cif_string = """
... content of the CIF file ...
"""
project.experiments.add_from_cif_str(cif_string)
```

Accessing the experiment after adding it will also be done through the
`experiments` object of the `project` instance. The name of the
experiment will be the same as the data block id in the CIF file. For
example, if the CIF file contains a data block with the id `hrpt`,

<!-- prettier-ignore-start -->

<div class="cif">
<pre>
data_<span class="red"><b>hrpt</b></span>

<span class="blue"><b>_experiment_type</b>.beam_mode</span>  "constant wavelength"
...
</pre>
</div>

<!-- prettier-ignore-end -->

you can access it in the code as follows:

```python
# Access the experiment by its name
project.experiments['hrpt']
```

### Defining Manually

If you do not have a CIF file or prefer to define the experiment
manually, you can use the `add_from_data_path` method of the
`experiments` object of the `project` instance. In this case, you will
need to specify the **name** of the experiment, which will be used to
reference it later, as well as **data_path** to the measured data file
(e.g., `.xye`, `.xy`). Supported formats are described in the
[Measured Data Category](#measured-data-category) section.

Optionally, you can also specify the additional parameters that define
the **type of experiment** you want to create. If you do not specify any
of these parameters, the default values will be used, which are the
first in the list of supported options for each parameter:

- **sample_form**: The form of the sample (powder, single crystal).
- **beam_mode**: The mode of the beam (constant wavelength,
  time-of-flight).
- **radiation_probe**: The type of radiation used (neutron, X-ray).
- **scattering_type**: The type of scattering (bragg, total).

!!! warning "Important"

    It is important to mention that once an experiment is added, you cannot change
    these parameters. If you need to change them, you must create a new experiment
    or redefine the existing one.

Here is an example of how to add an experiment with all relevant
components explicitly defined:

```python
# Add an experiment with default parameters, based on the specified type.
project.experiments.add_from_data_path(
    name='hrpt',
    data_path='data/hrpt_lbco.xye',
    sample_form='powder',
    beam_mode='constant wavelength',
    radiation_probe='neutron',
    scattering_type='bragg',
)
```

To add an experiment of default type, you can simply do:

```python
# Add an experiment of default type
project.experiments.add_from_data_path(
    name='hrpt',
    data_path='data/hrpt_lbco.xye',
)
```

If you do not have measured data for fitting and only want to view the
simulated pattern, you can define an experiment without measured data
using the `create` method:

```python
# Add an experiment without measured data
project.experiments.create(
    name='hrpt',
    sample_form='powder',
    beam_mode='constant wavelength',
    radiation_probe='x-ray',
)
```

The calculated pattern needs a range to compute over. With no measured
data loaded, this comes from the `data_range` category, which defaults
to a sensible window derived from the instrument so the experiment is
calculable straight away. To choose the range yourself, set its bounds
and step (in 2θ for constant-wavelength, or time-of-flight for TOF):

```python
# Set the calculation range explicitly (constant wavelength)
data_range = project.experiments['hrpt'].data_range
data_range.two_theta_min = 10.0
data_range.two_theta_max = 160.0
data_range.two_theta_inc = 0.05
```

Once a measured scan is present the range is read from the data instead,
so `data_range` becomes read-only.

Finally, you can also add an experiment by passing the experiment object
directly using the `add` method:

```python
# Add an experiment by passing the experiment object directly
from easydiffraction import ExperimentFactory

experiment = ExperimentFactory.create(
    name='hrpt',
    data_path='data/hrpt_lbco.xye',
    sample_form='powder',
    beam_mode='constant wavelength',
    radiation_probe='neutron',
    scattering_type='bragg',
)
project.experiments.add(experiment)
```

## Modifying Parameters

When an experiment is added, it is created with a set of default
parameters that you can modify to match your specific experimental
setup. All parameters are grouped into categories based on their
function, making it easier to manage and understand the different
aspects of the experiment:

1. **Instrument Category**: Defines the instrument configuration,
   including wavelength, two-theta offset, and resolution parameters.
2. **Peak Category**: Specifies the peak profile type and its
   parameters, such as broadening and asymmetry.
3. **Background Category**: Defines the background type and allows you
   to add background points.
4. **Linked Structures Category**: Links the structure defined in the
   previous step to the experiment, allowing you to specify the scale
   factor for the linked structure.
5. **Measured Data Category**: Contains the measured data. The expected
   format depends on the experiment type, but generally includes columns
   for 2θ angle or TOF and intensity.

### 1. Instrument Category { #instrument-category }

```python
# Modify the default instrument parameters
project.experiments['hrpt'].instrument.setup_wavelength = 1.494
project.experiments['hrpt'].instrument.calib_twotheta_offset = 0.6
```

### 2. Excluded Regions Category { #excluded-regions-category }

```python
# Add excluded regions to the experiment
project.experiments['hrpt'].excluded_regions.create(start=0, end=10)
project.experiments['hrpt'].excluded_regions.create(start=160, end=180)
```

### 3. Peak Category { #peak-category }

```python
# Select the desired peak profile type
project.experiments['hrpt'].peak.type = 'pseudo-voigt'

# Modify default peak profile parameters
project.experiments['hrpt'].peak.broad_gauss_u = 0.1
project.experiments['hrpt'].peak.broad_gauss_v = -0.1
project.experiments['hrpt'].peak.broad_gauss_w = 0.1
project.experiments['hrpt'].peak.broad_lorentz_x = 0
project.experiments['hrpt'].peak.broad_lorentz_y = 0.1
```

### 4. Background Category { #background-category }

```python
# Select the desired background type
project.experiments['hrpt'].background.type = 'line-segment'

# Add background points
project.experiments['hrpt'].background.create(position=10, intensity=170)
project.experiments['hrpt'].background.create(position=30, intensity=170)
project.experiments['hrpt'].background.create(position=50, intensity=170)
project.experiments['hrpt'].background.create(position=110, intensity=170)
project.experiments['hrpt'].background.create(position=165, intensity=170)
```

Instead of placing every point by hand, you can let EasyDiffraction
detect a sensible set of background points directly from the measured
pattern with the `auto_estimate` method. Called with no arguments, it
builds a peak-insensitive background curve, places points between the
peaks, and reads their heights from that curve so they do not eat into
peak intensities:

```python
# Automatically estimate background points from the measured pattern
project.experiments['hrpt'].background.auto_estimate()
```

The generated points are ordinary, editable control points. They are
created **fixed** (not refined); you can review them, keep them, or free
any of them for refinement (see [Analysis](analysis.md)). Each call
**overwrites** the existing points (when there are active data to
estimate from), so you always start from a clean, reproducible
background; if no active data remain — for example every point is
excluded, or data are not yet loaded — it warns and leaves your existing
points unchanged. It works for both constant-wavelength and
time-of-flight data, neutron and X-ray.

You can also guide the estimate with optional arguments, for example to
cap the number of points or choose a specific method:

```python
# Estimate with at most 10 background points
project.experiments['hrpt'].background.auto_estimate(n_points=10)
```

### 5. Linked Structures Category { #linked-structures-category }

```python
# Link the structure defined in the previous step to the experiment
project.experiments['hrpt'].linked_structures.create(structure_id='lbco', scale=10.0)
```

### 6. Preferred Orientation Category { #preferred-orientation-category }

For textured powders, add a March–Dollase preferred-orientation
correction per phase. Set the March coefficient `march_r` (1 = no
texture, &lt;1 platy/disk, &gt;1 needle), the texture direction
(`index_h`, `index_k`, `index_l`), and optionally the random untextured
fraction `march_random_fract`:

```python
# Add a March–Dollase preferred-orientation correction for a phase
project.experiments['hrpt'].preferred_orientation.create(
    structure_id='lbco', march_r=1.2, index_h=0, index_k=0, index_l=1
)
```

This is a constant-wavelength Bragg powder correction, available on the
`cryspy` engine. The defaults (`march_r=1`, `march_random_fract=0`)
apply no texture, so it has no effect until you set them. See the
[preferred-orientation parameters](../parameters/experiment/preferred_orientation.md)
for details.

### 7. Measured Data Category { #measured-data-category }

If you do not have a CIF file for your experiment, you can load measured
data from a file in a supported format. The measured data is added to
the experiment and saved with the project as Edifa. The expected format
depends on the experiment type.

#### Supported data file formats:

- `.xye` or `.xys` (3 columns, including standard deviations)
  - [\_data.two_theta](../parameters/experiment/data.md#data-two-theta)
  - [\_data.intensity_meas](../parameters/experiment/data.md#data-intensity-meas)
  - [\_data.intensity_meas_su](../parameters/experiment/data.md#data-intensity-meas-su)
- `.xy` (2 columns, no standard deviations):
  - [\_data.two_theta](../parameters/experiment/data.md#data-two-theta)
  - [\_data.intensity_meas](../parameters/experiment/data.md#data-intensity-meas)

If no **standard deviations** are provided, they are automatically
calculated as the **square root** of measured intensities.

Optional comments with `#` are possible in data file headers.

Here are some examples:

#### example1.xye

<!-- prettier-ignore-start -->
<div class="cif">
<pre>
<span class="grey"># 2theta  intensity    su</span>
   10.00     167      12.6
   10.05     157      12.5
   10.10     187      13.3
   10.15     197      14.0
   10.20     164      12.5
  ...
  164.65     173      30.1
  164.70     187      27.9
  164.75     175      38.2
  164.80     168      30.9
  164.85     109      41.2
</pre>
</div>
<!-- prettier-ignore-end -->

#### example2.xy

<!-- prettier-ignore-start -->
<div class="cif">
<pre>
<span class="grey"># 2theta  intensity</span>
   10.00     167    
   10.05     157    
   10.10     187    
   10.15     197    
   10.20     164    
  ...
  164.65     173    
  164.70     187    
  164.75     175    
  164.80     168    
  164.85     109  
</pre>
</div>
<!-- prettier-ignore-end -->

#### example3.xy

<!-- prettier-ignore-start -->
<div class="cif">
<pre>
10  167.3    
10.05  157.4    
10.1  187.1    
10.15  197.8    
10.2  164.9    
...
164.65  173.3    
164.7  187.5    
164.75  175.8    
164.8  168.1    
164.85  109     
</pre>
</div>
<!-- prettier-ignore-end -->

## Listing Defined Experiments

To check which experiments have been added to the `project`, use:

```python
# Show defined experiments
project.experiments.show_names()
```

Expected output:

```
Defined experiments 🔬
['hrpt']
```

## Viewing an Experiment as Text

To inspect an experiment's serialized text (the same content the project
persists into its Edifa files), use:

```python
# Show experiment as text
project.experiments['hrpt'].show_as_text()
```

Long loops (measured data, reflections) are truncated with `...` for
display. Example output:

```
Experiment 🔬 'hrpt' as text
┌────────────────────────────────────────────────────┐
│       CIF                                            │
├────────────────────────────────────────────────────┤
│   1   data_hrpt                                      │
│   2                                                  │
│   3   _experiment_type.sample_form powder            │
│   4   _experiment_type.beam_mode "constant wavelength" │
│   5   _experiment_type.radiation_probe neutron       │
│   6   _experiment_type.scattering_type bragg         │
│   7                                                  │
│   8   _calculator.type cryspy                        │
│   9                                                  │
│  10   _peak.broad_gauss_u 0.0816(31)                 │
│  11   _peak.broad_gauss_v -0.1159(66)                │
│  12   _peak.broad_gauss_w 0.1204(32)                 │
│  13   _peak.broad_lorentz_x 0.                       │
│  14   _peak.broad_lorentz_y 0.0844(21)               │
│  15   _peak.type cwl-pseudo-voigt                    │
│  16                                                  │
│  17   _instrument.setup_wavelength 1.494             │
│  18   _instrument.calib_twotheta_offset 0.6226(10)   │
│  19                                                  │
│  20   loop_                                          │
│  21   _linked_structure.structure_id                 │
│  22   _linked_structure.scale                        │
│  23   lbco 9.135(54)                                 │
│  24                                                  │
│  25   _background.type line-segment                  │
│  26                                                  │
│  27   loop_                                          │
│  28   _background.id                                 │
│  29   _background.position                           │
│  30   _background.intensity                          │
│  31   1 10. 168.4(1.4)                               │
│  32   ...                                            │
│  33                                                  │
│  34   loop_                                          │
│  35   _data.two_theta                                │
│  36   _data.id                                       │
│  37   _data.intensity_meas                           │
│  38   _data.intensity_meas_su                        │
│  39   10. 1 167. 12.6                                │
│  40   ...                                            │
└────────────────────────────────────────────────────┘
```

## Saving an Experiment

Saving the project, as described in the [Project](project.md) section, will
also save the experiment. Each experiment is saved as a separate
`.edifa` file in the `experiments` subdirectory of the project
directory. The project file contains references to these files.

EasyDiffraction supports different types of experiments, and each
experiment is saved in a dedicated Edifa file with experiment-specific
parameters.

Below are examples of how different experiments are saved in Edifa
format.

### [pd-neut-cwl][3]{:.label-experiment}

This example represents a constant-wavelength neutron powder diffraction
experiment:

<!-- prettier-ignore-start -->

<div class="cif">
<pre>
data_<span class="red"><b>hrpt</b></span>

<span class="blue"><b>_experiment_type</b>.beam_mode</span>        "constant wavelength"
<span class="blue"><b>_experiment_type</b>.radiation_probe</span>  neutron
<span class="blue"><b>_experiment_type</b>.sample_form</span>      powder
<span class="blue"><b>_experiment_type</b>.scattering_type</span>  bragg

<span class="blue"><b>_instrument</b>.setup_wavelength</span>       1.494
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
 1   10  174.3
 2   20  159.8
 3   30  167.9
 4   50  166.1
 5   70  172.3
 6   90  171.1
 7  110  172.4
 8  130  182.5
 9  150  173.0
10  165  171.1

loop_
<span class="green"><b>_data</b>.id</span>
<span class="green"><b>_data</b>.two_theta</span>
<span class="green"><b>_data</b>.intensity_meas</span>
<span class="green"><b>_data</b>.intensity_meas_su</span>
1   10.00  167  12.6
2   10.05  157  12.5
3   10.10  187  13.3
4   10.15  197  14.0
5   10.20  164  12.5
6   10.25  171  13.0
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

### [pd-neut-tof][3]{:.label-experiment}

This example demonstrates a time-of-flight neutron powder diffraction
experiment:

<!-- prettier-ignore-start -->
<div class="cif">
<pre>
data_<span class="red"><b>wish</b></span>

<span class="blue"><b>_experiment_type</b>.beam_mode</span>        "time-of-flight"
<span class="blue"><b>_experiment_type</b>.radiation_probe</span>  neutron
<span class="blue"><b>_experiment_type</b>.sample_form</span>      powder
<span class="blue"><b>_experiment_type</b>.scattering_type</span>  bragg

<span class="blue"><b>_instrument</b>.setup_twotheta_bank</span> 152.827

<span class="blue"><b>_instrument</b>.calib_d_to_tof_linear</span>    20773.1(3)
<span class="blue"><b>_instrument</b>.calib_d_to_tof_quadratic</span> -1.08308
<span class="blue"><b>_instrument</b>.calib_d_to_tof_offset</span>    -13.7(5)

<span class="blue"><b>_peak</b>.exp_rise_alpha_0</span>    -0.009(1)
<span class="blue"><b>_peak</b>.exp_rise_alpha_1</span>     0.109(2)
<span class="blue"><b>_peak</b>.exp_decay_beta_0</span>     0.00670(3)
<span class="blue"><b>_peak</b>.exp_decay_beta_1</span>     0.0100(3)
<span class="blue"><b>_peak</b>.broad_gauss_sigma_0</span> 0
<span class="blue"><b>_peak</b>.broad_gauss_sigma_1</span> 0
<span class="blue"><b>_peak</b>.broad_gauss_sigma_2</span> 15.7(8)

loop_
<span class="green"><b>_linked_structure</b>.structure_id</span>
<span class="green"><b>_linked_structure</b>.scale</span>
ncaf 1.093(5)

loop_
<span class="green"><b>_background</b>.id</span>
<span class="green"><b>_background</b>.position</span>
<span class="green"><b>_background</b>.intensity</span>
 1    9162.3  465(38)
 2   11136.8  593(30)
 3   14906.5  546(18)
 4   17352.2  496(14)
 5   20179.5  452(10)
 6   22176.0  468(12)
 7   24644.7  380(6)
 8   28257.2  378(4)
 9   34034.4  328(4)
10   41214.6  323(3)
11   49830.9  273(3)
12   58204.9  260(4)
13   70186.9  262(5)
14   82103.2  268(5)
15  102712.0  262(15)

loop_
<span class="green"><b>_data</b>.id</span>
<span class="green"><b>_data</b>.time_of_flight</span>
<span class="green"><b>_data</b>.intensity_meas</span>
<span class="green"><b>_data</b>.intensity_meas_su</span>
1    9001.0  616.523  124.564
2    9006.8  578.769  123.141
3    9012.6  574.184  120.507
4    9018.5  507.739  111.300
5    9024.3  404.672  101.616
6    9030.1  469.244  107.991
...
103085.0  275.072   60.978
103151.4  214.187   55.675
103217.9  256.211   62.825
103284.4  323.872   73.082
103351.0  242.382   65.736
103417.6  277.666   73.837
</pre>
</div>
<!-- prettier-ignore-end -->

### [sc-neut-cwl][3]{:.label-experiment}

This example represents a single-crystal neutron diffraction experiment:

<!-- prettier-ignore-start -->
<div class="cif">
<pre>
data_<span class="red"><b>heidi</b></span>

<span class="blue"><b>_experiment_type</b>.beam_mode</span>        "constant wavelength"
<span class="blue"><b>_experiment_type</b>.radiation_probe</span>  neutron
<span class="blue"><b>_experiment_type</b>.sample_form</span>      "single crystal"
<span class="blue"><b>_experiment_type</b>.scattering_type</span>  bragg

<span class="blue"><b>_instrument</b>.setup_wavelength</span>       0.793

loop_
<span class="green"><b>_linked_structure</b>.structure_id</span>
<span class="green"><b>_linked_structure</b>.scale</span>
tbti 2.92(6)

loop_
<span class="green"><b>_refln</b>.index_h</span>
<span class="green"><b>_refln</b>.index_k</span>
<span class="green"><b>_refln</b>.index_l</span>
<span class="green"><b>_refln</b>.intensity_meas</span>
<span class="green"><b>_refln</b>.intensity_meas_su</span>
 1  1  1   194.5677    2.3253
 2  2  0    22.6319    1.1233
 3  1  1    99.2917    2.5620
 2  2  2   219.2877    3.2522
...
16  8  8    29.3063   12.6552
17  7  7  1601.5154  628.8915
13 13  7  1176.0896  414.6018
19  5  1     0.8334   20.4207
15  9  9    10.9864    8.0650
12 12 10    14.4074   11.3800
</pre>
</div>
<!-- prettier-ignore-end -->

<!-- prettier-ignore-start -->
[3]: ../glossary.md#experiment-type-labels
<!-- prettier-ignore-end -->

<br>

---

Now that the experiment has been defined, you can proceed to the next
step: [Analysis](analysis.md).
