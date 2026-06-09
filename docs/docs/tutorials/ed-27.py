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

# %%
project.structures.create(name='lbco')

# %%
structure = project.structures['lbco']

# %%
structure.space_group.name_h_m = 'P m -3 m'
structure.space_group.it_coordinate_system_code = '1'

# %%
structure.cell.length_a = 3.88

# %%
structure.atom_sites.create(
    label='La',
    type_symbol='La',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    adp_iso=0.5,
    occupancy=0.5,
)
structure.atom_sites.create(
    label='Ba',
    type_symbol='Ba',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    adp_iso=0.5,
    occupancy=0.5,
)
structure.atom_sites.create(
    label='Co',
    type_symbol='Co',
    fract_x=0.5,
    fract_y=0.5,
    fract_z=0.5,
    adp_iso=0.5,
)
structure.atom_sites.create(
    label='O',
    type_symbol='O',
    fract_x=0,
    fract_y=0.5,
    fract_z=0.5,
    adp_iso=0.5,
)

# %%
project.display.structure(struct_name='lbco')

# %% [markdown]
# ## 🔬 Define Experiment
#
# ### Create Experiment Without Data
#
# Instead of loading a measured data file, the experiment is created
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
experiment.background.create(id='1', x=10, y=20)
experiment.background.create(id='2', x=160, y=20)

# %% [markdown]
# ### Set Calculation Range
#
# With no measured data, the x-grid to calculate on comes from the
# `data_range` category. It already holds a sensible default window
# derived from the instrument, so the experiment is calculable without
# any setup. Here it is printed and then set explicitly.

# %%
print('Default 2θ range:')
print('  min:', experiment.data_range.two_theta_min.value)
print('  max:', experiment.data_range.two_theta_max.value)
print('  inc:', experiment.data_range.two_theta_inc.value)

# %%
experiment.data_range.two_theta_min = 10.0
experiment.data_range.two_theta_max = 160.0
experiment.data_range.two_theta_inc = 0.05

# %% [markdown]
# ### Set Linked Phases

# %%
experiment.linked_phases.create(id='lbco', scale=10.0)

# %% [markdown]
# ## 🚀 Perform Calculation
#
# ### Display Pattern
#
# Plotting the pattern computes the calculated curve over the
# `data_range` grid and shows it together with the background. There is
# no measured curve or residual, because there is no measurement.

# %%
project.display.pattern(expt_name='sim')

# %%
project.display.pattern(expt_name='sim', x_min=30, x_max=60)

# %% [markdown]
# ### Inspect as CIF
#
# The experiment serialises the calculation range (`data_range`) rather
# than a measured-data loop, so a saved project restores and recomputes
# the same pattern.

# %%
project.experiments['sim'].show_as_cif()

# %% [markdown]
# ## 💾 Save Project

# %%
project.save_as(dir_path='projects/ed_27_lbco_simulation')
