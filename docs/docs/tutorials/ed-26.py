# %% [markdown]
# # Bayesian Analysis Resume (`emcee`): LBCO, HRPT
#
# This tutorial shows how to reopen the Bayesian project created previously,
# inspect the saved fit results and then run more sampling steps to
# extend the existing chain. Resuming only works with EMCEE because the
# current BUMPS-DREAM implementation does not support saving and
# resuming its state.
#
# This workflow is useful when:
# - the initial sampling run has not yet converged and more steps are needed,
# - the initial sampling run has converged but more steps are desired
#   for better posterior resolution,
# - the initial sampling run has converged but the posterior plots have
#   not yet been inspected and the user wants to see the plots before
#   deciding whether to run more steps.
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
# ## Download Saved Project
#
# The returned path points directly to the saved project directory with
# the completed Bayesian fit and persisted posterior samples and plot
# caches.

# %%
project_dir = ed.download_data(id=38, destination='projects')

# %% [markdown]
# ## Load the Saved Bayesian Project
#
# Loading restores the persisted fit state, posterior samples, and plot
# caches. No new fit is launched in this tutorial.

# %%
project = ed.Project.load(project_dir)

# %% [markdown]
# ## View Structure
#
# Render the La0.5Ba0.5CoO3 structure restored from the saved project.

# %%
project.display.structure(struct_name='lbco')

# %% [markdown]
# ## Review the Saved Fit Summary
#
# The fit summary reports the committed point estimate, sampler
# settings, convergence diagnostics, and posterior parameter summaries
# from the saved Bayesian run.

# %%
project.display.fit.results()

# %% [markdown]
# ## Show Correlations
#
# The correlation matrix is restored from the saved project state.

# %%
project.display.fit.correlations()

# %% [markdown]
# ## Inspect Posterior Densities and Pair Structure
#
# The pair plot and one-dimensional posterior distributions now load
# from the persisted caches generated when the Bayesian fit was saved.

# %%
project.display.posterior.pairs()

# %%
project.display.posterior.distribution()

# %% [markdown]
# ## Plot Posterior Predictive Checks
#
# The posterior predictive view reuses the cached predictive summary
# stored in the project rather than recalculating it on first display.
# It overlays the 95% credible interval propagated from the posterior
# samples.

# %%
project.display.posterior.predictive(expt_name='hrpt')

# %% [markdown]
# A zoomed view is useful for checking the propagated uncertainty in a
# narrow region of the diffraction pattern.

# %%
project.display.posterior.predictive(expt_name='hrpt', x_min=92, x_max=93)

# %% [markdown]
# ## Resume emcee Sampling
#
# Resume from the saved backend and append 100 more emcee steps to the
# existing chain. We use only 100 steps here to keep the tutorial fast,
# but in practice you would typically run more steps to ensure
# convergence and better posterior resolution.

# %%
project.analysis.fit(resume=True, extra_steps=100)

# %%
project.display.fit.results()

# %% [markdown]
# ## Inspect the Resumed Posterior
#
# After resume, the posterior plots use the extended chain.

# %%
project.display.posterior.pairs()

# %%
project.display.posterior.distribution()

# %%
project.display.posterior.predictive(expt_name='hrpt', x_min=92, x_max=93)
