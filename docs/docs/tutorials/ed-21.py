# %% [markdown]
# # Deterministic and Bayesian Refinement: LBCO, HRPT
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
# ## Import Library

# %%
import easydiffraction as ed

# %% [markdown]
# ## Step 1: Create a Project Container
#
# The project object keeps structures, experiments, fit settings, and
# plotting utilities together in a single place. We will build the full
# workflow inside this object.

# %%
project = ed.Project()

# %% [markdown]
# ## Step 2: Build the Structural Model
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
structure.space_group.it_coordinate_system_code = '1'

# %%
structure.cell.length_a = 3.88

# %% [markdown]
# The atom-site definitions below form the starting structural model. The
# parameters are intentionally reasonable rather than fully optimized,
# because the refinement step will improve them.

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
# ## Step 3: Define the Diffraction Experiment
#
# Next we download the measured powder pattern, create a neutron powder
# experiment, and configure the instrument, profile, background, and
# excluded regions.

# %% [markdown]
# #### Download the Measured Data

# %%
data_path = ed.download_data(id=3, destination='data')

# %% [markdown]
# #### Create the Experiment Object

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
# #### Set Instrument and Peak-Profile Parameters
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
# #### Add Background Points and Excluded Regions
#
# The line-segment background is defined by a few anchor points. We also
# exclude regions that are not intended to contribute to the fit.

# %%
experiment.background.create(id='1', x=10, y=168.5585)
experiment.background.create(id='2', x=30, y=164.3357)
experiment.background.create(id='3', x=50, y=166.8881)
experiment.background.create(id='4', x=110, y=175.4006)

# %%
experiment.excluded_regions.create(id='1', start=0, end=10)
experiment.excluded_regions.create(id='2', start=100, end=180)

# %% [markdown]
# #### Link the Structural Phase to the Experiment

# %%
experiment.linked_phases.create(id='lbco', scale=9.1351)

# %% [markdown]
# ## Step 4: Run an Initial Local Refinement
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
experiment.linked_phases['lbco'].scale.free = True
experiment.peak.broad_gauss_u.free = True
experiment.peak.broad_gauss_v.free = True
experiment.instrument.calib_twotheta_offset.free = True

# %% [markdown]
# We choose the BUMPS Levenberg-Marquardt minimizer as a fast local
# optimizer. Its main purpose here is to provide a stable starting point
# and uncertainty estimates for the Bayesian run.

# %%
project.analysis.fit.show_minimizer_types()

# %%
project.analysis.fit.minimizer_type = 'bumps (lm)'

# %%
project.analysis.fit()

# %%
project.analysis.display.fit_results()

# %% [markdown]
# The correlation plot shows how strongly the fitted parameters move
# together in the local refinement. The measured-vs-calculated plots show
# how well the refined model reproduces the data globally and in a zoomed
# region.

# %%
project.display.plotter.plot_param_correlations()

# %%
project.display.plotter.plot_meas_vs_calc(expt_name='hrpt')

# %% [markdown]
# ## Step 5: Prepare for Bayesian Sampling
#
# DREAM requires finite bounds for the free parameters. Instead of
# setting them manually, we derive them from the uncertainties estimated
# in the local refinement.
#
# The helper method `set_fit_bounds_from_uncertainty` centers the bounds
# on the current parameter value and expands them by a chosen multiple of
# the reported uncertainty.
#
# Default `multiplier` is 8 to give a wide range for the sampler to
# explore, but here we use 3 to speed up the tutorial.

# %%
project.analysis.display.free_params()

# %%
for param in project.free_parameters:
    param.set_fit_bounds_from_uncertainty(multiplier=3.5)

# %% [markdown]
# Displaying the free parameters again is a convenient way to confirm
# that the fit bounds have been assigned as expected before launching the
# sampler.

# %%
project.analysis.display.free_params()

# %% [markdown]
# ## Step 6: Configure and Run DREAM
#
# We now switch from the local minimizer to the Bayesian DREAM sampler.
#
# The settings below are intentionally small so the tutorial runs
# quickly. For production analysis you would usually increase the number
# of steps (`steps`) and often the burn-in (`burn`) as well. When
# needed, the DREAM API also lets you tune how chains are initialized
# through the `init` setting. Other sampler settings such as `thin` and
# `pop` can be adjusted  as well, but here we keep them at their
# defaults.
#
# Default `steps` is 1000, which is often need to be increased for a
# real analysis to ensure good convergence and sampling of the posterior
# distribution. Here we use much smaller value to speed up the tutorial,
# but this is not recommended for a real analysis.

# %%
project.analysis.fit.show_minimizer_types()

# %%
project.analysis.fit.minimizer_type = 'bumps (dream)'

# %%
project.analysis.fit.minimizer.steps = 100  # 1000

# %%
project.analysis.fit()

# %% [markdown]
# ## Step 7: Inspect Bayesian Results
#
# The fit-results display now includes sampler settings, convergence
# diagnostics, committed parameter values, and posterior summary
# statistics.

# %%
project.analysis.display.fit_results()

# %% [markdown]
# The correlation and posterior-pair plots are complementary:
#
# - `plot_param_correlations` summarizes pairwise structure in a compact
#   matrix.
# - `plot_posterior_pairs` shows marginal densities on the diagonal and
#   posterior contours off-diagonal.

# %%
project.display.plotter.plot_param_correlations()

# %%
project.display.plotter.plot_posterior_pairs()

# %% [markdown]
# The one-dimensional posterior distributions below make it easier to
# inspect individual parameters in isolation, including asymmetry or
# multimodality.

# %%
for param in project.free_parameters:
    project.display.plotter.plot_param_distribution(param)

# %% [markdown]
# Finally, the posterior predictive plot propagates the sampled parameter
# uncertainty into the calculated diffraction pattern. Comparing this to
# the zoomed measured-vs-calculated view helps assess whether the sampled
# model family explains the data in the region of interest.

# %%
project.display.plotter.plot_posterior_predictive(expt_name='hrpt')

# %% [markdown]
# A final zoomed measured-vs-calculated plot is useful for checking how
# the posterior-supported model behaves in a narrow region of the pattern
# after the Bayesian run.

# %%
project.display.plotter.plot_posterior_predictive(expt_name='hrpt', x_min=92, x_max=93)
