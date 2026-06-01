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

# %% [markdown]
# ## Download Saved Project

# %%
project_dir = download_data(id=36, destination='projects')

# %% [markdown]
# ## Load Project

# %%
project = Project.load(project_dir)

# %% [markdown]
# ## View Structure

# %%
project.display.structure(struct_name='lbco')

# %% [markdown]
# ## Perform Analysis

# %%
project.analysis.fit()

# %% [markdown]
# ## Show Results

# %%
project.display.fit.results()

# %%
project.display.fit.correlations()

# %%
project.display.pattern(expt_name='hrpt')
