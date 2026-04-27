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
# ## Import Library

# %%
import easydiffraction as ed

# %% [markdown]
# ## Step 1: Define Project

# %%
# Create minimal project without name and description
project = ed.Project()

# %% [markdown]
# ## Step 2: Define Crystal Structure

# %%
# Download CIF file from repository
structure_path = ed.download_data(id=1, destination='data')

# %%
# Add structure from downloaded CIF
project.structures.add_from_cif_path(structure_path)

# %% [markdown]
# ## Step 3: Define Experiment

# %%
# Download CIF file from repository
expt_path = ed.download_data(id=2, destination='data')

# %%
# Add experiment from downloaded CIF
project.experiments.add_from_cif_path(expt_path)

# %% [markdown]
# ## Step 4: Perform Analysis (no constraints)

# %%
# Start refinement. All parameters, which have standard uncertainties
# in the input CIF files, are refined by default.
project.analysis.fit()

# %%
# Show fit results summary
project.analysis.display.fit_results()

# %%
# Show parameter correlations
project.display.plotter.plot_param_correlations()

# %% [markdown]
# ## Step 5: Perform Analysis (with constraints)

# %%
# As can be seen from the parameter-correlation plot, the isotropic
# displacement parameters of La and Ba are highly correlated. Because
# La and Ba share the same mixed-occupancy site, their contributions to
# the neutron diffraction pattern are difficult to separate, especially
# since their coherent scattering lengths are not very different.
# Therefore, it is necessary to constrain them to be equal. First we
# define aliases and then use them to create a constraint.
project.analysis.aliases.create(
    label='biso_La',
    param=project.structures['lbco'].atom_sites['La'].adp_iso,
)
project.analysis.aliases.create(
    label='biso_Ba',
    param=project.structures['lbco'].atom_sites['Ba'].adp_iso,
)
project.analysis.constraints.create(expression='biso_Ba = biso_La')

# %%
# Start refinement. All parameters, which have standard uncertainties
# in the input CIF files, are refined by default.
project.analysis.fit()

# %%
# Show fit results summary
project.analysis.display.fit_results()

# %%
# Show parameter correlations
project.display.plotter.plot_param_correlations()

# %%
# Show defined experiment names
project.experiments.show_names()

# %%
# Plot measured vs. calculated diffraction patterns
project.display.plotter.plot_meas_vs_calc(expt_name='hrpt', show_residual=True)
