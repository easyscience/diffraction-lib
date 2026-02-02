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

# %%
project.plotter.engine = 'plotly'

# %% [markdown]
# ## Step 2: Define Sample Model

# %%
# Download CIF file from repository
model_path = ed.download_data(id=21, destination='data')
# model_path = "data/ed-21.cif"

# %%
project.sample_models.add(cif_path=model_path)

# %%
sample_model = project.sample_models['taurine']

# %%
# sample_model.show_as_cif()

# %% [markdown]
# ## Step 3: Define Experiment

# %%
data_path = ed.download_data(id=22, destination='data')
# data_path = "data/ed-22.xye"

# %%
project.experiments.add(
    name='senju',
    data_path=data_path,
    sample_form='single crystal',
    beam_mode='time-of-flight',
    radiation_probe='neutron',
)

# %%
experiment = project.experiments['senju']  # TODO: <senju (None)>

# %%
experiment.linked_crystal.id = 'taurine'
experiment.linked_crystal.scale = 1.3

# %%
# experiment.instrument.setup_wavelength = 1.5# TODO: Remove in TOF SC
# experiment.instrument.calib_twotheta_offset = 0.6 # TODO: Remove in SC

# %%
experiment.extinction.mosaicity = 1000
experiment.extinction.radius = 1.0

# %% [markdown]
# ## Step 4: Perform Analysis

# %%
project.plot_meas_vs_calc(expt_name='senju', d_spacing=True)

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
project.analysis.show_fit_results()

# %%
# experiment.show_as_cif()

# %%
# project.experiments.show_names()

# %%
project.plot_meas_vs_calc(expt_name='senju', d_spacing=True)

# %% [markdown]
# ## Step 5: Show Project Summary

# %%
project.summary.show_report()
