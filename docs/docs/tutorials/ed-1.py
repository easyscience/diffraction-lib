# %% [markdown]
# # Structure Refinement: LBCO, HRPT
#
# This basic example is designed to show how Rietveld refinement can be
# performed when both the crystal structure and experiment parameters
# are defined using CIF files.
#
# For this example, constant-wavelength neutron powder diffraction data
# for La0.5Ba0.5CoO3 from HRPT at PSI is used.
#
# The example is intended for users who are already familiar with the
# EasyDiffraction library and want to quickly get started with a basic
# refinement.
#
# It is also useful for those who want to see how constraints can be
# applied to highly correlated parameters. For a more detailed
# explanation of the code, please refer to the other tutorials.

# %% [markdown]
# ## 🛠️ Import Library

# %%
import easydiffraction as ed

# %% [markdown]
# ## 📦 Define Project

# %%
# Create a minimal project with a short name
project = ed.Project(name='lbco_hrpt')

# %% [markdown]
# ## 🧩 Define Structure

# %%
# Download CIF file from repository
structure_path = ed.download_data(id=1, destination='data')

# %%
# Add structure from downloaded CIF
project.structures.add_from_cif_path(structure_path)

# %%
# Plot the crystal structure
project.display.structure(struct_name='lbco')

# %% [markdown]
# ## 🔬 Define Experiment

# %%
# Download CIF file from repository
expt_path = ed.download_data(id=2, destination='data')

# %%
# Add experiment from downloaded CIF
project.experiments.add_from_cif_path(expt_path)

# %% [markdown]
# ## 🚀 Perform Analysis

# %% [markdown]
# ### Without Constraints

# %%
# Start refinement. All parameters, which have standard uncertainties
# in the input CIF files, are refined by default.
project.analysis.fit()

# %%
# Show fit results summary
project.display.fit.results()

# %%
# Show parameter correlations
project.display.fit.correlations()

# %% [markdown]
# ### With Constraints

# %%
# As can be seen from the parameter-correlation plot, the isotropic
# displacement parameters of La and Ba are highly correlated. Because
# La and Ba share the same mixed-occupancy site, their contributions to
# the neutron diffraction pattern are difficult to separate, especially
# since their coherent scattering lengths are not very different.
# Therefore, it is necessary to constrain them to be equal. First we
# define aliases and then use them to create a constraint.
project.analysis.aliases.create(
    id='biso_La',
    param=project.structures['lbco'].atom_sites['La'].adp_iso,
)
project.analysis.aliases.create(
    id='biso_Ba',
    param=project.structures['lbco'].atom_sites['Ba'].adp_iso,
)
project.analysis.constraints.create(expression='biso_Ba = biso_La')

# %%
# Start refinement. All parameters, which have standard uncertainties
# in the input CIF files, are refined by default.
project.analysis.fit()

# %%
# Show fit results summary
project.display.fit.results()

# %%
# Show parameter correlations
project.display.fit.correlations()

# %%
# Show defined experiment names
project.experiments.show_names()

# %%
# Plot measured vs. calculated diffraction patterns
project.display.pattern(expt_name='hrpt')

# %% [markdown]
# ## 💾 Save Project

# %%
project.save_as(dir_path='projects/ed_1_lbco_hrpt')
