# %% [markdown]
# # Bayesian Analysis with emcee: LBCO, HRPT
#
# This tutorial demonstrates how to run Bayesian sampling with the
# emcee minimizer and then resume the same chain from the saved project.
#
# The workflow uses the same La0.5Ba0.5CoO3 powder diffraction example
# as the DREAM Bayesian tutorial:
#
# - run a short local refinement,
# - derive finite fit bounds for the sampled parameters,
# - switch to emcee and sample the posterior,
# - save the project with the emcee chain,
# - resume the chain with additional steps,
# - inspect posterior plots after each sampling stage.

# %% [markdown]
# ## Import Library

# %%
import easydiffraction as ed

# %% [markdown]
# ## Create a Project Container
#
# The project is saved before sampling because emcee stores its chain in
# the project's analysis sidecar file.

# %%
project = ed.Project()

# %%
project.save_as('projects/lbco_hrpt_emcee')

# %% [markdown]
# ## Build the Structural Model
#
# Define a compact cubic perovskite model for La0.5Ba0.5CoO3.

# %%
project.structures.create(name='lbco')

# %%
structure = project.structures['lbco']

# %%
structure.space_group.name_h_m = 'P m -3 m'
structure.space_group.it_coordinate_system_code = '1'

# %%
structure.cell.length_a = 3.88

# %%
structure.atom_sites.create(
    label='La',
    type_symbol='La',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    wyckoff_letter='a',
    adp_type='Biso',
    adp_iso=0.5151,
    occupancy=0.5,
)
structure.atom_sites.create(
    label='Ba',
    type_symbol='Ba',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    wyckoff_letter='a',
    adp_type='Biso',
    adp_iso=0.5151,
    occupancy=0.5,
)
structure.atom_sites.create(
    label='Co',
    type_symbol='Co',
    fract_x=0.5,
    fract_y=0.5,
    fract_z=0.5,
    wyckoff_letter='b',
    adp_type='Biso',
    adp_iso=0.2190,
)
structure.atom_sites.create(
    label='O',
    type_symbol='O',
    fract_x=0,
    fract_y=0.5,
    fract_z=0.5,
    wyckoff_letter='c',
    adp_type='Biso',
    adp_iso=1.3916,
)

# %% [markdown]
# ## Define the Diffraction Experiment
#
# Download the HRPT powder pattern, create a neutron powder experiment,
# and set the key instrument, peak-profile, and background values.

# %%
data_path = ed.download_data(id=3, destination='data')

# %%
project.experiments.add_from_data_path(
    name='hrpt',
    data_path=data_path,
    sample_form='powder',
    beam_mode='constant wavelength',
    radiation_probe='neutron',
)

# %%
experiment = project.experiments['hrpt']

# %%
experiment.linked_phases.create(id='lbco', scale=9.1351)

# %%
experiment.instrument.setup_wavelength = 1.494
experiment.instrument.calib_twotheta_offset = 0.0

# %%
experiment.peak.broad_gauss_u = 0.1
experiment.peak.broad_gauss_v = -0.1
experiment.peak.broad_gauss_w = 0.1204
experiment.peak.broad_lorentz_y = 0.0844

# %%
experiment.background.create(id='1', x=10, y=168.5585)
experiment.background.create(id='2', x=30, y=164.3357)
experiment.background.create(id='3', x=50, y=166.8881)
experiment.background.create(id='4', x=110, y=175.4006)

# %%
experiment.excluded_regions.create(id='1', start=0, end=10)
experiment.excluded_regions.create(id='2', start=100, end=180)

# %% [markdown]
# ## Run a Local Refinement First
#
# The local fit provides starting values and uncertainties that are used
# to build finite bounds for emcee.

# %%
structure.cell.length_a.free = True

# %%
experiment.linked_phases['lbco'].scale.free = True
experiment.peak.broad_gauss_u.free = True
experiment.peak.broad_gauss_v.free = True
experiment.instrument.calib_twotheta_offset.free = True

# %%
project.analysis.minimizer.type = 'bumps (lm)'

# %%
project.analysis.fit()

# %%
project.display.fit.results()

# %%
for param in project.free_parameters:
    param.set_fit_bounds_from_uncertainty()

# %%
project.display.parameters.free()

# %% [markdown]
# ## Run emcee Sampling
#
# The sampling settings are intentionally small for tutorial runtime.
# Use more steps and inspect convergence diagnostics for production
# analysis.

# %%
project.analysis.minimizer.type = 'emcee'

# %%
project.analysis.minimizer.sampling_steps = 1000
project.analysis.minimizer.burn_in_steps = 200
project.analysis.minimizer.thinning_interval = 10
project.analysis.minimizer.population_size = 32
project.analysis.minimizer.initialization_method = 'ball'
project.analysis.minimizer.random_seed = 12345

# %%
project.analysis.fit()

# %%
project.display.fit.results()

# %% [markdown]
# ## Inspect the Posterior
#
# The posterior distribution plot shows the sampled marginal
# distributions after the first emcee run.

# %%
project.display.posterior.distribution()

# %% [markdown]
# The posterior predictive plot propagates the sampled parameter
# uncertainty into the calculated diffraction pattern.

# %%
project.display.posterior.predictive(expt_name='hrpt')

# %% [markdown]
# ## Save the Sampled Project
#
# Saving persists both the analysis state and the emcee chain sidecar so
# the same chain can be resumed later.

# %%
project.save()

# %% [markdown]
# ## Resume emcee Sampling
#
# Resume from the saved backend and append 500 more emcee steps to the
# existing chain.

# %%
project.analysis.fit(resume=True, extra_steps=500)

# %%
project.display.fit.results()

# %% [markdown]
# ## Inspect the Resumed Posterior
#
# After resume, the posterior plots use the extended chain.

# %%
project.display.posterior.distribution()

# %%
project.display.posterior.predictive(expt_name='hrpt')
