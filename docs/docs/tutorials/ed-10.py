# %% [markdown]
# # Pair Distribution Function: Ni, NPD
#
# This example demonstrates a pair distribution function (PDF) analysis
# of Ni, based on data collected from a constant wavelength neutron
# powder diffraction experiment.
#
# The dataset is taken from:
# https://github.com/diffpy/cmi_exchange/tree/main/cmi_scripts/fitNiPDF

# %% [markdown]
# ## 🛠️ Import Library

# %%
import easydiffraction as ed

# %% [markdown]
# ## 📦 Define Project

# %% [markdown]
# ### Create Project

# %%
project = ed.Project(name='ni_pdf')

# %% [markdown]
# ### Add Structure

# %%
project.structures.create(name='ni')

# %%
project.structures['ni'].space_group.name_h_m = 'F m -3 m'
project.structures['ni'].space_group.it_coordinate_system_code = '1'
project.structures['ni'].cell.length_a = 3.52387
project.structures['ni'].atom_sites.create(
    id='Ni',
    type_symbol='Ni',
    fract_x=0.0,
    fract_y=0.0,
    fract_z=0.0,
    adp_iso=0.5,
)

# %% [markdown]
# ### Display Structure

# %%
project.display.structure(struct_name='ni')

# %% [markdown]
# ### Add Experiment

# %%
data_path = ed.download_data(id=6, destination='data')

# %%
project.experiments.add_from_data_path(
    name='pdf',
    data_path=data_path,
    sample_form='powder',
    beam_mode='constant wavelength',
    radiation_probe='neutron',
    scattering_type='total',
)

# %%
project.experiments['pdf'].linked_structures.create(structure_id='ni', scale=1.0)
project.experiments['pdf'].peak.damp_q = 0
project.experiments['pdf'].peak.broad_q = 0.03
project.experiments['pdf'].peak.cutoff_q = 27.0
project.experiments['pdf'].peak.sharp_delta_1 = 0.0
project.experiments['pdf'].peak.sharp_delta_2 = 2.0
project.experiments['pdf'].peak.damp_particle_diameter = 0

# %% [markdown]
# ## 🚀 Perform Analysis

# %% [markdown]
# ### Set Free Parameters

# %%
project.structures['ni'].cell.length_a.free = True
project.structures['ni'].atom_sites['Ni'].adp_iso.free = True

# %%
project.experiments['pdf'].linked_structures['ni'].scale.free = True
project.experiments['pdf'].peak.broad_q.free = True
project.experiments['pdf'].peak.sharp_delta_2.free = True

# %% [markdown]
# ### Run Fitting

# %%
project.analysis.fit()
project.display.fit.results()
project.display.fit.correlations(threshold=0.75)

# %% [markdown]
# ### Display Pattern

# %%
project.display.pattern(expt_name='pdf')

# %% [markdown]
# ## 💾 Save Project

# %%
project.save_as(dir_path='projects/ed_10_ni_pdf')
