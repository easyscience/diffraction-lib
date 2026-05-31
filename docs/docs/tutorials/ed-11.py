# %% [markdown]
# # Pair Distribution Function: Si, NPD
#
# This example demonstrates a pair distribution function (PDF) analysis
# of Si, based on data collected from a time-of-flight neutron powder
# diffraction experiment at NOMAD at SNS.

# %% [markdown]
# ## Import Library

# %%
import easydiffraction as ed

# %% [markdown]
# ## Create Project

# %%
project = ed.Project()

# %% [markdown]
# ## Set Plotting Engine

# %%
project.rendering_plot.show_supported()

# %%
# Set global plot range for plots
project.rendering_plot.plotter.x_max = 40

# %% [markdown]
# ## Add Structure

# %%
project.structures.create(name='si')

# %%
structure = project.structures['si']
structure.space_group.name_h_m.value = 'F d -3 m'
structure.space_group.it_coordinate_system_code = '1'
structure.cell.length_a = 5.43146
structure.atom_sites.create(
    label='Si',
    type_symbol='Si',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    wyckoff_letter='a',
    adp_iso=0.5,
)

# %% [markdown]
# ## Plot Structure

# %%
project.display.structure(struct_name='si')

# %% [markdown]
# ## Add Experiment

# %%
data_path = ed.download_data(id=5, destination='data')

# %%
project.experiments.add_from_data_path(
    name='nomad',
    data_path=data_path,
    sample_form='powder',
    beam_mode='time-of-flight',
    radiation_probe='neutron',
    scattering_type='total',
)

# %%
experiment = project.experiments['nomad']
experiment.linked_phases.create(id='si', scale=1.0)
experiment.peak.damp_q = 0.02
experiment.peak.broad_q = 0.03
experiment.peak.cutoff_q = 35.0
experiment.peak.sharp_delta_1 = 0.0
experiment.peak.sharp_delta_2 = 4.0
experiment.peak.damp_particle_diameter = 0

# %% [markdown]
# ## Select Fitting Parameters

# %%
project.structures['si'].cell.length_a.free = True
project.structures['si'].atom_sites['Si'].adp_iso.free = True
experiment.linked_phases['si'].scale.free = True

# %%
experiment.peak.damp_q.free = True
experiment.peak.broad_q.free = True
experiment.peak.sharp_delta_1.free = True
experiment.peak.sharp_delta_2.free = True

# %% [markdown]
# ## Run Fitting

# %%
project.analysis.fit()
project.display.fit.results()
project.display.fit.correlations()

# %% [markdown]
# ## Plot Measured vs Calculated

# %%
project.display.pattern(expt_name='nomad', include=('measured', 'calculated'))
