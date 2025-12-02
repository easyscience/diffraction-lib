# %% [markdown]
# # Structure Refinement: LBCO, HRPT
#
# This minimalistic example is designed to be as compact as possible for
# a Rietveld refinement of a crystal structure using constant-wavelength
# neutron powder diffraction data for La0.5Ba0.5CoO3 from HRPT at PSI.
#
# It does not contain any advanced features or options, and includes no
# comments or explanations—these can be found in the other tutorials.
# Default values are used for all parameters if not specified. Only
# essential and self-explanatory code is provided.
#
# The example is intended for users who are already familiar with the
# EasyDiffraction library and want to quickly get started with a simple
# refinement. It is also useful for those who want to see what a
# refinement might look like in code. For a more detailed explanation of
# the code, please refer to the other tutorials.

# %% [markdown]
# ## Import Library

# %%
import easydiffraction as ed

# %%
from easydiffraction.utils.logging import Logger
Logger.configure(
    level=Logger.Level.INFO,
    mode=Logger.Mode.VERBOSE,
    reaction=Logger.Reaction.WARN,
)

# %% [markdown]
# ## Step 1: Define Project

# %%
# Create project without name and description
project = ed.Project()

# %% [markdown]
# ## Step 2: Define Sample Model

# %%
ed.download_from_repository('lbco.cif', destination='data')

# %%
project.sample_models.add(cif_path="data/lbco.cif")

# %%
project.sample_models.show_names()

# %%
# Create an alias for easier access
lbco = project.sample_models['lbco']

# %% [markdown]
# ## Step 3: Define Experiment

# %%
ed.download_from_repository('hrpt_lbco.cif', destination='data')

# %%
project.experiments.add(cif_path="data/hrpt_lbco.cif")

# %%
project.experiments.show_names()

# %%
# Create an alias for easier access
hrpt = project.experiments['hrpt']

# %% [markdown]
# ## Step 4: Perform Analysis

# %%
# Start refinement. All parameters, which have standard uncertainties
# in the input CIF files, are refined by default.
project.analysis.fit()

# %%
project.plot_meas_vs_calc(expt_name='hrpt', show_residual=True)

# %% [markdown]
# #### Step 5: Show Project Summary

# %%
project.summary.show_report()

# %%
