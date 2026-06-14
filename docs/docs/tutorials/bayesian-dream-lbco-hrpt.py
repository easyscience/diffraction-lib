# %% [markdown]
# # Bayesian Analysis (`bumps-dream`): LBCO, HRPT
#
# This tutorial demonstrates a practical two-stage workflow for powder
# diffraction analysis with EasyDiffraction.
#
# In the first stage, we run a fast local refinement to obtain a sensible
# point estimate and parameter uncertainties. In the second stage, we use
# these refined values to define fit bounds and then sample the posterior
# distribution with DREAM.
#
# The example uses constant-wavelength neutron powder diffraction data
# for La0.5Ba0.5CoO3 measured on HRPT at PSI.
#
# The goal is not only to obtain a good fit, but also to answer Bayesian
# questions such as:
#
# - Which parameter values are most probable?
# - How broad are the credible intervals?
# - Which parameters are strongly correlated?
# - How much uncertainty propagates into the calculated diffraction
#   pattern?

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
#
# Save the project to a directory early on so that you can easily reload
# it later if needed.

# %%
project = ed.Project(name='lbco_hrpt_bumps_dream')

# %%
project.save_as(dir_path='projects/ed_21_lbco_hrpt_bumps_dream')

# %% [markdown]
# ## 🧩 Define Structure
#
# We define a simple cubic perovskite model for LBCO. La and Ba share the
# same crystallographic site with equal occupancy, while Co and O occupy
# the remaining ideal perovskite positions.

# %%
project.structures.create(name='lbco')

# %%
structure = project.structures['lbco']

# %%
structure.space_group.name_h_m = 'P m -3 m'
structure.space_group.coord_system_code = '1'

# %%
structure.cell.length_a = 3.88

# %% [markdown]
# The atom-site definitions below form the starting structural model. The
# parameters are intentionally reasonable rather than fully optimized,
# because the refinement step will improve them.

# %%
structure.atom_sites.create(
    id='La',
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
    id='Ba',
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
    id='Co',
    type_symbol='Co',
    fract_x=0.5,
    fract_y=0.5,
    fract_z=0.5,
    wyckoff_letter='b',
    adp_type='Biso',
    adp_iso=0.2190,
)
structure.atom_sites.create(
    id='O',
    type_symbol='O',
    fract_x=0,
    fract_y=0.5,
    fract_z=0.5,
    wyckoff_letter='c',
    adp_type='Biso',
    adp_iso=1.3916,
)

# %% [markdown]
# With the structural model complete, render it to confirm the perovskite
# framework before configuring the experiment.

# %%
project.display.structure(struct_name='lbco')

# %% [markdown]
# ## 🔬 Define Experiment
#
# Next we download the measured powder pattern, create a neutron powder
# experiment, and configure the instrument, profile, background, and
# excluded regions.

# %% [markdown]
# Download the measured data from the repository. Alternatively, you
# could use your own data file by providing the path to it instead of
# downloading from the repository.

# %%
data_path = ed.download_data('measured/lbco-hrpt', destination='data')

# %% [markdown]
# Create the experiment object and specify the sample form, beam mode,
# and radiation probe.

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

# %% [markdown]
# Link the structural phase to the experiment.

# %%
experiment.linked_structures.create(structure_id='lbco', scale=9.1351)

# %% [markdown]
# Set instrument and peak profile parameters.
#
# These values provide the initial instrument description for the local
# refinement. Later, a subset of them will be refined.

# %%
experiment.instrument.setup_wavelength = 1.494
experiment.instrument.calib_twotheta_offset = 0.0

# %%
experiment.peak.broad_gauss_u = 0.1
experiment.peak.broad_gauss_v = -0.1
experiment.peak.broad_gauss_w = 0.1204
experiment.peak.broad_lorentz_y = 0.0844

# %% [markdown]
# Add background points and excluded regions.
#
# The line-segment background is defined by a few anchor points. We also
# exclude regions that are not intended to contribute to the fit.

# %%
experiment.background.create(id='1', position=10, intensity=168.5585)
experiment.background.create(id='2', position=30, intensity=164.3357)
experiment.background.create(id='3', position=50, intensity=166.8881)
experiment.background.create(id='4', position=110, intensity=175.4006)

