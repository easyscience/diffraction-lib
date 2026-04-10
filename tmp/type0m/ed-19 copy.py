# %% [markdown]
# # Structure Refinement: CeO2, iMATERIA
#
# This example demonstrates a Rietveld refinement of CeO2 crystal
# structure using time-of-flight neutron powder diffraction data from
# iMATERIA at J-PARC.

# %% [markdown]
# ## Import Library

# %%
import math
from easydiffraction import ExperimentFactory
from easydiffraction import Project
from easydiffraction import StructureFactory

# %% [markdown]
# ## Define Structure
#
# This section shows how to add structures and modify their
# parameters.
#
# #### Create Structure

# %%
structure = StructureFactory.from_scratch(name='ceo2')

# %% [markdown]
# #### Set Space Group

# %%
structure.space_group.name_h_m = 'F m -3 m'
structure.space_group.it_coordinate_system_code = '1'

# %% [markdown]
# #### Set Unit Cell

# %%
structure.cell.length_a = 5.411651

# %% [markdown]
# #### Set Atom Sites

# %%
structure.atom_sites.create(
    label='Ce',
    type_symbol='Ce',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    b_iso=0.258208,
    wyckoff_letter='a',
)
structure.atom_sites.create(
    label='O',
    type_symbol='O',
    fract_x=0.25,
    fract_y=0.25,
    fract_z=0.25,
    b_iso=0.444608,
    wyckoff_letter='c',
)

# %% [markdown]
# ## Define Experiment
#
# This section shows how to add experiments, configure their
# parameters, and link the structures defined in the previous step.
#
# #### Download Measured Data

# %%
# data_path = download_data(id=7, destination='data')
data_path = 'data/MAT005500.SE.bin02Double_0_int_c.histogramIgor'

# %% [markdown]
# #### Create Experiment

# %%
expt = ExperimentFactory.from_data_path(name='se', data_path=data_path, beam_mode='time-of-flight')

# %% [markdown]
# #### Set Linked Phases

# %%
expt.linked_phases.create(id='ceo2', scale=0.015)

# %% [markdown]
# #### Set Instrument

# %%
expt.instrument.setup_twotheta_bank = 90.0
expt.instrument.calib_d_to_tof_offset = -1.894685
expt.instrument.calib_d_to_tof_linear = 10050.037258
expt.instrument.calib_d_to_tof_quad = -0.514363

# %% [markdown]
# #### Set Peak Profile

# %%
expt.peak_profile_type = 'jorgensen'
expt.peak.broad_gauss_sigma_0 = -12
expt.peak.broad_gauss_sigma_1 = 285
expt.peak.broad_gauss_sigma_2 = 29.3
expt.peak.exp_decay_beta_0 = 0.0
expt.peak.exp_decay_beta_1 = 12.8
expt.peak.exp_rise_alpha_0 = 0.0
expt.peak.exp_rise_alpha_1 = 0.27

# %% [markdown]
# #### Set Background

# %%
expt.background_type = 'line-segment'
expt.background.create(id='1', x=3000, y=0.061)
expt.background.create(id='2', x=6000, y=0.0384)
expt.background.create(id='3', x=8000, y=0.0291)
expt.background.create(id='4', x=10000, y=0.0273)
expt.background.create(id='5', x=12000, y=0.0206)
expt.background.create(id='6', x=20000, y=0.0267)
expt.background.create(id='7', x=30000, y=0.0202)
expt.background.create(id='8', x=40000, y=0.0157)

# %% [markdown]
# #### Set Excluded Regions

# %%
expt.excluded_regions.create(id='1', start=0, end=4000)
expt.excluded_regions.create(id='2', start=40015, end=100000)

# %% [markdown]
# ## Define Project
#
# The project object is used to manage the structure, experiment, and
# analysis.
#
# #### Create Project

# %%
project = Project()

# %% [markdown]
# #### Add Structure

# %%
project.structures.add(structure)

# %% [markdown]
# #### Add Experiment

# %%
project.experiments.add(expt)

# %% [markdown]
# ## Perform Analysis
#
# This section shows the analysis process, including how to set up
# calculation and fitting engines.
#
# #### Set Minimizer

# %%
project.analysis.current_minimizer = 'lmfit'

# %% [markdown]
# #### Plot Measured vs Calculated

# %%
#structure.cell.length_a = 5.411651
#expt.instrument.calib_d_to_tof_offset = 7.894685
project.plotter.plot_meas_vs_calc(expt_name='se', show_residual=True)

# %%
project.plotter.plot_meas_vs_calc(expt_name='se', x_min=11000, x_max=11210)

