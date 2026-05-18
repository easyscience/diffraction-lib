# %% [markdown]
# # Load Saved Bayesian Project: LBCO, HRPT
#
# This tutorial shows how to reopen the Bayesian project created in
# `ed-21.py` and inspect the saved fit results without rerunning DREAM.
#
# The project already contains posterior samples together with cached
# posterior density, pair, and predictive data, so the plots below are
# restored directly from disk.

# %% [markdown]
# ## Import Library

# %%
from pathlib import Path

import easydiffraction as ed

# %% [markdown]
# ## Locate the Saved Project
#
# In the repository, the saved project currently lives under
# `tmp/tutorials/projects/lbco_hrpt_bayesian`. Once a downloadable
# archive is available, replace this path with the extracted project
# directory instead.

# %%
project_dir = Path('../../../tmp/tutorials/projects/lbco_hrpt_bayesian')

# %%

# %% [markdown]
# ## Load the Saved Bayesian Project
#
# Loading restores the persisted fit state, posterior samples, and plot
# caches. No new fit is launched in this tutorial.

# %%
project = ed.Project.load(project_dir)

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
