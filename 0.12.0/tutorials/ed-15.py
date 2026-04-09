# %% [markdown]
# # Structure Refinement: Taurine, SENJU
#
# Crystal structure refinement of Taurine using time-of-flight single
# crystal neutron diffraction data from SENJU at J-PARC.

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
# ## Step 2: Define Structure

# %%
# Download CIF file from repository
structure_path = ed.download_data(id=21, destination='data')

# %%
project.structures.add_from_cif_path(structure_path)

# %%
project.structures.show_names()

# %%
structure = project.structures['taurine']

# %%
# structure.show_as_cif()

# %% [markdown]
# ## Step 3: Define Experiment

# %%
data_path = ed.download_data(id=22, destination='data')

# %%
project.experiments.add_from_data_path(
    name='senju',
    data_path=data_path,
    sample_form='single crystal',
    beam_mode='time-of-flight',
    radiation_probe='neutron',
)

# %%
experiment = project.experiments['senju']

# %%
experiment.linked_crystal.id = 'taurine'
experiment.linked_crystal.scale = 1.0

# %%
experiment.extinction.mosaicity = 1000.0
experiment.extinction.radius = 100.0

# %% [markdown]
# ## Step 4: Perform Analysis

# %%
project.plotter.plot_meas_vs_calc(expt_name='senju')

# %%
experiment.linked_crystal.scale.free = True
experiment.extinction.radius.free = True

# %%
# experiment.show_as_cif()

# %%
# Start refinement. All parameters, which have standard uncertainties
# in the input CIF files, are refined by default.
project.analysis.fit()

# %%
# Show fit results summary
project.analysis.display.fit_results()

# %%
# experiment.show_as_cif()

# %%
project.experiments.show_names()

# %%
project.plotter.plot_meas_vs_calc(expt_name='senju')

# %% [markdown]
# ## Step 5: Show Project Summary

# %%
project.summary.show_report()