# %% [markdown]
# ### Perform Fit 1/5
#
# Set parameters to be refined.

# %%
structure.cell.length_a.free = True

expt.linked_phases['ceo2'].scale.free = True
expt.instrument.calib_d_to_tof_offset.free = True

for point in expt.background:
    point.y.free = True

expt.peak.broad_gauss_sigma_0.free = True
expt.peak.broad_gauss_sigma_1.free = True
expt.peak.broad_gauss_sigma_2.free = True

expt.peak.exp_decay_beta_1.free = True
expt.peak.exp_rise_alpha_1.free = True

# %% [markdown]
# Show free parameters after selection.

# %%
project.analysis.display.free_params()

# %% [markdown]
# #### Run Fitting

# %%
project.analysis.fit()

# %%
project.analysis.display.fit_results()

# %% [markdown]
# #### Show parameter correlations

# %%
#project.plotter.plot_param_correlations()

# %% [markdown]
# #### Plot Measured vs Calculated

# %%
project.plotter.plot_meas_vs_calc(expt_name='se', show_residual=True)

# %%
project.plotter.plot_meas_vs_calc(expt_name='se', x_min=11000, x_max=11210)

# %% [markdown]
# ### Perform Fit 5/5
#
# Change Peak Profile

# %%
expt.peak_profile_type = 'double-jorgensen-von-dreele'
expt.peak.broad_gauss_sigma_0 = math.sqrt(0.0)
expt.peak.broad_gauss_sigma_1 = math.sqrt(249.608083)
expt.peak.broad_gauss_sigma_2 = math.sqrt(6.660444)
expt.peak.broad_lorentz_gamma_0 = -1.625176
expt.peak.broad_lorentz_gamma_1 = 3.96284
expt.peak.broad_lorentz_gamma_2 = 0.438507
expt.peak.dexp_decay_beta_10 = -0.741805
expt.peak.dexp_decay_beta_00 = 0.445145
expt.peak.dexp_decay_beta_01 = -0.276235
expt.peak.dexp_rise_alpha_1 = -0.5697
expt.peak.dexp_rise_alpha_2 = 0.002
expt.peak.dexp_switch_r_01 = 0.490586
expt.peak.dexp_switch_r_02 = 0.639906
expt.peak.dexp_switch_r_03 = 2.5

expt.peak.broad_gauss_sigma_0.free = True
expt.peak.broad_gauss_sigma_1.free = True
expt.peak.broad_gauss_sigma_2.free = True
expt.peak.broad_lorentz_gamma_0.free = True
expt.peak.broad_lorentz_gamma_1.free = True
expt.peak.broad_lorentz_gamma_2.free = True
expt.peak.dexp_decay_beta_00.free = False
expt.peak.dexp_decay_beta_01.free = False
expt.peak.dexp_decay_beta_10.free = False
expt.peak.dexp_rise_alpha_1.free = False
expt.peak.dexp_rise_alpha_2.free = False
expt.peak.dexp_switch_r_01.free = True
expt.peak.dexp_switch_r_02.free = True
expt.peak.dexp_switch_r_03.free = False


#expt.linked_phases['ceo2'].scale = 0.2

#structure.cell.length_a = 5.4166
#expt.instrument.calib_d_to_tof_offset = -1.6127

#structure.cell.length_a.free = False
#expt.instrument.calib_d_to_tof_offset.free = False

project.plotter.plot_meas_vs_calc(expt_name='se', show_residual=True)

# %%
project.analysis.display.free_params()

# %% [markdown]
# Set more parameters to be refined.

# %%
# structure.atom_sites['Ce'].b_iso.free = True
# structure.atom_sites['O'].b_iso.free = True

# expt.peak.exp_decay_beta_0.free = True
# expt.peak.exp_decay_beta_1.free = True
# expt.peak.exp_rise_alpha_1.free = True

# %% [markdown]
# Show free parameters after selection.

# %%
# project.analysis.display.free_params()

# %%
#project.plotter.plot_meas_vs_calc(expt_name='se', show_residual=True)

# %% [markdown]
# #### Run Fitting

# %%
project.analysis.fit()

# %%
project.analysis.display.fit_results()

# %% [markdown]
# #### Show parameter correlations

# %%
# project.plotter.plot_param_correlations()

# %% [markdown]
# #### Plot Measured vs Calculated

# %%
project.plotter.plot_meas_vs_calc(expt_name='se', show_residual=True)

# %%
project.plotter.plot_meas_vs_calc(expt_name='se', x_min=11000, x_max=11210)

# %%

# %%
# project.plotter.plot_meas_vs_calc(expt_name='se', x='d_spacing', show_residual=True)

# %%
