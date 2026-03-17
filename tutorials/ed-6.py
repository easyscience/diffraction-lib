# %% [markdown]
# # Structure Refinement: HS, HRPT
#
# This example demonstrates a Rietveld refinement of HS crystal
# structure using constant wavelength neutron powder diffraction data
# from HRPT at PSI.

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
# This section shows how to add structures and modify their
# parameters.
#
# #### Create Structure

# %%
structure = StructureFactory.from_scratch(name='hs')

# %% [markdown]
# #### Set Space Group

# %%
structure.space_group.name_h_m = 'R -3 m'
structure.space_group.it_coordinate_system_code = 'h'

# %% [markdown]
# #### Set Unit Cell


# %%
structure.cell.length_a = 6.9
structure.cell.length_c = 14.1

# %% [markdown]
# #### Set Atom Sites

# %%
structure.atom_sites.add_from_scratch(
    label='Zn',
    type_symbol='Zn',
    fract_x=0,
    fract_y=0,
    fract_z=0.5,
    wyckoff_letter='b',
    b_iso=0.5,
)
structure.atom_sites.add_from_scratch(
    label='Cu',
    type_symbol='Cu',
    fract_x=0.5,
    fract_y=0,
    fract_z=0,
    wyckoff_letter='e',
    b_iso=0.5,
)
structure.atom_sites.add_from_scratch(
    label='O',
    type_symbol='O',
    fract_x=0.21,
    fract_y=-0.21,
    fract_z=0.06,
    wyckoff_letter='h',
    b_iso=0.5,
)
structure.atom_sites.add_from_scratch(
    label='Cl',
    type_symbol='Cl',
    fract_x=0,
    fract_y=0,
    fract_z=0.197,
    wyckoff_letter='c',
    b_iso=0.5,
)
structure.atom_sites.add_from_scratch(
    label='H',
    type_symbol='2H',
    fract_x=0.13,
    fract_y=-0.13,
    fract_z=0.08,
    wyckoff_letter='h',
    b_iso=0.5,
)

# %% [markdown]
# ## Define Experiment
#
# This section shows how to add experiments, configure their parameters,
# and link the structures defined in the previous step.
#
# #### Download Measured Data

# %%
data_path = download_data(id=11, destination='data')

# %% [markdown]
# #### Create Experiment

# %%
expt = ExperimentFactory.from_data_path(name='hrpt', data_path=data_path)

# %% [markdown]
# #### Set Instrument

# %%
expt.instrument.setup_wavelength = 1.89
expt.instrument.calib_twotheta_offset = 0.0

# %% [markdown]
# #### Set Peak Profile

# %%
expt.peak.broad_gauss_u = 0.1
expt.peak.broad_gauss_v = -0.2
expt.peak.broad_gauss_w = 0.2
expt.peak.broad_lorentz_x = 0.0
expt.peak.broad_lorentz_y = 0

# %% [markdown]
# #### Set Background

# %%
expt.background.add_from_scratch(id='1', x=4.4196, y=500)
expt.background.add_from_scratch(id='2', x=6.6207, y=500)
expt.background.add_from_scratch(id='3', x=10.4918, y=500)
expt.background.add_from_scratch(id='4', x=15.4634, y=500)
expt.background.add_from_scratch(id='5', x=45.6041, y=500)
expt.background.add_from_scratch(id='6', x=74.6844, y=500)
expt.background.add_from_scratch(id='7', x=103.4187, y=500)
expt.background.add_from_scratch(id='8', x=121.6311, y=500)
expt.background.add_from_scratch(id='9', x=159.4116, y=500)

# %% [markdown]
# #### Set Linked Phases

# %%
expt.linked_phases.add_from_scratch(id='hs', scale=0.5)

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
# #### Set Plotting Engine

# %%
# Keep the auto-selected engine. Alternatively, you can uncomment the
# line below to explicitly set the engine to the required one.
# project.plotter.engine = 'plotly'

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
# #### Set Calculator

# %%
project.analysis.current_calculator = 'cryspy'

