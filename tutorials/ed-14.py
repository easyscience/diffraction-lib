# %% [markdown]
# # Structure Refinement: Tb2TiO7, HEiDi
#
# Crystal structure refinement of Tb2TiO7 using single crystal neutron
# diffraction data from HEiDi at FRM II

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
# ## Step 2: Define Sample Model

# %%
# Download CIF file from repository
model_path = ed.download_data(id=20, destination='data')

# %%
project.sample_models.add(cif_path=model_path)

# %% [markdown]
# ## Step 3: Define Experiment

# %%
data_path = ed.download_data(id=19, destination='data')

# %%
project.experiments.add(
    name='heidi',
    data_path=data_path,
    sample_form='single crystal',
    beam_mode='constant wavelength',
    radiation_probe='neutron',
)

# %%
experiment = project.experiments['heidi']  # TODO: <heidi (None)>

# %%
experiment.linked_crystal.id = 'tbti'
experiment.linked_crystal.scale = 10.0

# %%
experiment.instrument.setup_wavelength = 1.494
# experiment.instrument.calib_twotheta_offset = 0.6 # TODO: Remove in SC

# %%
experiment.extinction.mosaicity = 30000
experiment.extinction.radius = 30

# %% [markdown]
# ## Step 4: Perform Analysis

# %%
# Start refinement. All parameters, which have standard uncertainties
# in the input CIF files, are refined by default.
project.analysis.fit()

# %%
# Show fit results summary
# project.analysis.show_fit_results()

# %%
# project.experiments.show_names()

# %%
# project.plot_meas_vs_calc(expt_name='hrpt', show_residual=True)

# %% [markdown]
# ## Step 5: Show Project Summary

# %%
# project.summary.show_report()
