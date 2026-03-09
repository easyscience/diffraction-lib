# %% [markdown]
# # Structure Refinement: Tb2TiO7, HEiDi
#
# Crystal structure refinement of Tb2TiO7 using single crystal neutron
# diffraction data from HEiDi at FRM II.

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

# %%
project.sample_models.show_names()

# %%
sample_model = project.sample_models['tbti']

# %%
sample_model.atom_sites['Tb'].b_iso.value = 0.0
sample_model.atom_sites['Ti'].b_iso.value = 0.0
sample_model.atom_sites['O1'].b_iso.value = 0.0
sample_model.atom_sites['O2'].b_iso.value = 0.0

# %%
sample_model.show_as_cif()

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
experiment.linked_crystal.scale = 1.0

# %%
experiment.instrument.setup_wavelength = 0.793
# experiment.instrument.calib_twotheta_offset = 0.6 # TODO: Remove in SC

# %%
experiment.extinction.mosaicity = 29820
experiment.extinction.radius = 30

# %% [markdown]
# ## Step 4: Perform Analysis

# %%
project.plot_meas_vs_calc(expt_name='heidi')

# %%
experiment.linked_crystal.scale.free = True
experiment.extinction.radius.free = True

# %%
experiment.show_as_cif()

# %%
# Start refinement. All parameters, which have standard uncertainties
# in the input CIF files, are refined by default.
project.analysis.fit()

# %%
# Show fit results summary
project.analysis.show_fit_results()

# %%
experiment.show_as_cif()

# %%
project.experiments.show_names()

# %%
project.plot_meas_vs_calc(expt_name='heidi')

# %% [markdown]
# ## Step 5: Show Project Summary

# %%
project.summary.show_report()
