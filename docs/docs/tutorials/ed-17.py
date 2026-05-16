# %% [markdown]
# # Structure Refinement: Co2SiO4, D20 (T-scan)
#
# This example demonstrates a Rietveld refinement of the Co2SiO4 crystal
# structure using constant-wavelength neutron powder diffraction data
# from D20 at ILL. A sequential refinement is performed against a
# temperature scan using sequential fitting, which processes each data
# file independently without loading all datasets into memory at once.

# %% [markdown]
# ## Import Library

# %%
import easydiffraction as ed

# %% [markdown]
# ## Step 1: Define Project
#
# The project object manages structures, experiments, and analysis.

# %%
project = ed.Project()

# %% [markdown]
# The project must be saved before running sequential fitting, so that
# results can be written to `analysis/results.csv`.

# %%
project.save_as('projects/cosio', temporary=False)

# %% [markdown]
# ## Step 2: Define Crystal Structure
#
# This section shows how to add structures and modify their
# parameters.
#
# #### Create Structure

# %%
project.structures.create(name='cosio')
structure = project.structures['cosio']

# %% [markdown]
# #### Set Space Group

# %%
structure.space_group.name_h_m = 'P n m a'
structure.space_group.it_coordinate_system_code = 'abc'

# %% [markdown]
# #### Set Unit Cell

# %%
structure.cell.length_a = 10.31
structure.cell.length_b = 6.0
structure.cell.length_c = 4.79

# %% [markdown]
# #### Set Atom Sites

# %%
structure.atom_sites.create(
    label='Co1',
    type_symbol='Co',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    wyckoff_letter='a',
    adp_iso=0.3,
)
structure.atom_sites.create(
    label='Co2',
    type_symbol='Co',
    fract_x=0.279,
    fract_y=0.25,
    fract_z=0.985,
    wyckoff_letter='c',
    adp_iso=0.3,
)
structure.atom_sites.create(
    label='Si',
    type_symbol='Si',
    fract_x=0.094,
    fract_y=0.25,
    fract_z=0.429,
    wyckoff_letter='c',
    adp_iso=0.34,
)
structure.atom_sites.create(
    label='O1',
    type_symbol='O',
    fract_x=0.091,
    fract_y=0.25,
    fract_z=0.771,
    wyckoff_letter='c',
    adp_iso=0.63,
)
structure.atom_sites.create(
    label='O2',
    type_symbol='O',
    fract_x=0.448,
    fract_y=0.25,
    fract_z=0.217,
    wyckoff_letter='c',
    adp_iso=0.59,
)
structure.atom_sites.create(
    label='O3',
    type_symbol='O',
    fract_x=0.164,
    fract_y=0.032,
    fract_z=0.28,
    wyckoff_letter='d',
    adp_iso=0.83,
)

# %% [markdown]
# ## Step 3: Define Template Experiment
#
# For sequential fitting, we create a single template experiment from
# the first data file. This template defines the instrument, peak
# profile, background, and linked phases that will be reused for every
# data file in the scan.
#
# #### Download Measured Data

# %%
zip_path = ed.download_data(id=27, destination='data')

# %% [markdown]
# #### Extract Data Files

# %%
scan_data_dir = 'experiments/d20_scan'
data_paths = ed.extract_data_paths_from_zip(zip_path, destination=scan_data_dir)

# %% [markdown]
# #### Create Template Experiment from the First File

# %%
project.experiments.add_from_data_path(
    name='d20',
    data_path=data_paths[0],
)
expt = project.experiments['d20']

# %% [markdown]
# #### Set Instrument

# %%
expt.instrument.setup_wavelength = 1.87
expt.instrument.calib_twotheta_offset = 0.29

# %% [markdown]
# #### Set Peak Profile

# %%
expt.peak.broad_gauss_u = 0.24
expt.peak.broad_gauss_v = -0.53
expt.peak.broad_gauss_w = 0.38
expt.peak.broad_lorentz_y = 0.02

# %% [markdown]
# #### Set Excluded Regions

# %%
expt.excluded_regions.create(id='1', start=0, end=8)
expt.excluded_regions.create(id='2', start=150, end=180)

# %% [markdown]
# #### Set Background

# %%
expt.background.create(id='1', x=8, y=609)
expt.background.create(id='2', x=9, y=581)
expt.background.create(id='3', x=10, y=563)
expt.background.create(id='4', x=11, y=540)
expt.background.create(id='5', x=12, y=520)
expt.background.create(id='6', x=15, y=507)
expt.background.create(id='7', x=25, y=463)
expt.background.create(id='8', x=30, y=434)
expt.background.create(id='9', x=50, y=451)
expt.background.create(id='10', x=70, y=431)
expt.background.create(id='11', x=90, y=414)
expt.background.create(id='12', x=110, y=361)
expt.background.create(id='13', x=130, y=292)
expt.background.create(id='14', x=150, y=241)

# %% [markdown]
# #### Set Linked Phases

# %%
expt.linked_phases.create(id='cosio', scale=1.2)

# %% [markdown]
# ## Step 4: Perform Analysis
#
# This section shows how to set free parameters, define constraints,
# and run the sequential refinement.

# %% [markdown]
# #### Set Free Parameters

# %%
structure.cell.length_a.free = True
structure.cell.length_b.free = True
structure.cell.length_c.free = True

