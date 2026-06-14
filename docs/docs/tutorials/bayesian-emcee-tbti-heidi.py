# %% [markdown]
# # Bayesian Analysis: Tb2TiO7 (`emcee`), HEiDi
#
# This tutorial demonstrates a practical two-stage workflow for single-crystal
# diffraction analysis with EasyDiffraction.
#
# In the first stage, we run a fast local refinement to obtain a sensible
# point estimate and parameter uncertainties. In the second stage, we use
# these refined values to define fit bounds and then sample the posterior
# distribution with emcee.
#
# The example uses constant-wavelength neutron single-crystal diffraction data
# for Tb2TiO7 measured on HEiDi at FRM II.
#
# The goal is not only to obtain a good fit, but also to answer Bayesian
# questions such as:
#
# - Which parameter values are most probable?
# - How broad are the credible intervals?
# - Which parameters are strongly correlated?
# - How much uncertainty propagates into the calculated reflection
#   intensities?

# %% [markdown]
# ## 🛠️ Import Library

# %%
import easydiffraction as ed

# %% [markdown]
# ## 📦 Define Project
#
# The project object keeps structures, experiments, fit settings, and
# plotting utilities together in a single place. We will build the full
# workflow inside this object.

# %%
project = ed.Project(name='tbti_heidi_emcee')

# %%
project.save_as(dir_path='projects/ed_22_tbti_heidi_emcee')

# %% [markdown]
# ## 🧩 Define Structure
#
# For this example we start from a CIF file describing the Tb2TiO7
# pyrochlore structure. Loading the structure from CIF is convenient
# because it preserves a realistic starting
# model without rebuilding the full structure by hand.

# %%
structure_path = ed.download_data('structures/tbti', destination='data')

# %%
project.structures.add_from_cif_path(structure_path)

# %%
structure = project.structures['tbti']

# %% [markdown]
# Render the structure to confirm the pyrochlore model loaded from CIF as
# expected before configuring the experiment.

# %%
project.display.structure(struct_name='tbti')

# %% [markdown]
# ## 🔬 Define Experiment
#
# Next we download the measured reflection data, create a neutron
# single-crystal experiment, and configure the crystal link,
# wavelength, and extinction model.

# %%
data_path = ed.download_data('measured/tbti-heidi', destination='data')

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

# %% [markdown]
# Link the crystal structure to the experiment and set its scale factor.

# %%
experiment.linked_structure.structure_id = 'tbti'
experiment.linked_structure.scale = 1.0

# %% [markdown]
# Set the instrument wavelength and starting extinction parameters.
# These values provide the initial experiment description for the local
# refinement.

# %%
experiment.instrument.setup_wavelength = 0.793

# %%
experiment.extinction.mosaicity = 35000
experiment.extinction.radius = 10

# %% [markdown]
# ## 🚀 Initial Refinement
#
# Before Bayesian sampling, it is useful to run a deterministic fit. This
# gives us:
#
# - a good point estimate near the best-fit region,
# - uncertainties from the local optimizer,
# - a quick check that the model and experiment are configured
#   sensibly.
#
# In this tutorial we refine a small set of structural and extinction
# parameters while keeping occupancies fixed.

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
experiment.linked_structure.scale.free = True
experiment.extinction.radius.free = True

# %% [markdown]
# We keep using the default LMFIT Levenberg-Marquardt minimizer as a fast local
# optimizer. Its main purpose here is to provide a stable starting point
# and uncertainty estimates for the Bayesian run.

# %%
project.analysis.minimizer.show_supported()

# %%
project.analysis.fit()

# %% [markdown]
# The fit-results display summarizes the locally refined values and their
# estimated uncertainties.

# %%
project.display.fit.results()

# %% [markdown]
# The correlation plot shows how strongly the refined parameters move
# together in the local refinement. The measured-vs-calculated plot shows
# how well the refined crystal model reproduces the measured reflection
# intensities.

# %%
project.display.fit.correlations()

# %%
project.display.pattern(expt_name='heidi')

# %% [markdown]
# ## 🎲 Prepare Sampling
#
# Bayesian samplers require finite bounds for the free parameters. Instead of
# setting them manually, we derive them from the uncertainties estimated
# in the local refinement.
#
# The helper method `set_fit_bounds_from_uncertainty` centers the bounds
# on the current parameter value and expands them by a chosen multiple of
# the reported uncertainty.
#
# The default `multiplier` is 4. In this single-crystal tutorial we use
# a tighter value of `1.5` to keep the sampling window closer to the
# locally refined solution.
#
# Show unset fit bounds before setting them from the local refinement
# uncertainties.

# %%
project.display.parameters.free()

# %% [markdown]
# Set fit bounds for all free parameters using `multiplier=1.5`. In this
# tutorial that means the posterior pair plot will later refer to a
# `±1.5 × uncertainty` region in its title. To widen the sampling window,
# increase the multiplier explicitly.

# %%
for param in project.free_parameters:
    param.set_fit_bounds_from_uncertainty(multiplier=1.5)

# %% [markdown]
# Displaying the free parameters again is a convenient way to confirm
# that the fit bounds have been assigned as expected before launching the
# sampler.

# %%
project.display.parameters.free()

# %% [markdown]
# ## 🎲 Run Sampling
#
# We now switch from the local minimizer to the Bayesian emcee sampler.
#
# The settings below are intentionally small so the tutorial runs
# quickly. For production analysis you would usually increase the number
# of steps and often the burn-in as well. emcee also lets you tune how
# walkers are initialized, how many walkers are used, and which proposal
# move drives the ensemble.
#
# The `burn` setting is auto-resolved when left unset. Here we override
# `steps` with a smaller value to keep the tutorial fast, and the
# effective burn-in is recomputed automatically.

# %%
project.analysis.minimizer.show_supported()

# %%
project.analysis.minimizer.type = 'emcee'

# %%
project.analysis.minimizer.sampling_steps = 500  # lower than the default 3000
project.analysis.minimizer.burn_in_steps = 100  # lower than the default 600
project.analysis.minimizer.population_size = 16  # lower than the default 32
project.analysis.minimizer.random_seed = 42  # fixed seed for reproducible output

# %%
project.analysis.fit()

# %% [markdown]
# ## 📊 Inspect Results
#
# The fit-results display now includes sampler settings, convergence
# diagnostics, committed parameter values, and posterior summary
# statistics.

# %%
project.display.fit.results()

# %% [markdown]
# The correlation and posterior-pair plots are complementary:
#
# - `plot_param_correlations` summarizes pairwise structure in a compact
#   matrix.
# - `plot_posterior_pairs` shows marginal densities on the diagonal and
#   posterior contours off-diagonal. In this tutorial its title also
#   reminds you that the display region follows the `±1.5 × uncertainty`
#   bounds defined above, while numeric subplot ranges are omitted to
#   keep the grid readable.

# %%
project.display.fit.correlations()

# %%
project.display.posterior.pairs()

# %% [markdown]
# The one-dimensional posterior distributions below make it easier to
# inspect individual parameters in isolation, including asymmetry or
# multimodality.

# %%
project.display.posterior.distribution()

# %% [markdown]
# Finally, the posterior predictive plot propagates the sampled
# parameter uncertainty into the calculated single-crystal reflection
# intensities.

# %%
project.display.posterior.predictive(expt_name='heidi')
