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
# ## 🛠️ Import Library

# %%
import easydiffraction as ed

# %% [markdown]
# ## 📂 Load Project

# %% [markdown]
# ### Locate Project
#
# Download and extract the saved project from the EasyDiffraction data
# repository.

# %%
project_dir = ed.download_data('proj-lbco-hrpt', destination='projects')

# %% [markdown]
# ### Load Project

# %%
project = ed.Project.load(project_dir)

# %% [markdown]
# Re-save the project to a fresh working directory so fitting below
# writes there instead of the bundled read-only copy.

# %%
project.save_as(dir_path='projects/load-and-fit-lbco-hrpt')

# %% [markdown]
# ## 🚀 Perform Analysis

# %% [markdown]
# ### Display Structure

# %%
project.display.structure(struct_name='lbco')

# %% [markdown]
# ### Run Fitting

# %%
project.analysis.fit()

# %% [markdown]
# ### Display Fit Results

# %%
project.display.fit.results()

# %%
project.display.fit.correlations()

# %%
project.display.pattern(expt_name='hrpt')

# %% [markdown]
# ## 💾 Save Project

# %%
project.save_as(dir_path='projects/load-and-fit-lbco-hrpt')