structure.atom_sites['Co2'].fract_x.free = True
structure.atom_sites['Co2'].fract_z.free = True
structure.atom_sites['Si'].fract_x.free = True
structure.atom_sites['Si'].fract_z.free = True
structure.atom_sites['O1'].fract_x.free = True
structure.atom_sites['O1'].fract_z.free = True
structure.atom_sites['O2'].fract_x.free = True
structure.atom_sites['O2'].fract_z.free = True
structure.atom_sites['O3'].fract_x.free = True
structure.atom_sites['O3'].fract_y.free = True
structure.atom_sites['O3'].fract_z.free = True

structure.atom_sites['Co1'].adp_iso.free = True
structure.atom_sites['Co2'].adp_iso.free = True
structure.atom_sites['Si'].adp_iso.free = True
structure.atom_sites['O1'].adp_iso.free = True
structure.atom_sites['O2'].adp_iso.free = True
structure.atom_sites['O3'].adp_iso.free = True

# %%
expt.linked_phases['cosio'].scale.free = True

expt.instrument.calib_twotheta_offset.free = True

expt.peak.broad_gauss_u.free = True
expt.peak.broad_gauss_v.free = True
expt.peak.broad_gauss_w.free = True
expt.peak.broad_lorentz_y.free = True

for point in expt.background:
    point.y.free = True

# %% [markdown]
# #### Set Constraints
#
# Set aliases for parameters.

# %%
project.analysis.aliases.create(
    label='biso_Co1',
    param=structure.atom_sites['Co1'].adp_iso,
)
project.analysis.aliases.create(
    label='biso_Co2',
    param=structure.atom_sites['Co2'].adp_iso,
)

# %% [markdown]
# Set constraints.

# %%
project.analysis.constraints.create(expression='biso_Co2 = biso_Co1')

# %% [markdown]
# #### Set Minimizer

# %%
project.analysis.fitting.minimizer_type = 'bumps (lm)'

# %% [markdown]
# #### Run Single Fitting
#
# This is the fitting of the first dataset to optimize the initial
# parameters for the sequential fitting. This step is optional but can
# help with convergence and speed of the sequential fitting, especially
# if the initial parameters are far from optimal.

# %%
project.analysis.fit()

# %% [markdown]
# #### Show parameter correlations

# %%
project.display.fit.correlations()

# %% [markdown]
# #### Compare measured and calculated patterns for the first fit.

# %%
project.display.pattern(expt_name='d20')

# %% [markdown]
# #### Run Sequential Fitting
#
# Set output verbosity level to "short" to show only one-line status
# messages during the analysis process.

# %%
project.verbosity = 'short'

# %% [markdown]
#
# Create a persisted extract rule that reads the temperature from each
# data file.


# %%
temperature = 'diffrn.ambient_temperature'

# %%
project.analysis.sequential_fit_extract.create(
    id='temperature',
    target=temperature,
    pattern=r'^TEMP\s+([0-9.]+)',
    required=True,
)


# %% [markdown]
# Set the sequential fitting parameters.

# %%
project.analysis.fitting_mode_type = 'sequential'
project.analysis.sequential_fit.data_dir = scan_data_dir
project.analysis.sequential_fit.max_workers = 'auto'
project.analysis.sequential_fit.reverse = True

# %% [markdown]
# Run the sequential fit over all data files in the scan directory.

# %%
project.analysis.fit()

# %% [markdown]
# #### Replay a Dataset
#
# Apply fitted parameters from the first CSV row and plot the result.

# %%
project.apply_params_from_csv(row_index=0)
project.display.pattern(expt_name='d20')

# %% [markdown]
#
# Apply fitted parameters from the last CSV row and plot the result.

# %%
project.apply_params_from_csv(row_index=-1)
project.display.pattern(expt_name='d20')

# %% [markdown]
# #### Plot Parameter Evolution
#
# Reuse the extracted diffrn path as the x-axis in the following plots.

# %% [markdown]
# Plot unit cell parameters vs. temperature.

# %%
project.display.fit.series(structure.cell.length_a, versus=temperature)
project.display.fit.series(structure.cell.length_b, versus=temperature)
project.display.fit.series(structure.cell.length_c, versus=temperature)

# %% [markdown]
# Plot isotropic displacement parameters vs. temperature.

# %%
project.display.fit.series(
    structure.atom_sites['Co1'].adp_iso,
    versus=temperature,
)
project.display.fit.series(
    structure.atom_sites['Si'].adp_iso,
    versus=temperature,
)
project.display.fit.series(
    structure.atom_sites['O1'].adp_iso,
    versus=temperature,
)
project.display.fit.series(
    structure.atom_sites['O2'].adp_iso,
    versus=temperature,
)
project.display.fit.series(
    structure.atom_sites['O3'].adp_iso,
    versus=temperature,
)

# %% [markdown]
# Plot selected fractional coordinates vs. temperature.

# %%
project.display.fit.series(
    structure.atom_sites['Co2'].fract_x,
    versus=temperature,
)
project.display.fit.series(
    structure.atom_sites['Co2'].fract_z,
    versus=temperature,
)
project.display.fit.series(
    structure.atom_sites['O1'].fract_z,
    versus=temperature,
)
project.display.fit.series(
    structure.atom_sites['O2'].fract_z,
    versus=temperature,
)
project.display.fit.series(
    structure.atom_sites['O3'].fract_z,
    versus=temperature,
)