# %% [markdown]
# #### Set Minimizer

# %%
project.analysis.current_minimizer = 'lmfit (leastsq)'

# %% [markdown]
# #### Plot Measured vs Calculated

# %%
project.plot_meas_vs_calc(expt_name='hrpt', show_residual=True)

# %%
project.plot_meas_vs_calc(expt_name='hrpt', x_min=48, x_max=51, show_residual=True)

# %% [markdown]
# ### Perform Fit 1/5
#
# Set parameters to be refined.

# %%
structure.cell.length_a.free = True
structure.cell.length_c.free = True

expt.linked_phases['hs'].scale.free = True
expt.instrument.calib_twotheta_offset.free = True

# %% [markdown]
# Show free parameters after selection.

# %%
project.analysis.show_free_params()

# %% [markdown]
# #### Run Fitting

# %%
project.analysis.fit()

# %%
project.analysis.show_fit_results()

# %% [markdown]
# #### Plot Measured vs Calculated

# %%
project.plot_meas_vs_calc(expt_name='hrpt', show_residual=True)

# %%
project.plot_meas_vs_calc(expt_name='hrpt', x_min=48, x_max=51, show_residual=True)

# %% [markdown]
# ### Perform Fit 2/5
#
# Set more parameters to be refined.

# %%
expt.peak.broad_gauss_u.free = True
expt.peak.broad_gauss_v.free = True
expt.peak.broad_gauss_w.free = True
expt.peak.broad_lorentz_x.free = True

for point in expt.background:
    point.y.free = True

# %% [markdown]
# Show free parameters after selection.

# %%
project.analysis.show_free_params()

# %% [markdown]
# #### Run Fitting

# %%
project.analysis.fit()

# %%
project.analysis.show_fit_results()

# %% [markdown]
# #### Plot Measured vs Calculated

# %%
project.plot_meas_vs_calc(expt_name='hrpt', show_residual=True)

# %%
project.plot_meas_vs_calc(expt_name='hrpt', x_min=48, x_max=51, show_residual=True)

# %% [markdown]
# ### Perform Fit 3/5
#
# Set more parameters to be refined.

# %%
structure.atom_sites['O'].fract_x.free = True
structure.atom_sites['O'].fract_z.free = True
structure.atom_sites['Cl'].fract_z.free = True
structure.atom_sites['H'].fract_x.free = True
structure.atom_sites['H'].fract_z.free = True

# %% [markdown]
# Show free parameters after selection.

# %%
project.analysis.show_free_params()

# %% [markdown]
# #### Run Fitting

# %%
project.analysis.fit()

# %%
project.analysis.show_fit_results()

# %% [markdown]
# #### Plot Measured vs Calculated

# %%
project.plot_meas_vs_calc(expt_name='hrpt', show_residual=True)

# %%
project.plot_meas_vs_calc(expt_name='hrpt', x_min=48, x_max=51, show_residual=True)

# %% [markdown]
# ### Perform Fit 4/5
#
# Set more parameters to be refined.

# %%
structure.atom_sites['Zn'].b_iso.free = True
structure.atom_sites['Cu'].b_iso.free = True
structure.atom_sites['O'].b_iso.free = True
structure.atom_sites['Cl'].b_iso.free = True
structure.atom_sites['H'].b_iso.free = True

# %% [markdown]
# Show free parameters after selection.

# %%
project.analysis.show_free_params()

# %% [markdown]
# #### Run Fitting

# %%
project.analysis.fit()

# %%
project.analysis.show_fit_results()

# %% [markdown]
# #### Plot Measured vs Calculated

# %%
project.plot_meas_vs_calc(expt_name='hrpt', show_residual=True)

# %%
project.plot_meas_vs_calc(expt_name='hrpt', x_min=48, x_max=51, show_residual=True)

# %% [markdown]
# ## Summary
#
# This final section shows how to review the results of the analysis.

# %% [markdown]
# #### Show Project Summary

# %%
project.summary.show_report()
