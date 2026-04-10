# %% [markdown]
# # Structure Refinement: LBCO+Si, McStas
#
# This example demonstrates a Rietveld refinement of La0.5Ba0.5CoO3
# crystal structure with a small amount of Si phase using time-of-flight
# neutron powder diffraction data simulated with McStas.

# %% [markdown]
# ## Import Library

# %%
from easydiffraction import ExperimentFactory
from easydiffraction import Project
from easydiffraction import StructureFactory
from easydiffraction import download_data

# %% [markdown]
# ## Define Structures
#
# This section shows how to add structures and modify their
# parameters.
#
# ### Create Structure 1: LBCO

# %%
structure_1 = StructureFactory.from_scratch(name='lbco')

# %% [markdown]
# #### Set Space Group

# %%
structure_1.space_group.name_h_m = 'P m -3 m'
structure_1.space_group.it_coordinate_system_code = '1'

# %% [markdown]
# #### Set Unit Cell

# %%
structure_1.cell.length_a = 3.8909

# %% [markdown]
# #### Set Atom Sites

# %%
structure_1.atom_sites.create(
    label='La',
    type_symbol='La',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    wyckoff_letter='a',
    b_iso=0.2,
    occupancy=0.5,
)
structure_1.atom_sites.create(
    label='Ba',
    type_symbol='Ba',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    wyckoff_letter='a',
    b_iso=0.2,
    occupancy=0.5,
)
structure_1.atom_sites.create(
    label='Co',
    type_symbol='Co',
    fract_x=0.5,
    fract_y=0.5,
    fract_z=0.5,
    wyckoff_letter='b',
    b_iso=0.2567,
)
structure_1.atom_sites.create(
    label='O',
    type_symbol='O',
    fract_x=0,
    fract_y=0.5,
    fract_z=0.5,
    wyckoff_letter='c',
    b_iso=1.4041,
)

# %% [markdown]
# ### Create Structure 2: Si

# %%
structure_2 = StructureFactory.from_scratch(name='si')

# %% [markdown]
# #### Set Space Group

# %%
structure_2.space_group.name_h_m = 'F d -3 m'
structure_2.space_group.it_coordinate_system_code = '2'

# %% [markdown]
# #### Set Unit Cell

# %%
structure_2.cell.length_a = 5.43146

# %% [markdown]
# #### Set Atom Sites

# %%
structure_2.atom_sites.create(
    label='Si',
    type_symbol='Si',
    fract_x=0.0,
    fract_y=0.0,
    fract_z=0.0,
    wyckoff_letter='a',
    b_iso=0.0,
)

# %% [markdown]
# ## Define Experiment
#
# This section shows how to add experiments, configure their parameters,
# and link the structures defined in the previous step.
#
# #### Download Data

# %%
data_path = download_data(id=8, destination='data')

# %% [markdown]
# #### Create Experiment

# %%
experiment = ExperimentFactory.from_data_path(
    name='mcstas',
    data_path=data_path,
    sample_form='powder',
    beam_mode='time-of-flight',
    radiation_probe='neutron',
    scattering_type='bragg',
)

# %% [markdown]
# #### Set Instrument

# %%
experiment.instrument.setup_twotheta_bank = 94.90931761529106
experiment.instrument.calib_d_to_tof_offset = 0.0
experiment.instrument.calib_d_to_tof_linear = 58724.76869981215
experiment.instrument.calib_d_to_tof_quad = -0.00001

# %% [markdown]
# #### Set Peak Profile

# %%
# experiment.peak_profile_type = 'jorgensen'
experiment.peak.broad_gauss_sigma_0 = 45137
experiment.peak.broad_gauss_sigma_1 = -52394
experiment.peak.broad_gauss_sigma_2 = 22998
experiment.peak.exp_decay_beta_0 = 0.0055
experiment.peak.exp_decay_beta_1 = 0.0041
experiment.peak.exp_rise_alpha_0 = 0
experiment.peak.exp_rise_alpha_1 = 0.0097

# %% [markdown]
# #### Set Background

# %% [markdown]
# Select the background type.

# %%
experiment.background_type = 'line-segment'

# %% [markdown]
# Add background points.

# %%
experiment.background.create(id='1', x=45000, y=0.2)
experiment.background.create(id='2', x=50000, y=0.2)
experiment.background.create(id='3', x=55000, y=0.2)
experiment.background.create(id='4', x=65000, y=0.2)
experiment.background.create(id='5', x=70000, y=0.2)
experiment.background.create(id='6', x=75000, y=0.2)
experiment.background.create(id='7', x=80000, y=0.2)
experiment.background.create(id='8', x=85000, y=0.2)
experiment.background.create(id='9', x=90000, y=0.2)
experiment.background.create(id='10', x=95000, y=0.2)
experiment.background.create(id='11', x=100000, y=0.2)
experiment.background.create(id='12', x=105000, y=0.2)
experiment.background.create(id='13', x=110000, y=0.2)

# %% [markdown]
# #### Set Linked Phases

# %%
experiment.linked_phases.create(id='lbco', scale=4.0)
experiment.linked_phases.create(id='si', scale=0.2)

# %% [markdown]
# ## Define Project
#
# The project object is used to manage structures, experiments, and
# analysis.
#
# #### Create Project

# %%
project = Project()

# %% [markdown]
# #### Add Structures

# %%
project.structures.add(structure_1)
project.structures.add(structure_2)

# %% [markdown]
# #### Show Structures

# %%
project.structures.show_names()

# %% [markdown]
# #### Add Experiments

# %%
project.experiments.add(experiment)

# %% [markdown]
# #### Set Excluded Regions
#
# Show measured data as loaded from the file.

# %%
project.plotter.plot_meas(expt_name='mcstas')

# %% [markdown]
# Add excluded regions.

# %%
experiment.excluded_regions.create(id='1', start=0, end=40000)
experiment.excluded_regions.create(id='2', start=108000, end=200000)

# %% [markdown]
# Show excluded regions.

# %%
experiment.excluded_regions.show()

# %% [markdown]
# Show measured data after adding excluded regions.

# %%
project.plotter.plot_meas(expt_name='mcstas')

# %% [markdown]
# Show experiment as CIF.

# %%
project.experiments['mcstas'].show_as_cif()

# %% [markdown]
# ## Perform Analysis
#
# This section outlines the analysis process, including how to configure
# calculation and fitting engines.
#
# #### Set Minimizer

# %%
project.analysis.current_minimizer = 'lmfit'

# %% [markdown]
# #### Set Fitting Parameters
#
# Set structure parameters to be optimized.

# %%
structure_1.cell.length_a.free = True
structure_1.atom_sites['Co'].b_iso.free = True
structure_1.atom_sites['O'].b_iso.free = True

structure_2.cell.length_a.free = True

# %% [markdown]
# Set experiment parameters to be optimized.

# %%
experiment.linked_phases['lbco'].scale.free = True
experiment.linked_phases['si'].scale.free = True

experiment.peak.broad_gauss_sigma_0.free = True
experiment.peak.broad_gauss_sigma_1.free = True
experiment.peak.broad_gauss_sigma_2.free = True

experiment.peak.exp_rise_alpha_1.free = True
experiment.peak.exp_decay_beta_0.free = True
experiment.peak.exp_decay_beta_1.free = True

for point in experiment.background:
    point.y.free = True

# %% [markdown]
# #### Perform Fit

# %%
project.analysis.fit()
project.analysis.display.fit_results()

# %% [markdown]
# #### Plot Measured vs Calculated

# %%
project.plotter.plot_meas_vs_calc(expt_name='mcstas')

# %%
