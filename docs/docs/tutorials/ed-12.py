# %% [markdown]
# # Pair Distribution Function: NaCl, XRD
#
# This example demonstrates a pair distribution function (PDF) analysis
# of NaCl, based on data collected from an X-ray powder diffraction
# experiment.
#
# The dataset is taken from:
# https://github.com/diffpy/add2019-diffpy-cmi/tree/master

# %% [markdown]
# ## 🛠️ Import Library

# %%
import easydiffraction as ed

# %% [markdown]
# ## 📦 Define Project

# %% [markdown]
# ### Create Project

# %%
project = ed.Project()

# %% [markdown]
# ### Set Plotting Engine

# %%
# Keep the auto-selected engine. Alternatively, you can uncomment the
# line below to explicitly set the engine to the required one.
# project.rendering_plot.type = 'plotly'

# %%
# Set global plot range for plots
project.rendering_plot.plotter.x_min = 2.0
project.rendering_plot.plotter.x_max = 30.0

# %% [markdown]
# ### Add Structure

# %%
project.structures.create(name='nacl')

# %%
project.structures['nacl'].space_group.name_h_m = 'F m -3 m'
project.structures['nacl'].space_group.it_coordinate_system_code = '1'
project.structures['nacl'].cell.length_a = 5.62
project.structures['nacl'].atom_sites.create(
    label='Na',
    type_symbol='Na',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    wyckoff_letter='a',
    adp_iso=1.0,
)
project.structures['nacl'].atom_sites.create(
    label='Cl',
    type_symbol='Cl',
    fract_x=0.5,
    fract_y=0.5,
    fract_z=0.5,
    wyckoff_letter='b',
    adp_iso=1.0,
)

# %% [markdown]
# ### Display Structure

# %%
project.display.structure(struct_name='nacl')

# %% [markdown]
# ### Add Experiment

# %%
data_path = ed.download_data(id=4, destination='data')

# %%
project.experiments.add_from_data_path(
    name='xray_pdf',
    data_path=data_path,
    sample_form='powder',
    beam_mode='constant wavelength',
    radiation_probe='xray',
    scattering_type='total',
)

# %%
project.experiments['xray_pdf'].peak.show_supported()

# %%
project.experiments['xray_pdf'].peak.type = 'gaussian-damped-sinc'

# %%
project.experiments['xray_pdf'].peak.damp_q = 0.03
project.experiments['xray_pdf'].peak.broad_q = 0
project.experiments['xray_pdf'].peak.cutoff_q = 21
project.experiments['xray_pdf'].peak.sharp_delta_1 = 0
project.experiments['xray_pdf'].peak.sharp_delta_2 = 5
project.experiments['xray_pdf'].peak.damp_particle_diameter = 0

# %%
project.experiments['xray_pdf'].linked_phases.create(id='nacl', scale=0.5)

# %% [markdown]
# ## 🚀 Perform Analysis

# %% [markdown]
# ### Set Free Parameters

# %%
project.structures['nacl'].cell.length_a.free = True
project.structures['nacl'].atom_sites['Na'].adp_iso.free = True
project.structures['nacl'].atom_sites['Cl'].adp_iso.free = True

# %%
project.experiments['xray_pdf'].linked_phases['nacl'].scale.free = True
project.experiments['xray_pdf'].peak.damp_q.free = True
project.experiments['xray_pdf'].peak.sharp_delta_2.free = True

# %% [markdown]
# ### Run Fitting

# %%
project.analysis.fit()
project.display.fit.results()
project.display.fit.correlations()

# %% [markdown]
# ### Display Pattern

# %%
project.display.pattern(expt_name='xray_pdf')
