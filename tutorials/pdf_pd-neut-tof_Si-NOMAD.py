# %% [markdown]
# # Pair distribution function: Si
#
# Pair distribution function (PDF) analysis of Si after the powder neutron
# time-of-flight diffraction measurement from NOMAD at SNS.

# %% [markdown]
# ## Import EasyDiffraction

# %%
import easydiffraction as ed

# %% [markdown]
# ## Initialize Project

# %%
project = ed.Project()

# %% [markdown]
# ## Configure Plotting Engine

# %%
project.plotter.engine = 'plotly'
project.plotter.x_max = 40

# %% [markdown]
# ## Define Sample Model

# %%
project.sample_models.add(name='si')

# %%
sample_model = project.sample_models['si']
sample_model.space_group.name_h_m.value = 'F d -3 m'
sample_model.space_group.it_coordinate_system_code = '1'
sample_model.cell.length_a = 5.43146
sample_model.atom_sites.add(label='Si',
                            type_symbol='Si',
                            fract_x=0,
                            fract_y=0,
                            fract_z=0,
                            wyckoff_letter='a',
                            b_iso=0.5)

# %% [markdown]
# ## Define Experiment

# %%
ed.download_from_repository('NOM_9999_Si_640g_PAC_50_ff_ftfrgr_up-to-50.gr',
                            branch='docs',
                            destination='data')

# %%
project.experiments.add(name='nomad',
                        sample_form='powder',
                        beam_mode='time-of-flight',
                        radiation_probe='neutron',
                        scattering_type='total',
                        data_path = 'data/NOM_9999_Si_640g_PAC_50_ff_ftfrgr_up-to-50.gr')

# %%
experiment = project.experiments['nomad']
experiment.linked_phases.add(id='si', scale=1.)
experiment.peak.damp_q = 0.02
experiment.peak.broad_q = 0.03
experiment.peak.cutoff_q = 35.0
experiment.peak.sharp_delta_1 = 0.0
experiment.peak.sharp_delta_2 = 4.0
experiment.peak.damp_particle_diameter = 0

# %% [markdown]
# ## Select Fitting Parameters

# %%
project.sample_models['si'].cell.length_a.free = True
project.sample_models['si'].atom_sites['Si'].b_iso.free = True
experiment.linked_phases['si'].scale.free = True

# %%
experiment.peak.damp_q.free = True
experiment.peak.broad_q.free = True
experiment.peak.sharp_delta_1.free = True
experiment.peak.sharp_delta_2.free = True

# %% [markdown]
# ## Perform Fit

# %%
project.analysis.current_calculator = 'pdffit'
project.analysis.fit()

# %% [markdown]
# ## Plot Measured vs Calculated Data

# %%
project.plot_meas_vs_calc(expt_name='nomad',
                          show_residual=False)
