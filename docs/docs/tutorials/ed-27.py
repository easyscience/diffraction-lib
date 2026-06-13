# %% [markdown]
# # Calculation Without Data: LBCO, CWL
#
# This example shows how to **calculate and plot a diffraction pattern
# without any measured data**. Everything the calculation needs — the
# crystal structure, the instrument, the peak profile, and the
# background — is defined in code, and the pattern is computed over a
# calculation range instead of over loaded data points.
#
# This is useful to preview what a candidate structure should look like,
# to teach, or to generate a synthetic pattern before any measurement
# exists. No data file is downloaded or loaded.
#
# For this example, a constant-wavelength neutron powder experiment for
# La0.5Ba0.5CoO3 is used.

# %% [markdown]
# ## 🛠️ Import Library

# %%
import easydiffraction as ed

# %% [markdown]
# ## 📦 Define Project

# %%
project = ed.Project(name='lbco_simulation')

# %% [markdown]
# ## 🧩 Define Structure

# %% [markdown]
# ### Download CIF file

# %%
structure_path = ed.download_data(id=1, destination='data')

# %% [markdown]
# ### Add Structure from CIF

# %%
project.structures.add_from_cif_path(structure_path)
project.structures.show_names()

structure = project.structures['lbco']

# %% [markdown]
# ### Plot Structure

# %%
project.display.structure(struct_name='lbco')

# %% [markdown]
# ## 🔬 Define Experiment
#
# ### Create Experiment Without Data
#
# Instead of loading a measured data file, the 'virtual' experiment is created
# directly from its type. With no measured scan present, the pattern is
# later computed over the `data_range` defined below.

# %%
project.experiments.create(
    name='sim',
    sample_form='powder',
    beam_mode='constant wavelength',
    radiation_probe='neutron',
)

# %%
experiment = project.experiments['sim']

# %% [markdown]
# ### Set Instrument

# %%
experiment.instrument.setup_wavelength = 1.494

# %% [markdown]
# ### Set Peak Profile

# %%
experiment.peak.broad_gauss_u = 0.1
experiment.peak.broad_gauss_v = -0.1
experiment.peak.broad_gauss_w = 0.1
experiment.peak.broad_lorentz_y = 0.1

# %% [markdown]
# ### Set Background

# %%
experiment.background.create(id='1', position=10, intensity=20)
experiment.background.create(id='2', position=160, intensity=20)

# %% [markdown]
# ### Set Calculation Range
#
# With no measured data, the x-grid to calculate on comes from the
# `data_range` category. It already holds a sensible default window
# derived from the instrument, so the experiment is calculable without
# any setup. Here we change the default window as an example.

# %%
experiment.data_range.two_theta_min = 10.0
experiment.data_range.two_theta_max = 160.0
experiment.data_range.two_theta_inc = 0.05

# %% [markdown]
# ### Set Linked Structures

# %%
experiment.linked_structures.create(structure_id='lbco', scale=10.0)

# %% [markdown]
# ## 🚀 Perform Calculation
#
# ### Display Pattern
#
# Plotting the pattern computes the calculated curve over the
# `data_range` grid and shows a two-panel view: the calculated curve
# with its background on the main panel, plus a Bragg-peaks row. There
# is no measured curve or residual, because there is no measurement.

# %%
project.display.pattern(expt_name='sim')

# %%
project.display.pattern(expt_name='sim', x_min=30, x_max=60)

# %% [markdown]
# ### Modify Parameters and Recalculate

# %%
structure.cell.length_a = 3.6
structure.atom_sites['O'].adp_iso = 1.2
experiment.peak.broad_lorentz_y = 0.9

# %%
project.analysis.calculate()

# %%
project.display.pattern(expt_name='sim', x_min=30, x_max=60)

# %% [markdown]
# ## 💾 Save Project

# %%
project.save_as(dir_path='projects/ed_27_lbco_simulation')
