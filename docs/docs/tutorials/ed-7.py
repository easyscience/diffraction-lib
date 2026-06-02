# %% [markdown]
# # Structure Refinement: Si, SEPD
#
# This example demonstrates a Rietveld refinement of Si crystal
# structure using time-of-flight neutron powder diffraction data from
# SEPD at Argonne.
#
# It also shows how to switch calculation engine and peak profile type.

# %% [markdown]
# ## 🛠️ Import Library

# %%
from easydiffraction import ExperimentFactory
from easydiffraction import Project
from easydiffraction import StructureFactory
from easydiffraction import download_data

# %% [markdown]
# ## 🧩 Define Structure
#
# This section shows how to add structures and modify their
# parameters.
#
# ### Create Structure

# %%
structure = StructureFactory.from_scratch(name='si')

# %% [markdown]
# ### Set Space Group

# %%
structure.space_group.name_h_m = 'F d -3 m'
structure.space_group.it_coordinate_system_code = '2'

# %% [markdown]
# ### Set Unit Cell

# %%
structure.cell.length_a = 5.431

# %% [markdown]
# ### Set Atom Sites

# %%
structure.atom_sites.create(
    label='Si',
    type_symbol='Si',
    fract_x=0.125,
    fract_y=0.125,
    fract_z=0.125,
    adp_iso=0.5,
)

# %% [markdown]
# ## 🔬 Define Experiment
#
# This section shows how to add experiments, configure their
# parameters, and link the structures defined in the previous step.
#
# ### Download Data

# %%
data_path = download_data(id=7, destination='data')

# %% [markdown]
# ### Create Experiment

# %%
expt = ExperimentFactory.from_data_path(
    name='sepd', data_path=data_path, beam_mode='time-of-flight'
)

# %% [markdown]
# ### Set Instrument

# %%
expt.instrument.setup_twotheta_bank = 144.845
expt.instrument.calib_d_to_tof_offset = 0.0
expt.instrument.calib_d_to_tof_linear = 7476.91
expt.instrument.calib_d_to_tof_quad = -1.54

# %% [markdown]
# ### Set Peak Profile

# %%
expt.peak.show_supported()
expt.peak.broad_gauss_sigma_0 = 3.0
expt.peak.broad_gauss_sigma_1 = 40.0
expt.peak.broad_gauss_sigma_2 = 2.0
expt.peak.exp_decay_beta_0 = 0.04221
expt.peak.exp_decay_beta_1 = 0.00946
expt.peak.exp_rise_alpha_0 = 0.0
expt.peak.exp_rise_alpha_1 = 0.5971

# %% [markdown]
# ### Set Background

# %%
expt.background.type = 'line-segment'
for x in range(0, 35000, 5000):
    expt.background.create(id=str(x), x=x, y=200)

# %% [markdown]
# ### Set Linked Phases

# %%
expt.linked_phases.create(id='si', scale=10.0)

# %% [markdown]
# ## 📦 Define Project
#
# The project object is used to manage the structure, experiment, and
# analysis.
#
# ### Create Project

# %%
project = Project()

# %% [markdown]
# ### Add Structure

# %%
project.structures.add(structure)

# %% [markdown]
# ### Add Experiment

# %%
project.experiments.add(expt)

# %% [markdown]
# ## 🚀 Perform Analysis
#
# This section shows the analysis process, including how to set up
# calculation and fitting engines.
#
# ### Display Structure

# %%
project.display.structure(struct_name='si')

# %% [markdown]
# ### Display Pattern

# %%
project.display.pattern(expt_name='sepd')
project.display.pattern(expt_name='sepd', x_min=23200, x_max=23700)

# %% [markdown]
# ### Perform Fit 1/5
#
# Set parameters to be refined.

# %%
structure.cell.length_a.free = True

expt.linked_phases['si'].scale.free = True
expt.instrument.calib_d_to_tof_offset.free = True

# %% [markdown]
# Show free parameters after selection.

# %%
project.display.parameters.free()

# %% [markdown]
# #### Run Fitting

