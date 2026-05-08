# %% [markdown]
# # Structure Refinement: LBCO, HRPT
#
# This minimalistic example is designed to show how Rietveld refinement
# can be performed when both the crystal structure and experiment are
# defined directly in code. Only the experimentally measured data is
# loaded from an external file. It also shows how to switch calculation
# engine.
#
# For this example, constant-wavelength neutron powder diffraction data
# for La0.5Ba0.5CoO3 from HRPT at PSI is used.
#
# It does not contain any advanced features or options, and includes no
# comments or explanations — these can be found in the other tutorials.
# Default values are used for all parameters if not specified. Only
# essential and self-explanatory code is provided.
#
# The example is intended for users who are already familiar with the
# EasyDiffraction library and want to quickly get started with a simple
# refinement. It is also useful for those who want to see what a
# refinement might look like in code. For a more detailed explanation of
# the code, please refer to the other tutorials.

# %% [markdown]
# ## Import Library

# %%
import easydiffraction as ed

# %% [markdown]
# ## Step 1: Define Project

# %%
project = ed.Project()

# %% [markdown]
# ## Step 2: Define Structure

# %%
project.structures.create(name='lbco')

# %%
structure = project.structures['lbco']

# %%
structure.space_group.name_h_m = 'P m -3 m'
structure.space_group.it_coordinate_system_code = '1'

# %%
structure.cell.length_a = 3.8909

# %%
structure.atom_sites.create(
    label='La',
    type_symbol='La',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    wyckoff_letter='a',
    adp_type='Biso',
    adp_iso=0.5,
    occupancy=0.5,
)
structure.atom_sites.create(
    label='Ba',
    type_symbol='Ba',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    wyckoff_letter='a',
    adp_type='Biso',
    adp_iso=0.5,
    occupancy=0.5,
)
structure.atom_sites.create(
    label='Co',
    type_symbol='Co',
    fract_x=0.5,
    fract_y=0.5,
    fract_z=0.5,
    wyckoff_letter='b',
    adp_type='Biso',
    adp_iso=0.5,
)
structure.atom_sites.create(
    label='O',
    type_symbol='O',
    fract_x=0,
    fract_y=0.5,
    fract_z=0.5,
    wyckoff_letter='c',
    adp_type='Biso',
    adp_iso=0.5,
)

# %% [markdown]
# ## Step 3: Define Experiment

# %%
data_path = ed.download_data(id=3, destination='data')

# %%
project.experiments.add_from_data_path(
    name='hrpt',
    data_path=data_path,
    sample_form='powder',
    beam_mode='constant wavelength',
    radiation_probe='neutron',
)

# %%
experiment = project.experiments['hrpt']

# %%
experiment.instrument.setup_wavelength = 1.494
experiment.instrument.calib_twotheta_offset = 0.6226

# %%
experiment.peak.broad_gauss_u = 0.0816
experiment.peak.broad_gauss_v = -0.1159
experiment.peak.broad_gauss_w = 0.1204
experiment.peak.broad_lorentz_y = 0.0844

# %%
experiment.background.create(id='1', x=10, y=168.5585)
experiment.background.create(id='2', x=30, y=164.3357)
experiment.background.create(id='3', x=50, y=166.8881)
experiment.background.create(id='4', x=110, y=175.4006)
experiment.background.create(id='5', x=165, y=174.2813)

# %%
experiment.excluded_regions.create(id='1', start=0, end=20)
experiment.excluded_regions.create(id='2', start=160, end=180)

# %%
experiment.linked_phases.create(id='lbco', scale=9.1351)

# %% [markdown]
# ## Step 4: Perform Analysis

# %%
structure.cell.length_a.free = True
experiment.instrument.calib_twotheta_offset.free = True

# %%
project.analysis.fit.show_minimizer_types()
project.analysis.fit.minimizer_type = 'bumps (lm)'

# %%
project.analysis.fit()

# %%
project.analysis.display.fit_results()

# %%
project.display.plotter.plot_param_correlations()

# %%
project.display.plotter.plot_meas_vs_calc(expt_name='hrpt')

# %% [markdown]
# ## Step 5: Perform Bayesian Analysis

# %%
length_a = structure.cell.length_a.value
length_a_sigma = structure.cell.length_a.uncertainty or 0.001
length_a_window = max(8.0 * length_a_sigma, 0.001)
structure.cell.length_a.fit_min = length_a - length_a_window
structure.cell.length_a.fit_max = length_a + length_a_window

twotheta_offset = experiment.instrument.calib_twotheta_offset.value
twotheta_offset_sigma = experiment.instrument.calib_twotheta_offset.uncertainty or 0.01
twotheta_offset_window = max(8.0 * twotheta_offset_sigma, 0.01)
experiment.instrument.calib_twotheta_offset.fit_min = twotheta_offset - twotheta_offset_window
experiment.instrument.calib_twotheta_offset.fit_max = twotheta_offset + twotheta_offset_window

# %%
project.analysis.display.free_params()

# %%
project.analysis.fit.show_minimizer_types()
project.analysis.fit.minimizer_type = 'bumps (dream)'

dream = project.analysis.fit.minimizer
dream.steps = 1000
dream.burn = 200
dream.thin = 1
dream.pop = 4

# %%
project.analysis.fit()

# %%
project.analysis.display.fit_results()

# %%
project.display.plotter.plot_param_correlations()

# %%
project.display.plotter.plot_meas_vs_calc(expt_name='hrpt')

# %%
project.display.plotter.plot_posterior_pairs()

# %%
project.display.plotter.plot_param_distribution(structure.cell.length_a)
project.display.plotter.plot_param_distribution(experiment.instrument.calib_twotheta_offset)

# %%
project.display.plotter.plot_posterior_predictive(expt_name='hrpt', style='band')
project.display.plotter.plot_posterior_predictive(expt_name='hrpt', style='draws')
