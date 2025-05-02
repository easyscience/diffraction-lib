# %% [markdown]
# # Standard Diffraction: NCAF, TOF NPD
#
# This example demonstrates standard diffraction analysis of Na2Ca3Al2F14 using
# neutron powder diffraction data collected in time-of-flight mode from WISH at
# ISIS.
#
# Only a single dataset from detector banks 5 & 6 is used here.

# %% [markdown]
# ## Import Library

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
# ### Create Sample Model

# %%
model = SampleModel('ncaf')

# %% [markdown]
# ### Set Space Group

# %%
model.space_group.name_h_m = 'I 21 3'
model.space_group.it_coordinate_system_code = '1'

# %% [markdown]
# ### Set Unit Cell

# %%
model.cell.length_a = 10.250256

# %% [markdown]
# ### Set Atom Sites

# %%
model.atom_sites.add('Ca', 'Ca', 0.4661, 0.0, 0.25, wyckoff_letter="b", b_iso=0.9)
model.atom_sites.add('Al', 'Al', 0.25171, 0.25171, 0.25171, wyckoff_letter="a", b_iso=0.66)
model.atom_sites.add('Na', 'Na', 0.08481, 0.08481, 0.08481, wyckoff_letter="a", b_iso=1.9)
model.atom_sites.add('F1', 'F', 0.1375, 0.3053, 0.1195, wyckoff_letter="c", b_iso=0.9)
model.atom_sites.add('F2', 'F', 0.3626, 0.3634, 0.1867, wyckoff_letter="c", b_iso=1.28)
model.atom_sites.add('F3', 'F', 0.4612, 0.4612, 0.4612, wyckoff_letter="a", b_iso=0.79)

# %% [markdown]
# ## Define Experiment
#
# This section shows how to add experiments, configure their parameters, and
# link the sample models defined in the previous step.
#
# ### Download Measured Data

# %%
download_from_repository('wish_ncaf.xye',
                         branch='docs',
                         destination='data')

# %% [markdown]
# ### Create Experiment

# %%
expt = Experiment('wish',
                  beam_mode='time-of-flight',
                  data_path='data/wish_ncaf.xye')

# %% [markdown]
# ### Set Instrument

# %%
expt.instrument.setup_twotheta_bank = 152.827
expt.instrument.calib_d_to_tof_offset = 0.0
expt.instrument.calib_d_to_tof_linear = 20770
expt.instrument.calib_d_to_tof_quad = -1.08308

# %% [markdown]
# ### Set Peak Profile

# %%
expt.peak_profile_type = 'pseudo-voigt * ikeda-carpenter'
expt.peak.broad_gauss_sigma_0 = 0.0
expt.peak.broad_gauss_sigma_1 = 0.0
expt.peak.broad_gauss_sigma_2 = 5.0
expt.peak.broad_mix_beta_0 = 0.01
expt.peak.broad_mix_beta_1 = 0.01

# %% [markdown]
# ### Set Peak Asymmetry

# %%
expt.peak.asym_alpha_0 = 0.0
expt.peak.asym_alpha_1 = 0.1

# %% [markdown]
# ### Set Background

# %%
expt.background_type = 'line-segment'
for x, y in [
    (9162, 465),
    (11136, 593),
    (13313, 497),
    (14906, 546),
    (16454, 533),
    (17352, 496),
    (18743, 428),
    (20179, 452),
    (21368, 397),
    (22176, 468),
    (22827, 477),
    (24644, 380),
    (26439, 381),
    (28257, 378),
    (31196, 343),
    (34034, 328),
    (37265, 310),
    (41214, 323),
    (44827, 283),
    (49830, 273),
    (52905, 257),
    (58204, 260),
    (62916, 261),
    (70186, 262),
    (74204, 262),
    (82103, 268),
    (91958, 268),
    (102712, 262)
]:
    expt.background.add(x, y)

# %% [markdown]
# ### Set Linked Phases

# %%
expt.linked_phases.add('ncaf', scale=0.5)

# %% [markdown]
# ## Define Project
#
# The project object is used to manage the sample model, experiments, and
# analysis
#
# ### Create Project

# %%
project = Project()

# %% [markdown]
# ### Set Plotting Engine

# %%
project.plotter.engine = 'plotly'

# %% [markdown]
# ### Add Sample Model

# %%
project.sample_models.add(model)

# %% [markdown]
# ### Add Experiment

# %%
project.experiments.add(expt)

