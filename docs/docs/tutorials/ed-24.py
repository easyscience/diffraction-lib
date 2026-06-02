# %% [markdown]
# # Bayesian Analysis Display (`bumps-dream`): LBCO, HRPT
#
# This tutorial shows how to reopen the Bayesian project created in
# `ed-21.py` and inspect the saved fit results without rerunning DREAM.
#
# The project already contains posterior samples together with cached
# posterior density, pair, and predictive data, so the plots below are
# restored directly from disk.

# %% [markdown]
# ## 🛠️ Import Library

# %%
import easydiffraction as ed

# %% [markdown]
# ## 📂 Load Project

# %% [markdown]
# ### Download Project
#
# The returned path points directly to the saved project directory with
# the completed Bayesian fit and persisted posterior samples and plot
# caches.

# %%
project_dir = ed.download_data(id=39, destination='projects')

# %% [markdown]
# ### Load Project
#
# Loading restores the persisted fit state, posterior samples, and plot
# caches. No new fit is launched in this tutorial.

# %%
project = ed.Project.load(project_dir)

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
