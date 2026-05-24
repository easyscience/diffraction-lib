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


def normalize_saved_project_selectors(project_dir):
    """Normalize archived project CIF selector tags for the current API."""
    project_path = Path(project_dir)

    replacements_by_file = {
        project_path / 'project.cif': {
            '_rendering.chart_engine': '_chart.type',
            '_rendering.table_engine': '_table.type',
        },
        project_path / 'analysis' / 'analysis.cif': {
            '_fitting.mode_type': '_fitting_mode.type',
            '_fitting.minimizer_type': '_minimizer.type',
        },
        project_path / 'experiments' / 'hrpt.cif': {
            '_calculation.calculator_type': '_calculator.type',
            '_peak.profile_type': '_peak.type',
        },
    }

    for file_path, replacements in replacements_by_file.items():
        text = file_path.read_text(encoding='utf-8')
        for old, new in replacements.items():
            text = text.replace(old, new)
        if file_path.name == 'hrpt.cif' and '_background.type' not in text:
            text = text.replace(
                '\nloop_\n_pd_background.id\n',
                '\n_background.type line-segment\nloop_\n_pd_background.id\n',
            )
        file_path.write_text(text, encoding='utf-8')

# %% [markdown]
# ## Download Saved Project
#
# The returned path points directly to the saved project directory with
# the completed Bayesian fit and persisted posterior samples and plot
# caches.

# %%
project_dir = ed.download_data(id=35, destination='projects')
normalize_saved_project_selectors(project_dir)

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
