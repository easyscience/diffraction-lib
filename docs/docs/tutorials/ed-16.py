# %% [markdown]
# # Joint Refinement: Si, Bragg + PDF
#
# This example demonstrates a joint refinement of the Si crystal
# structure combining Bragg diffraction and pair distribution function
# (PDF) analysis. The Bragg experiment uses time-of-flight neutron
# powder diffraction data from SEPD at Argonne, while the PDF
# experiment uses data from NOMAD at SNS. A single shared Si structure
# is refined simultaneously against both datasets.

# %% [markdown]
# ## Import Library

# %%
from easydiffraction import ExperimentFactory
from easydiffraction import Project
from easydiffraction import StructureFactory
from easydiffraction import download_data

# %% [markdown]
# ## Define Structure
#
# A single Si structure is shared between the Bragg and PDF
# experiments. Structural parameters refined against both datasets
# simultaneously.
#
# #### Create Structure

# %%
structure = StructureFactory.from_scratch(name='si')

# %% [markdown]
# #### Set Space Group

# %%
structure.space_group.name_h_m = 'F d -3 m'
structure.space_group.it_coordinate_system_code = '1'

# %% [markdown]
# #### Set Unit Cell

# %%
structure.cell.length_a = 5.42

# %% [markdown]
# #### Set Atom Sites

# %%
structure.atom_sites.create(
    label='Si',
    type_symbol='Si',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    wyckoff_letter='a',
    b_iso=0.2,
)

# %% [markdown]
# ## Define Experiments
#
# Two experiments are defined: one for Bragg diffraction and one for
# PDF analysis. Both are linked to the same Si structure.
#
# ### Experiment 1: Bragg (SEPD, TOF)
#
# #### Download Data

# %%
bragg_data_path = download_data(id=7, destination='data')

# %% [markdown]
# #### Create Experiment

# %%
bragg_expt = ExperimentFactory.from_data_path(
    name='sepd', data_path=bragg_data_path, beam_mode='time-of-flight'
)

# %% [markdown]
# #### Set Instrument

# %%
bragg_expt.instrument.setup_twotheta_bank = 144.845
bragg_expt.instrument.calib_d_to_tof_offset = -9.2
bragg_expt.instrument.calib_d_to_tof_linear = 7476.91
bragg_expt.instrument.calib_d_to_tof_quad = -1.54

# %% [markdown]
# #### Set Peak Profile

# %%
bragg_expt.peak_profile_type = 'jorgensen'
bragg_expt.peak.broad_gauss_sigma_0 = 5.0
bragg_expt.peak.broad_gauss_sigma_1 = 45.0
bragg_expt.peak.broad_gauss_sigma_2 = 1.0
bragg_expt.peak.exp_decay_beta_0 = 0.04221
bragg_expt.peak.exp_decay_beta_1 = 0.00946
bragg_expt.peak.exp_rise_alpha_0 = 0.0
bragg_expt.peak.exp_rise_alpha_1 = 0.5971

# %% [markdown]
# #### Set Background

# %%
bragg_expt.background_type = 'line-segment'
for x in range(0, 35000, 5000):
    bragg_expt.background.create(id=str(x), x=x, y=200)

# %% [markdown]
# #### Set Linked Phases

# %%
bragg_expt.linked_phases.create(id='si', scale=13.0)

# %% [markdown]
# ### Experiment 2: PDF (NOMAD, TOF)
#
# #### Download Data

# %%
pdf_data_path = download_data(id=5, destination='data')

# %% [markdown]
# #### Create Experiment

# %%
pdf_expt = ExperimentFactory.from_data_path(
    name='nomad',
    data_path=pdf_data_path,
    beam_mode='time-of-flight',
    scattering_type='total',
)

# %% [markdown]
# #### Set Peak Profile (PDF Parameters)

# %%
pdf_expt.peak.damp_q = 0.02
pdf_expt.peak.broad_q = 0.02
pdf_expt.peak.cutoff_q = 35.0
pdf_expt.peak.sharp_delta_1 = 0.001
pdf_expt.peak.sharp_delta_2 = 4.0
pdf_expt.peak.damp_particle_diameter = 0

# %% [markdown]
# #### Set Linked Phases

# %%
pdf_expt.linked_phases.create(id='si', scale=1.0)

# %% [markdown]
# ## Define Project
#
# The project object manages the shared structure, both experiments,
# and the analysis.
#
# #### Create Project

# %%
project = Project()

# %% [markdown]
# #### Add Structure

# %%
project.structures.add(structure)

# %% [markdown]
# #### Add Experiments

# %%
project.experiments.add(bragg_expt)
project.experiments.add(pdf_expt)

# %% [markdown]
# ## Perform Analysis
#
# This section shows the joint analysis process. The calculator is
# auto-resolved per experiment: CrysPy for Bragg, PDFfit for PDF.
#
# #### Set Fit Mode and Weights

# %%
project.analysis.fit_mode.mode = 'joint'
project.analysis.joint_fit_experiments.create(id='sepd', weight=0.7)
project.analysis.joint_fit_experiments.create(id='nomad', weight=0.3)

# %% [markdown]
# #### Set Minimizer

# %%
project.analysis.current_minimizer = 'lmfit'

# %% [markdown]
# #### Plot Measured vs Calculated (Before Fit)

# %%
project.plotter.plot_meas_vs_calc(expt_name='sepd', show_residual=False)

# %%
project.plotter.plot_meas_vs_calc(expt_name='nomad', show_residual=False)

# %% [markdown]
# #### Set Fitting Parameters
#
# Shared structural parameters are refined against both datasets
# simultaneously.

# %%
structure.cell.length_a.free = True
structure.atom_sites['Si'].b_iso.free = True

# %% [markdown]
# Bragg experiment parameters.

# %%
bragg_expt.linked_phases['si'].scale.free = True
bragg_expt.instrument.calib_d_to_tof_offset.free = True
bragg_expt.peak.broad_gauss_sigma_0.free = True
bragg_expt.peak.broad_gauss_sigma_1.free = True
bragg_expt.peak.broad_gauss_sigma_2.free = True
for point in bragg_expt.background:
    point.y.free = True

# %% [markdown]
# PDF experiment parameters.

# %%
pdf_expt.linked_phases['si'].scale.free = True
pdf_expt.peak.damp_q.free = True
pdf_expt.peak.broad_q.free = True
pdf_expt.peak.sharp_delta_1.free = True
pdf_expt.peak.sharp_delta_2.free = True

# %% [markdown]
# #### Show Free Parameters

# %%
project.analysis.display.free_params()

# %% [markdown]
# #### Run Fitting

# %%
project.analysis.fit()
project.analysis.display.fit_results()

# %% [markdown]
# #### Plot Measured vs Calculated (After Fit)

# %%
project.plotter.plot_meas_vs_calc(expt_name='sepd', show_residual=False)

# %%
project.plotter.plot_meas_vs_calc(expt_name='nomad', show_residual=False)
