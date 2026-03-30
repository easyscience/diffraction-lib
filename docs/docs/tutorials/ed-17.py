# %% [markdown]
# # Structure Refinement: Co2SiO4, D20 (Temperature scan)
#
# This example demonstrates a Rietveld refinement of Co2SiO4 crystal
# structure using constant wavelength neutron powder diffraction data
# from D20 at ILL. A sequential refinement of the same structure against
# a temperature scan is performed to show how to manage multiple
# experiments in a project.

# %% [markdown]
# ## Import Library

# %%
import easydiffraction as ed

# %% [markdown]
# ## Step 1: Define Project
#
# The project object is used to manage the structure, experiment, and
# analysis.

# %%
# Create minimal project without name and description
project = ed.Project()

# %% [markdown]
# ## Set Plotting Engine

# %%
# Keep the auto-selected engine. Alternatively, you can uncomment the
# line below to explicitly set the engine to the required one.
# project.plotter.engine = 'plotly'

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
    b_iso=0.3,
)
structure.atom_sites.create(
    label='Co2',
    type_symbol='Co',
    fract_x=0.279,
    fract_y=0.25,
    fract_z=0.985,
    wyckoff_letter='c',
    b_iso=0.3,
)
structure.atom_sites.create(
    label='Si',
    type_symbol='Si',
    fract_x=0.094,
    fract_y=0.25,
    fract_z=0.429,
    wyckoff_letter='c',
    b_iso=0.34,
)
structure.atom_sites.create(
    label='O1',
    type_symbol='O',
    fract_x=0.091,
    fract_y=0.25,
    fract_z=0.771,
    wyckoff_letter='c',
    b_iso=0.63,
)
structure.atom_sites.create(
    label='O2',
    type_symbol='O',
    fract_x=0.448,
    fract_y=0.25,
    fract_z=0.217,
    wyckoff_letter='c',
    b_iso=0.59,
)
structure.atom_sites.create(
    label='O3',
    type_symbol='O',
    fract_x=0.164,
    fract_y=0.032,
    fract_z=0.28,
    wyckoff_letter='d',
    b_iso=0.83,
)

# %% [markdown]
# ## Define Experiment
#
# This section shows how to add experiments, configure their parameters,
# and link the structures defined in the previous step.
#
# #### Download Measured Data

# %%
file_path = ed.download_data(id=25, destination='data')

# %% [markdown]
# #### Create Experiments and Set Temperature

# %%
data_paths = ed.extract_data_paths_from_zip(file_path)
for i, data_path in enumerate(data_paths, start=1):
    name = f'd20_{i}'
    project.experiments.add_from_data_path(name=name, data_path=data_path)
    project.experiments[name].diffrn.ambient_temperature = ed.extract_metadata(
        data_path, r'^TEMP\s+([0-9.]+)'
    )

# %% [markdown]
# #### Set Instrument

# %%
for expt in project.experiments:
    expt.instrument.setup_wavelength = 1.87
    expt.instrument.calib_twotheta_offset = 0.29

# %% [markdown]
# #### Set Peak Profile

# %%
for expt in project.experiments:
    expt.peak.broad_gauss_u = 0.24
    expt.peak.broad_gauss_v = -0.53
    expt.peak.broad_gauss_w = 0.38
    expt.peak.broad_lorentz_y = 0.02

# %% [markdown]
# #### Set Excluded Regions

# %%
for expt in project.experiments:
    expt.excluded_regions.create(id='1', start=0, end=8)
    expt.excluded_regions.create(id='2', start=150, end=180)

# %% [markdown]
# #### Set Background

# %%
for expt in project.experiments:
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
for expt in project.experiments:
    expt.linked_phases.create(id='cosio', scale=1.2)

# %% [markdown]
# ## Perform Analysis
#
# This section shows the analysis process, including how to set up
# calculation and fitting engines.
#
# #### Set Minimizer

# %%
project.analysis.current_minimizer = 'lmfit'

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

structure.atom_sites['Co1'].b_iso.free = True
structure.atom_sites['Co2'].b_iso.free = True
structure.atom_sites['Si'].b_iso.free = True
structure.atom_sites['O1'].b_iso.free = True
structure.atom_sites['O2'].b_iso.free = True
structure.atom_sites['O3'].b_iso.free = True

# %%
for expt in project.experiments:
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
# project.analysis.aliases.create(
#    label='biso_Co1',
#    param_uid=project.structures['cosio'].atom_sites['Co1'].b_iso.uid,
# )
# project.analysis.aliases.create(
#    label='biso_Co2',
#    param_uid=project.structures['cosio'].atom_sites['Co2'].b_iso.uid,
# )

# %% [markdown]
# Set constraints.

# %%
# project.analysis.constraints.create(
#    lhs_alias='biso_Co2',
#    rhs_expr='biso_Co1',
# )

# %% [markdown]
# Apply constraints.

# %%
# project.analysis.apply_constraints()

# %% [markdown]
# #### Set Fit Mode and Weights

# %%
project.analysis.fit_mode.mode = 'single'

# %% [markdown]
# #### Run Fitting

# %%
project.analysis.fit()

# %% [markdown]
# #### Plot Measured vs Calculated

# %%
last_expt_name = project.experiments.names[-1]
project.plot_meas_vs_calc(expt_name=last_expt_name, show_residual=True)

# %% [markdown]
# #### Plot parameters evolution

# %%
print(project.structures['cosio'].cell.length_a.unique_name)

# %%

project.plot_param(structure.cell.length_a, x_axis='temperature')
project.plot_param(structure.cell.length_b, x_axis='temperature')
project.plot_param(structure.cell.length_c, x_axis='temperature')

# %%
print(project.structures['cosio'].atom_sites['O3'].b_iso.unique_name)

# %%
project.plot_param(structure.atom_sites['Co1'].b_iso, x_axis='temperature')
project.plot_param(structure.atom_sites['Co2'].b_iso, x_axis='temperature')
project.plot_param(structure.atom_sites['Si'].b_iso, x_axis='temperature')
project.plot_param(structure.atom_sites['O1'].b_iso, x_axis='temperature')
project.plot_param(structure.atom_sites['O2'].b_iso, x_axis='temperature')
project.plot_param(structure.atom_sites['O3'].b_iso, x_axis='temperature')

# %%