# %%
experiment.excluded_regions.create(id='1', start=0, end=10)
experiment.excluded_regions.create(id='2', start=100, end=180)

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
# In this tutorial we refine only a small set of parameters that are easy
# to interpret in the later Bayesian stage.

# %%
structure.cell.length_a.free = True

# %%
experiment.linked_structures['lbco'].scale.free = True
experiment.peak.broad_gauss_u.free = True
experiment.peak.broad_gauss_v.free = True
experiment.instrument.calib_twotheta_offset.free = True

# %% [markdown]
# We choose the BUMPS Levenberg-Marquardt minimizer as a fast local
# optimizer. Its main purpose here is to provide a stable starting point
# and uncertainty estimates for the Bayesian run.

# %%
project.analysis.minimizer.show_supported()

# %%
project.analysis.minimizer.type = 'bumps (lm)'

# %%
project.analysis.fit()

# %%
project.display.fit.results()

# %% [markdown]
# The correlation plot shows how strongly the fitted parameters move
# together in the local refinement. The measured-vs-calculated plots show
# how well the refined model reproduces the data globally and in a zoomed
# region.

# %%
project.display.fit.correlations()

# %%
project.display.pattern(expt_name='hrpt')

# %% [markdown]
# ## 🎲 Prepare Sampling
#
# DREAM requires finite bounds for the free parameters. Instead of
# setting them manually, we derive them from the uncertainties estimated
# in the local refinement.
#
# The helper method `set_fit_bounds_from_uncertainty` centers the bounds
# on the current parameter value and expands them by a chosen multiple of
# the reported uncertainty.
#
# The default `multiplier` is 4. If the local refinement is very tight,
# or if you expect a broader posterior, increase it explicitly.
#
# Show unset fit bounds before setting them from the local refinement uncertainties.

# %%
project.display.parameters.free()

# %% [markdown]
# Set fit bounds for all free parameters using the default multiplier of
# 4. In this tutorial that means the posterior pair plot will later
# refer to a `±4 × uncertainty` region in its title. To use a different
# region, pass another value, for example `multiplier=6`.

# %%
for param in project.free_parameters:
    param.set_fit_bounds_from_uncertainty()

# %% [markdown]
# Displaying the free parameters again is a convenient way to confirm
# that the fit bounds have been assigned as expected before launching the
# sampler.

# %%
project.display.parameters.free()

# %% [markdown]
# ## 🎲 Run Sampling
#
# We now switch from the local minimizer to the Bayesian DREAM sampler.
#
# The settings below are intentionally small so the tutorial runs
# quickly. For production analysis you would usually increase the number
# of steps (`steps`) and often the burn-in (`burn`) as well. When
# needed, the DREAM API also lets you tune how chains are initialized
# through the `init` setting. Other sampler settings such as `thin` and
# `pop` can be adjusted as well. The current EasyDiffraction defaults
# use `steps=3000`, `init='lhs'`, and `parallel=0`, which tells
# BUMPS-DREAM to use all available CPUs for population evaluations.
#
# The `burn` setting is auto-resolved when left unset. With the default
# `steps=3000` this gives `burn=600`, but if you override `steps` and
# keep `burn=None`, the effective burn-in is recomputed automatically.
# Here we use a much smaller step count to keep the tutorial fast, but
# this is not recommended for production analysis.

# %%
project.analysis.minimizer.show_supported()

# %%
project.analysis.minimizer.type = 'bumps (dream)'

# %%
project.analysis.minimizer.sampling_steps = 100  # lower than the default 3000
project.analysis.minimizer.burn_in_steps = 20  # lower than the default 600
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
#   reminds you that the display region follows the `±4 × uncertainty`
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
# Finally, the posterior predictive plot propagates the sampled parameter
# uncertainty into the calculated diffraction pattern. Comparing this to
# the zoomed measured-vs-calculated view helps assess whether the sampled
# model family explains the data in the region of interest.

# %%
project.display.posterior.predictive(expt_name='hrpt')

# %% [markdown]
# A final zoomed measured-vs-calculated plot is useful for checking how
# the posterior-supported model behaves in a narrow region of the pattern
# after the Bayesian run.

# %%
project.display.posterior.predictive(expt_name='hrpt', x_min=92, x_max=93)
