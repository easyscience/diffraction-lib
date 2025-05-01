# %% [markdown]
# # Standard diffraction: Si
#
# Standard diffraction analysis of Si after the powder neutron time-of-flight
# diffraction measurement from SEPD at Argone.

# %% [markdown]
# ## Import EasyDiffraction

# %%
from easydiffraction import (
    Project,
    SampleModel,
    Experiment,
    download_from_repository
)

# %% [markdown]
# ## Define Sample Model
#
# This section covers how to add sample models and modify their parameters.
#
# ### Create sample model object

# %%
model = SampleModel('si')

# %% [markdown]
# ### Define space group

# %%
model.space_group.name_h_m = 'F d -3 m'
model.space_group.it_coordinate_system_code = '2'

# %% [markdown]
# ### Define unit cell

# %%
model.cell.length_a = 5.431

# %% [markdown]
# ### Define atom sites

# %%
model.atom_sites.add('Si', 'Si', 0.125, 0.125, 0.125, b_iso=0.5)

# %% [markdown]
# ## Define Experiment
#
# This section teaches how to add experiments, configure their parameters, and
# link to them the sample models defined in the previous step.
#
# ### Download measured data

# %%
download_from_repository('sepd_si.xye',
                         branch='docs',
                         destination='data')

# %% [markdown]
# ### Create experiment object

# %%
expt = Experiment('sepd',
                  beam_mode='time-of-flight',
                  data_path='data/sepd_si.xye')

# %% [markdown]
# ### Define instrument

# %%
expt.instrument.setup_twotheta_bank = 144.845
expt.instrument.calib_d_to_tof_offset = 0.0
expt.instrument.calib_d_to_tof_linear = 7476.91
expt.instrument.calib_d_to_tof_quad = -1.54

# %% [markdown]
# ### Define peak profile

# %%
expt.peak_profile_type = 'pseudo-voigt * ikeda-carpenter'
expt.peak.broad_gauss_sigma_0 = 3.0
expt.peak.broad_gauss_sigma_1 = 40.0
expt.peak.broad_gauss_sigma_2 = 2.0
expt.peak.broad_mix_beta_0 = 0.04221
expt.peak.broad_mix_beta_1 = 0.00946

# %% [markdown]
# ### Define peak asymmetry

# %%
expt.peak.asym_alpha_0 = 0.0
expt.peak.asym_alpha_1 = 0.5971

# %% [markdown]
# ### Define background

# %%
expt.background_type = 'line-segment'
for x in range(0, 35000, 5000):
    expt.background.add(x=x, y=200)

# %% [markdown]
# ### Select linked phase

# %%
expt.linked_phases.add('si', scale=10.0)

# %% [markdown]
# ## Define Project
#
# The project object is used to manage the sample model, experiments, and
# analysis
#
# ### Create project object

# %%
project = Project()

# %% [markdown]
# ### Configure Plotting Engine

# %%
project.plotter.engine = 'plotly'

# %% [markdown]
# ### Add sample model

# %%
project.sample_models.add(model)

# %% [markdown]
# ### Add experiment

# %%
project.experiments.add(expt)

# %% [markdown]
# ## Analysis
#
# This section will guide you through the analysis process, including setting
# up calculators and fitting models.
#
# ### Set calculation engine

# %%
project.analysis.current_calculator = 'cryspy'

# %% [markdown]
# ### Set fitting engine

# %%
project.analysis.current_minimizer = 'lmfit (leastsq)'

# %% [markdown]
# ### Show measured vs calculated

# %%
project.plot_meas_vs_calc(expt_name='sepd',
                          show_residual=True)
project.plot_meas_vs_calc(expt_name='sepd',
                          x_min=23200, x_max=23700,
                          show_residual=True)

# %% [markdown]
# ### Perform Fit 1/5
#
# Set parameters to be fitted

# %%
model.cell.length_a.free = True

expt.linked_phases['si'].scale.free = True
expt.instrument.calib_d_to_tof_offset.free = True

# %% [markdown]
# Show free parameters after selection

# %%
project.analysis.show_free_params()

# %% [markdown]
# #### Start fitting

# %%
project.analysis.fit()

# %% [markdown]
# #### Show fitting results

# %%
project.plot_meas_vs_calc(expt_name='sepd',
                          show_residual=True)
project.plot_meas_vs_calc(expt_name='sepd',
                          x_min=23200, x_max=23700,
                          show_residual=True)

# %% [markdown]
# ### Perform Fit 2/5
#
# Set parameters to be fitted

# %%
for point in expt.background:
    point.y.free = True

# %% [markdown]
# Show free parameters after selection

# %%
project.analysis.show_free_params()

# %% [markdown]
# #### Start fitting

# %%
project.analysis.fit()

# %% [markdown]
# #### Show fitting results

# %%
project.plot_meas_vs_calc(expt_name='sepd',
                          show_residual=True)
project.plot_meas_vs_calc(expt_name='sepd',
                          x_min=23200, x_max=23700,
                          show_residual=True)

# %% [markdown]
# ### Perform Fit 3/5
#
# Fix background points

# %%
for point in expt.background:
    point.y.free = False

# %% [markdown]
# Set parameters to be fitted

# %%
expt.peak.broad_gauss_sigma_0.free = True
expt.peak.broad_gauss_sigma_1.free = True
expt.peak.broad_gauss_sigma_2.free = True

# %% [markdown]
# Show free parameters after selection

# %%
project.analysis.show_free_params()

# %% [markdown]
# #### Start fitting

# %%
project.analysis.fit()

# %% [markdown]
# #### Show fitting results

# %%
project.plot_meas_vs_calc(expt_name='sepd',
                          show_residual=True)
project.plot_meas_vs_calc(expt_name='sepd',
                          x_min=23200, x_max=23700,
                          show_residual=True)

# %% [markdown]
# ### Perform Fit 4/5
#
# Set parameters to be fitted

# %%
model.atom_sites['Si'].b_iso.free = True

# %% [markdown]
# Show free parameters after selection

# %%
project.analysis.show_free_params()

# %% [markdown]
# #### Start fitting

# %%
project.analysis.fit()

# %% [markdown]
# #### Show fitting results

# %%
project.plot_meas_vs_calc(expt_name='sepd',
                          show_residual=True)
project.plot_meas_vs_calc(expt_name='sepd',
                          x_min=23200, x_max=23700,
                          show_residual=True)
