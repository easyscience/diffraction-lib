# %% [markdown]
# # Load Project and Fit: LBCO, HRPT
#
# This is the most minimal example of using EasyDiffraction. It shows
# how to load a previously saved project from a directory and run
# refinement — all in just a few lines of code.
#
# For this example, constant-wavelength neutron powder diffraction data
# for La0.5Ba0.5CoO3 from HRPT at PSI is used.
#
# It does not contain any advanced features or options, and includes no
# comments or explanations — these can be found in the other tutorials.

# %% [markdown]
# ## Import Modules

# %%
from easydiffraction import Project
from easydiffraction import download_data
from easydiffraction import extract_project_from_zip

# %% [markdown]
# ## Download Project Archive

# %%
zip_path = download_data(id=30, destination='data')

# %% [markdown]
# ## Extract Project

# %%
project_dir = extract_project_from_zip(zip_path, destination='data')

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
project.analysis.display.fit_results()

# %% [markdown]
# #### Show parameter correlations

# %%
project.plotter.plot_param_correlations()

# %% [markdown]
# ## Plot Meas vs Calc

# %%
project.plotter.plot_meas_vs_calc(expt_name='hrpt', show_residual=True)