# %%
project.analysis.fit()
project.display.fit.results()

# %% [markdown]
# #### Display Pattern

# %%
project.display.pattern(expt_name='sepd')

# %%
project.display.pattern(expt_name='sepd', x_min=23200, x_max=23700)

# %% [markdown]
# ### Perform Fit 2/5
#
# Set more parameters to be refined.

# %%
for point in expt.background:
    point.y.free = True

# %% [markdown]
# Show free parameters after selection.

# %%
project.display.parameters.free()

# %% [markdown]
# #### Run Fitting

# %%
project.analysis.fit()
project.display.fit.results()

# %% [markdown]
# #### Display Pattern

# %%
project.display.pattern(expt_name='sepd')

# %%
project.display.pattern(expt_name='sepd', x_min=23200, x_max=23700)

# %% [markdown]
# ### Perform Fit 3/5
#
# Fix background points.

# %%
for point in expt.background:
    point.y.free = False

# %% [markdown]
# Set more parameters to be refined.

# %%
expt.peak.broad_gauss_sigma_0.free = True
expt.peak.broad_gauss_sigma_1.free = True
expt.peak.broad_gauss_sigma_2.free = True

# %% [markdown]
# Show free parameters after selection.

# %%
project.display.parameters.free()

# %% [markdown]
# #### Run Fitting

# %%
project.analysis.fit()
project.display.fit.results()

# %% [markdown]
# #### Display Pattern

# %%
project.display.pattern(expt_name='sepd')

# %%
project.display.pattern(expt_name='sepd', x_min=23200, x_max=23700)

# %% [markdown]
# ### Perform Fit 4/5
#
# Set more parameters to be refined.

# %%
structure.atom_sites['Si'].adp_iso.free = True

expt.peak.exp_decay_beta_0.free = True
expt.peak.exp_decay_beta_1.free = True
expt.peak.exp_rise_alpha_1.free = True

# %% [markdown]
# Show free parameters after selection.

# %%
project.display.parameters.free()

# %% [markdown]
# #### Run Fitting

# %%
project.analysis.fit()
project.display.fit.results()

# %% [markdown]
# #### Display Correlations

# %%
project.display.fit.correlations()

# %% [markdown]
# #### Display Pattern

# %%
project.display.pattern(expt_name='sepd')

# %%
project.display.pattern(expt_name='sepd', x_min=23200, x_max=23700)

# %%
project.display.pattern(expt_name='sepd', x='d_spacing')


# %% [markdown]
# ### Perform Fit 5/5
#
# #### Switch calculator engine

# %%
expt.calculator.show_supported()

# %%
expt.calculator.type = 'crysfml'

# %% [markdown]
# #### Change peak profile type

# %%
expt.peak.show_supported()

# %%
expt.peak.type = 'jorgensen-von-dreele'

# %%
expt.peak.broad_gauss_sigma_0 = 3.0148
expt.peak.broad_gauss_sigma_1 = 33.3451
expt.peak.broad_lorentz_gamma_1 = 2.5489
expt.peak.exp_decay_beta_0 = 0.04221
expt.peak.exp_decay_beta_1 = 0.00946
expt.peak.exp_rise_alpha_1 = 0.5971

# %% [markdown]
# #### Add new free parameters

# %%
expt.peak.broad_gauss_sigma_0.free = True
expt.peak.broad_gauss_sigma_1.free = True
expt.peak.broad_lorentz_gamma_1.free = True
expt.peak.exp_decay_beta_0.free = True
expt.peak.exp_decay_beta_1.free = True
expt.peak.exp_rise_alpha_1.free = True

# %% [markdown]
# #### Run Fitting

# %%
project.analysis.fit()
project.display.fit.results()

# %% [markdown]
# #### Display Correlations

# %%
project.display.fit.correlations()

# %% [markdown]
# #### Display Pattern

# %%
project.display.pattern(expt_name='sepd', x_min=23200, x_max=23700)

# %%
project.display.pattern(expt_name='sepd', x='d_spacing')