# %% [markdown]
# ## Analysis
#
# This section shows the analysis process, including how to set up
# calculation and fitting engines.
#
# ### Set Calculator

# %%
project.analysis.current_calculator = 'cryspy'

# %% [markdown]
# ### Set Minimizer

# %%
project.analysis.current_minimizer = 'lmfit (leastsq)'

# %% [markdown]
# ### Plot Measured vs Calculated

# %%
project.plot_meas_vs_calc(expt_name='wish',
                          show_residual=True)

# %%
project.plot_meas_vs_calc(expt_name='wish',
                          x_min=37000, x_max=40000,
                          show_residual=True)

# %% [markdown]
# ### Perform Fit 1/5
#
# Set parameters to be refined.

# %%
model.cell.length_a.free = True

expt.instrument.calib_d_to_tof_offset.free = True
expt.linked_phases['ncaf'].scale.free = True

# %% [markdown]
# Show free parameters after selection.

# %%
project.analysis.show_free_params()

# %% [markdown]
# #### Run Fit

# %%
project.analysis.fit()

# %% [markdown]
# ### Plot Measured vs Calculated

# %%
project.plot_meas_vs_calc(expt_name='wish',
                          show_residual=True)

# %%
project.plot_meas_vs_calc(expt_name='wish',
                          x_min=37000, x_max=40000,
                          show_residual=True)

# %% [markdown]
# ### Perform Fit 2/5
#
# Set more parameters to be refined.

# %%
expt.peak.broad_gauss_sigma_2.free = True
expt.peak.broad_mix_beta_0.free = True
expt.peak.broad_mix_beta_1.free = True
expt.peak.asym_alpha_0.free = True
expt.peak.asym_alpha_1.free = True

# %% [markdown]
# Show free parameters after selection.

# %%
project.analysis.show_free_params()

# %% [markdown]
# #### Run Fit

# %%
project.analysis.fit()

# %% [markdown]
# #### Plot Measured vs Calculated

# %%
project.plot_meas_vs_calc(expt_name='wish',
                          show_residual=True)

# %%
project.plot_meas_vs_calc(expt_name='wish',
                          x_min=37000, x_max=40000,
                          show_residual=True)


# %% [markdown]
# ### Perform Fit 3/5
#
# Set more parameters to be refined.

# %%
model.atom_sites['Ca'].fract_x.free = True
model.atom_sites['Al'].fract_x.free = True
model.atom_sites['Na'].fract_x.free = True
model.atom_sites['F1'].fract_x.free = True
model.atom_sites['F1'].fract_y.free = True
model.atom_sites['F1'].fract_z.free = True
model.atom_sites['F2'].fract_x.free = True
model.atom_sites['F2'].fract_y.free = True
model.atom_sites['F2'].fract_z.free = True
model.atom_sites['F3'].fract_x.free = True

# %% [markdown]
# Show free parameters after selection.

# %%
project.analysis.show_free_params()

# %% [markdown]
# #### Run Fit

# %%
project.analysis.fit()

# %% [markdown]
# #### Plot Measured vs Calculated

# %%
project.plot_meas_vs_calc(expt_name='wish',
                          show_residual=True)

# %%
project.plot_meas_vs_calc(expt_name='wish',
                          x_min=37000, x_max=40000,
                          show_residual=True)

# %% [markdown]
# ### Perform Fit 4/5
#
# Set more parameters to be refined.

# %%
expt.instrument.calib_d_to_tof_linear.free = True

model.atom_sites['Ca'].b_iso.free = True
model.atom_sites['Al'].b_iso.free = True
model.atom_sites['Na'].b_iso.free = True
model.atom_sites['F1'].b_iso.free = True
model.atom_sites['F2'].b_iso.free = True
model.atom_sites['F3'].b_iso.free = True

# %% [markdown]
# Show free parameters after selection.

# %%
project.analysis.show_free_params()

# %% [markdown]
# #### Run Fit

# %%
project.analysis.fit()

# %% [markdown]
# #### Plot Measured vs Calculated

# %%
project.plot_meas_vs_calc(expt_name='wish',
                          show_residual=True)

# %%
project.plot_meas_vs_calc(expt_name='wish',
                          x_min=37000, x_max=40000,
                          show_residual=True)

# %% [markdown]
# ## Summary
#
# This final section shows how to review the results of the analysis.

# %% [markdown]
# ### Show Project Summary Report

# %%
project.summary.show_report()