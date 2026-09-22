# %% [markdown]
# # Calculation Without Data: NaCl, X-ray
#
# This is the most minimal "calculation without data" example. It
# defines an X-ray powder experiment for NaCl, **accepts the default
# calculation range**, and plots the calculated pattern — no data file
# and no manual range setup.
#
# The default `data_range` is derived from the instrument (here the
# X-ray wavelength), so a structure-only experiment is calculable
# immediately.

# %% [markdown]
# ## 🛠️ Import Library

# %%
import numpy as np

import easydiffraction as edi

# %% [markdown]
# ## 📦 Define Project

# %%
project = edi.Project(name='nacl_simulation')

# %% [markdown]
# ## 🧩 Define Structure

# %%
project.structures.create(name='nacl')

# %%
structure = project.structures['nacl']

# %%
structure.space_group.name_h_m = 'F m -3 m'
structure.space_group.coord_system_code = '1'

# %%
structure.cell.length_a = 5.62

# %%
structure.atom_sites.create(
    id='Na',
    type_symbol='Na',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    adp_iso=0.5,
)
structure.atom_sites.create(
    id='Cl',
    type_symbol='Cl',
    fract_x=0.5,
    fract_y=0.5,
    fract_z=0.5,
    adp_iso=0.5,
)

# %% [markdown]
# ## 🔬 Define Experiment
#
# ### Create Experiment Without Data

# %%
project.experiments.create(
    name='sim',
    sample_form='powder',
    beam_mode='constant wavelength',
    radiation_probe='xray',
)

# %%
experiment = project.experiments['sim']

# %% [markdown]
# ### Set Instrument

# %%
experiment.instrument.setup_wavelength = 1.5406

# %% [markdown]
# ### Set Peak Profile

# %%
experiment.peak.broad_gauss_u = 0.1
experiment.peak.broad_gauss_v = -0.1
experiment.peak.broad_gauss_w = 0.1

# %% [markdown]
# ### Set Linked Structures

# %%
experiment.linked_structures.create(structure_id='nacl', scale=1.0)

# %% [markdown]
# ### Inspect the Default Calculation Range
#
# No range is set explicitly: the default window (derived from the
# wavelength) is used as-is.

# %%
print('min:', experiment.data_range.two_theta_min.value)
print('max:', experiment.data_range.two_theta_max.value)
print('inc:', experiment.data_range.two_theta_inc.value)

# %% [markdown]
# ### Set X-ray Polarization Optics
#
# The polarization coefficient defaults to `0.0`. Setting it to a
# nonzero value includes the Lorentz-polarization optics in the
# calculated X-ray intensities.

# %%
project.analysis.calculate()
unpolarized_intensity = np.asarray(experiment.data.intensity_calc).copy()

# %%
experiment.instrument.setup_polarization_coefficient = 0.5
experiment.instrument.setup_monochromator_twotheta = 26.5650511771

# %%
project.analysis.calculate()
polarized_intensity = np.asarray(experiment.data.intensity_calc).copy()

# %%
print('max intensity change:', np.max(np.abs(polarized_intensity - unpolarized_intensity)))

# %% [markdown]
# ## 🚀 Perform Calculation
#
# ### Display Pattern

# %%
project.display.pattern(expt_name='sim')

# %% [markdown]
# ## 💾 Save Project

# %%
project.save_as(dir_path='projects/simulate-nacl-xray')
