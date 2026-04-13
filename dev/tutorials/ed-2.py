# %% [markdown]
# # Structure Refinement: LBCO, HRPT
#
# This minimalistic example is designed to show how Rietveld refinement
# can be performed when both the crystal structure and experiment are
# defined directly in code. Only the experimentally measured data is
# loaded from an external file.
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
structure.cell.length_a = 3.88

# %%
structure.atom_sites.create(
    label='La',
    type_symbol='La',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    wyckoff_letter='a',
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
    adp_iso=0.5,
)
structure.atom_sites.create(
    label='O',
    type_symbol='O',
    fract_x=0,
    fract_y=0.5,
    fract_z=0.5,
    wyckoff_letter='c',
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
experiment.instrument.calib_twotheta_offset = 0.6

# %%
experiment.peak.broad_gauss_u = 0.1
experiment.peak.broad_gauss_v = -0.1
experiment.peak.broad_gauss_w = 0.1
experiment.peak.broad_lorentz_y = 0.1

# %%
experiment.background.create(id='1', x=10, y=170)
experiment.background.create(id='2', x=30, y=170)
experiment.background.create(id='3', x=50, y=170)
experiment.background.create(id='4', x=110, y=170)
experiment.background.create(id='5', x=165, y=170)

# %%
experiment.excluded_regions.create(id='1', start=0, end=5)
experiment.excluded_regions.create(id='2', start=165, end=180)

# %%
experiment.linked_phases.create(id='lbco', scale=10.0)

# %% [markdown]
# ## Step 4: Perform Analysis

# %%
structure.cell.length_a.free = True

structure.atom_sites['La'].adp_iso.free = True
structure.atom_sites['Ba'].adp_iso.free = True
structure.atom_sites['Co'].adp_iso.free = True
structure.atom_sites['O'].adp_iso.free = True

# %%
experiment.instrument.calib_twotheta_offset.free = True

experiment.peak.broad_gauss_u.free = True
experiment.peak.broad_gauss_v.free = True
experiment.peak.broad_gauss_w.free = True
experiment.peak.broad_lorentz_y.free = True

experiment.background['1'].y.free = True
experiment.background['2'].y.free = True
experiment.background['3'].y.free = True
experiment.background['4'].y.free = True
experiment.background['5'].y.free = True

experiment.linked_phases['lbco'].scale.free = True


# %%
project.analysis.fit()
project.analysis.display.fit_results()

# %%
project.plotter.plot_meas_vs_calc(expt_name='hrpt', show_residual=True)
