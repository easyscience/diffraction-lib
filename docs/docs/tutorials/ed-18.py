# %% [markdown]
# # Load Project and Fit: LBCO, HRPT
#
# This is the most minimal example of using EasyDiffraction. It shows
# how to load a previously saved project from a directory and run
# refinement — all in just a few lines of code.
#
# For details on how to define structures and experiments, see the other
# tutorials.

# %% [markdown]
# ## Import Modules

# %%
from easydiffraction import Project
from easydiffraction import download_data
from easydiffraction import extract_project_from_zip

# %% [markdown]
# ## Download Project Archive

# %%
zip_path = download_data(id=28, destination='data')

# %% [markdown]
# ## Extract Project

# %%
project_dir = extract_project_from_zip('lbco_project.zip', destination='data')

# %% [markdown]
# ## Load Project

# %%
project = Project.load(project_dir)

# %% [markdown]
# ## Perform Analysis

# %%
project.analysis.fit()

# %% [markdown]
# ## Show Results

# %%
project.analysis.show_fit_results()

# %% [markdown]
# ## Plot Meas vs Calc

# %%
project.plot_meas_vs_calc(expt_name='hrpt', show_residual=True)

# %% [markdown]
# ## Save Project

# %%
project.save()
