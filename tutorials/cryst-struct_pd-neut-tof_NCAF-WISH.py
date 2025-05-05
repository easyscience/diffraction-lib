# %% [markdown]
# # Structure Refinement: NCAF, WISH
#
# This example demonstrates a Rietveld refinement of Na2Ca3Al2F14 crystal
# structure using time-of-flight neutron powder diffraction data from WISH at
# ISIS.
#
# Two datasets from detector banks 5_6 and 4_7 are used for joint fitting.

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
model.atom_sites.add('Ca', 'Ca', 0.4665, 0.0, 0.25, wyckoff_letter="b", b_iso=0.92)
model.atom_sites.add('Al', 'Al', 0.2520, 0.2520, 0.2520, wyckoff_letter="a", b_iso=0.73)
model.atom_sites.add('Na', 'Na', 0.0852, 0.0852, 0.0852, wyckoff_letter="a", b_iso=2.08)
model.atom_sites.add('F1', 'F', 0.1376, 0.3055, 0.1196, wyckoff_letter="c", b_iso=0.90)
model.atom_sites.add('F2', 'F', 0.3623, 0.3631, 0.1870, wyckoff_letter="c", b_iso=1.37)
model.atom_sites.add('F3', 'F', 0.4611, 0.4611, 0.4611, wyckoff_letter="a", b_iso=0.88)

# %% [markdown]
# ## Define Experiment
#
# This section shows how to add experiments, configure their parameters, and
# link the sample models defined in the previous step.
#
# ### Download Measured Data

# %%
download_from_repository('wish_ncaf_5_6.xye', branch='docs', destination='data')

# %%
download_from_repository('wish_ncaf_4_7.xye', branch='docs', destination='data')

# %% [markdown]
# ### Create Experiment

# %%
expt56 = Experiment('wish_5_6', beam_mode='time-of-flight', data_path='data/wish_ncaf_5_6.xye')

# %%
expt47 = Experiment('wish_4_7', beam_mode='time-of-flight', data_path='data/wish_ncaf_4_7.xye')

# %% [markdown]
# ### Set Instrument

# %%
expt56.instrument.setup_twotheta_bank = 152.827
expt56.instrument.calib_d_to_tof_offset = -13.0
expt56.instrument.calib_d_to_tof_linear = 20752.1
expt56.instrument.calib_d_to_tof_quad = -1.08308

# %%
expt47.instrument.setup_twotheta_bank = 121.660
expt47.instrument.calib_d_to_tof_offset = -15.0
expt47.instrument.calib_d_to_tof_linear = 18640.7
expt47.instrument.calib_d_to_tof_quad = -0.47488

# %% [markdown]
# ### Set Peak Profile

# %%
expt56.peak.broad_gauss_sigma_0 = 0.0
expt56.peak.broad_gauss_sigma_1 = 0.0
expt56.peak.broad_gauss_sigma_2 = 15.0
expt56.peak.broad_mix_beta_0 = 0.01
expt56.peak.broad_mix_beta_1 = 0.01
expt56.peak.asym_alpha_0 = -0.01
expt56.peak.asym_alpha_1 = 0.10

# %%
expt47.peak.broad_gauss_sigma_0 = 0.0
expt47.peak.broad_gauss_sigma_1 = 30.0
expt47.peak.broad_gauss_sigma_2 = 20.0
expt47.peak.broad_mix_beta_0 = 0.01
expt47.peak.broad_mix_beta_1 = 0.01
expt47.peak.asym_alpha_0 = -0.01
expt47.peak.asym_alpha_1 = 0.10

# %% [markdown]
# ### Set Background

# %%
expt56.background_type = 'line-segment'
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
    expt56.background.add(x, y)

# %%
expt47.background_type = 'line-segment'
for x, y in [
    (9090, 488),
    (10672, 566),
    (12287, 494),
    (14037, 559),
    (15451, 529),
    (16764, 445),
    (18076, 460),
    (19456, 413),
    (20466, 511),
    (21880, 396),
    (23798, 391),
    (25447, 385),
    (28073, 349),
    (30058, 332),
    (32583, 309),
    (34804, 355),
    (37160, 318),
    (40324, 290),
    (46895, 260),
    (50631, 256),
    (54602, 246),
    (58439, 264),
    (66520, 250),
    (75002, 258),
    (83649, 257),
    (92770, 255),
    (101524, 260)
]:
    expt47.background.add(x, y)

# %% [markdown]
# ### Set Linked Phases

# %%
expt56.linked_phases.add('ncaf', scale=1.0)

# %%
expt47.linked_phases.add('ncaf', scale=2.0)

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
project.experiments.add(expt56)
project.experiments.add(expt47)

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
# ### Set Fit Mode

# %%
project.analysis.fit_mode = 'joint'

# %% [markdown]
# ### Plot Measured vs Calculated

# %%
project.plot_meas_vs_calc(expt_name='wish_5_6', show_residual=True)

# %%
project.plot_meas_vs_calc(expt_name='wish_4_7', show_residual=True)

# %% [markdown]
# ### Perform Fit
#
# Set parameters to be refined.

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

model.atom_sites['Ca'].b_iso.free = True
model.atom_sites['Al'].b_iso.free = True
model.atom_sites['Na'].b_iso.free = True
model.atom_sites['F1'].b_iso.free = True
model.atom_sites['F2'].b_iso.free = True
model.atom_sites['F3'].b_iso.free = True

# %%
expt56.linked_phases['ncaf'].scale.free = True
expt56.instrument.calib_d_to_tof_offset.free = True
expt56.instrument.calib_d_to_tof_linear.free = True
expt56.peak.broad_gauss_sigma_2.free = True
expt56.peak.broad_mix_beta_0.free = True
expt56.peak.broad_mix_beta_1.free = True
expt56.peak.asym_alpha_0.free = True
expt56.peak.asym_alpha_1.free = True

expt47.linked_phases['ncaf'].scale.free = True
expt47.instrument.calib_d_to_tof_linear.free = True
expt47.instrument.calib_d_to_tof_offset.free = True
expt47.peak.broad_gauss_sigma_1.free = True
expt47.peak.broad_gauss_sigma_2.free = True
expt47.peak.broad_mix_beta_0.free = True
expt47.peak.broad_mix_beta_1.free = True
expt47.peak.asym_alpha_0.free = True
expt47.peak.asym_alpha_1.free = True

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
project.plot_meas_vs_calc(expt_name='wish_5_6', show_residual=True)

# %%
project.plot_meas_vs_calc(expt_name='wish_4_7', show_residual=True)

# %% [markdown]
# ## Summary
#
# This final section shows how to review the results of the analysis.

# %% [markdown]
# ### Show Project Summary Report

# %%
project.summary.show_report()