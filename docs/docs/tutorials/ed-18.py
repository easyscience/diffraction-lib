# %% [markdown]
# # Load Project and Fit: LBCO, HRPT
#
# This is the most minimal example of using EasyDiffraction. It shows
# how to load a previously saved project from a directory and run
# refinement — all in just a few lines of code.
#
# The project is first created and saved as a setup step (this would
# normally be done once and the directory would already exist on disk).
# Then the saved project is loaded back and fitted.
#
# For details on how to define structures and experiments, see the other
# tutorials.

# %% [markdown]
# ## Import Library

# %%
import easydiffraction as ed

# %% [markdown]
# ## Setup: Create and Save a Project
#
# This step creates a project from CIF files and saves it to a
# directory. In practice, the project directory would already exist
# on disk from a previous session.

# %%
# Create a project from CIF files
project = ed.Project()
project.structures.add_from_cif_path(ed.download_data(id=1, destination='data'))
project.experiments.add_from_cif_path(ed.download_data(id=2, destination='data'))

# %%
project.analysis.aliases.create(
    label='biso_La',
    param=project.structures['lbco'].atom_sites['La'].b_iso,
)
project.analysis.aliases.create(
    label='biso_Ba',
    param=project.structures['lbco'].atom_sites['Ba'].b_iso,
)

project.analysis.aliases.create(
    label='occ_La',
    param=project.structures['lbco'].atom_sites['La'].occupancy,
)
project.analysis.aliases.create(
    label='occ_Ba',
    param=project.structures['lbco'].atom_sites['Ba'].occupancy,
)

project.analysis.constraints.create(expression='biso_Ba = biso_La')
project.analysis.constraints.create(expression='occ_Ba = 1 - occ_La')

project.structures['lbco'].atom_sites['La'].occupancy.free = True

# %%
# Save to a directory
project.save_as('lbco_project')

# %% [markdown]
# ## Step 1: Load Project from Directory

# %%
project = ed.Project.load('lbco_project')

# %% [markdown]
# ## Step 2: Perform Analysis

# %%
project.analysis.fit()

# %%
project.analysis.show_fit_results()

# %%
project.plot_meas_vs_calc(expt_name='hrpt', show_residual=True)

# %% [markdown]
# ## Step 3: Show Project Summary

# %%
project.summary.show_report()
