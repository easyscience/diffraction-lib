# %% [markdown]
# # Bayesian Analysis: Tb2TiO7, HEiDi
#
# This tutorial demonstrates a practical two-stage workflow for single-crystal
# diffraction analysis with EasyDiffraction.
#
# In the first stage, we run a fast local refinement to obtain a sensible
# point estimate and parameter uncertainties. In the second stage, we use
# these refined values to define fit bounds and then sample the posterior
# distribution with BUMPS-DREAM.
#
# The example uses constant-wavelength neutron single-crystal diffraction data
# for Tb2TiO7 measured on HEiDi at FRM II.

# %% [markdown]
# ## Import Library

# %%
import easydiffraction as ed

# %% [markdown]
# ## Step 1: Create a Project Container

# %%
project = ed.Project()

# %% [markdown]
# ## Step 2: Build the Structural Model

# %%
structure_path = ed.download_data(id=20, destination='data')

# %%
project.structures.add_from_cif_path(structure_path)

# %%
structure = project.structures['tbti']

# %% [markdown]
# ## Step 3: Define the Diffraction Experiment

# %%
data_path = ed.download_data(id=19, destination='data')

# %%
project.experiments.add_from_data_path(
    name='heidi',
    data_path=data_path,
    sample_form='single crystal',
    beam_mode='constant wavelength',
    radiation_probe='neutron',
)

# %%
experiment = project.experiments['heidi']

# %%
experiment.linked_crystal.id = 'tbti'
experiment.linked_crystal.scale = 1.0

# %%
experiment.instrument.setup_wavelength = 0.793

# %%
experiment.extinction.mosaicity = 35000
experiment.extinction.radius = 10

# %% [markdown]
# ## Step 4: Run an Initial Local Refinement

# %%
structure.atom_sites['O1'].fract_x.free = True

structure.atom_sites['Ti'].occupancy.free = False
structure.atom_sites['O1'].occupancy.free = False
structure.atom_sites['O2'].occupancy.free = False

structure.atom_sites['Tb'].adp_iso.free = True
structure.atom_sites['Ti'].adp_iso.free = True
structure.atom_sites['O1'].adp_iso.free = True
structure.atom_sites['O2'].adp_iso.free = True

# %%
experiment.linked_crystal.scale.free = True
experiment.extinction.radius.free = True

# %%
project.analysis.fit.show_minimizer_types()

# %%
project.analysis.fit()

# %%
project.analysis.display.fit_results()

# %%
project.display.plotter.plot_param_correlations()

# %%
project.display.plotter.plot_meas_vs_calc(expt_name='heidi')

# %% [markdown]
# ## Step 5: Prepare for Bayesian Sampling

# %%
project.analysis.display.free_params()

# %%
for param in project.free_parameters:
    param.set_fit_bounds_from_uncertainty(multiplier=1.5)

# %%
project.analysis.display.free_params()

# %% [markdown]
# ## Step 6: Configure and Run BUMPS-DREAM

# %%
project.analysis.fit.show_minimizer_types()

# %%
project.analysis.fit.minimizer_type = 'bumps (dream)'

# %%
project.analysis.fit.minimizer.steps = 500

# %%
project.analysis.fit()

# %%
project.analysis.display.fit_results()

# %%
project.display.plotter.plot_param_correlations()

# %%
project.display.plotter.plot_posterior_pairs()

# %%
for param in project.free_parameters:
    project.display.plotter.plot_param_distribution(param)

# %%
project.display.plotter.plot_posterior_predictive(expt_name='heidi')
