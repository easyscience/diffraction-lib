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
# ## 🛠️ Import Library

# %%
import easydiffraction as ed

# %% [markdown]
# ## 📂 Load Project

# %% [markdown]
# ### Locate Project
#
# Download and extract the saved emcee project, with the persisted chain
# and posterior caches, from the EasyDiffraction data repository.

# %%
project_dir = ed.download_data(id=46, destination='projects')

# %% [markdown]
# ### Load Project
#
# Loading restores the persisted fit state, posterior samples, and plot
# caches. No new fit is launched in this tutorial.

# %%
project = ed.Project.load(project_dir)

# %% [markdown]
# Re-save the project to a fresh working directory so resuming the
# chain below writes there instead of the bundled read-only copy.

# %%
project.save_as(dir_path='projects/ed_26_lbco_hrpt_emcee')

# %% [markdown]
# ## 📊 Inspect Results

# %% [markdown]
# ### Display Structure
#
# Render the La0.5Ba0.5CoO3 structure restored from the saved project.

# %%
project.display.structure(struct_name='lbco')

# %% [markdown]
# ### Display Fit Results
#
# The fit summary reports the committed point estimate, sampler
# settings, convergence diagnostics, and posterior parameter summaries
# from the saved Bayesian run.

# %%
project.display.fit.results()

# %% [markdown]
# ### Display Correlations
#
# The correlation matrix is restored from the saved project state.

# %%
project.display.fit.correlations()

# %% [markdown]
# ### Display Posterior Densities
#
# The pair plot and one-dimensional posterior distributions now load
# from the persisted caches generated when the Bayesian fit was saved.

# %%
project.display.posterior.pairs()

# %%
project.display.posterior.distribution()

# %% [markdown]
# ### Display Posterior Predictive
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
# ## 🎲 Resume Sampling

# %% [markdown]
# ### Run Sampling
#
# Resume from the saved backend and append 100 more emcee steps to the
# existing chain. We use only 100 steps here to keep the tutorial fast,
# but in practice you would typically run more steps to ensure
# convergence and better posterior resolution.

# %%
project.analysis.minimizer.random_seed = 42  # fixed seed for reproducible output
project.analysis.fit(resume=True, extra_steps=100)

# %%
project.display.fit.results()

# %% [markdown]
# ### Display Resumed Posterior
#
# After resume, the posterior plots use the extended chain.

# %%
project.display.posterior.pairs()

# %%
project.display.posterior.distribution()

# %%
project.display.posterior.predictive(expt_name='hrpt', x_min=92, x_max=93)

# %% [markdown]
# ## 💾 Save Project

# %%
project.save_as(dir_path='projects/ed_26_lbco_hrpt_emcee')
