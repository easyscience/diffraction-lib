# %% [markdown]
# # Instrument calibration: BEER at ESS
#
# Two datasets from two symmetrically positioned banks (S2 and N2) of
# the BEER instrument are analyzed in this tutorial.
#
# The tutorial demonstrates how to set up the structures, experiments,
# and analysis for joint fitting of the two datasets, including how to
# link parameters across the two datasets.
#
# The tutorial also shows how to configure the instrument parameters
# based on metadata extracted from the data files.

# %% [markdown]
# ## Import Library

# %%
from easydiffraction import ExperimentFactory
from easydiffraction import Project
from easydiffraction import StructureFactory
from easydiffraction import download_data
from easydiffraction import extract_data_paths_from_zip
from easydiffraction import extract_metadata

# %% [markdown]
# ## Define Structures
#
# This section covers how to add structures and modify their
# parameters.
#
# #### Create Ferrite Structure

# %%
ferrite = StructureFactory.from_scratch(name='ferrite')

ferrite.space_group.name_h_m = 'I m -3 m'
ferrite.space_group.it_coordinate_system_code = '1'

ferrite.cell.length_a = 2.886

ferrite.atom_sites.create(
    label='Fe',
    type_symbol='Fe',
    fract_x=0.0,
    fract_y=0.0,
    fract_z=0.0,
    wyckoff_letter='a',
    adp_type='Biso',
    adp_iso=1.0,
)

# %% [markdown]
# #### Create Austenite Structure

# %%
austenite = StructureFactory.from_scratch(name='austenite')

austenite.space_group.name_h_m = 'F m -3 m'
austenite.space_group.it_coordinate_system_code = '1'

austenite.cell.length_a = 3.6468

austenite.atom_sites.create(
    label='Fe',
    type_symbol='Fe',
    fract_x=0.0,
    fract_y=0.0,
    fract_z=0.0,
    wyckoff_letter='a',
    adp_type='Biso',
    adp_iso=1.0,
)

# %% [markdown]
# ## Define Experiments
#
# This section shows how to add experiments, configure their parameters,
# and link the structures defined in the previous step.
#
# #### Download Measured Data

# %%
zip_path = download_data(id=33, destination='data')
data_paths = extract_data_paths_from_zip(zip_path, destination='data/ed-20')

data_path_s2 = data_paths[1]  # 'Duplex_in_HR_for_IRF_S2.dat'
data_path_n2 = data_paths[0]  # 'Duplex_in_HR_for_IRF_N2.dat'

# %% [markdown]
# #### Create Experiment

# %%
expt_s2 = ExperimentFactory.from_data_path(
    name='expt_s2',
    data_path=data_path_s2,
    beam_mode='time-of-flight',
)

# %%
expt_n2 = ExperimentFactory.from_data_path(
    name='expt_n2',
    data_path=data_path_n2,
    beam_mode='time-of-flight',
)

# %% [markdown]
# #### Set Instrument

# %%
expt_s2.instrument.setup_twotheta_bank = extract_metadata(
    data_path_s2, r'two_theta\s*=\s*(\d*\.?\d+)'
)
expt_s2.instrument.calib_d_to_tof_linear = extract_metadata(
    data_path_s2, r'DIFC\s*=\s*(\d*\.?\d+)'
)

# %%
expt_n2.instrument.setup_twotheta_bank = extract_metadata(
    data_path_n2, r'two_theta\s*=\s*(\d*\.?\d+)'
)
expt_n2.instrument.calib_d_to_tof_linear = extract_metadata(
    data_path_n2, r'DIFC\s*=\s*(\d*\.?\d+)'
)

# %% [markdown]
# #### Set Peak Profile

# %%
expt_s2.show_supported_peak_profile_types()
expt_s2.show_current_peak_profile_type()

# %%
expt_s2.peak_profile_type = 'pseudo-voigt'

# %%
expt_s2.peak.broad_gauss_sigma_0 = 300
expt_s2.peak.broad_gauss_sigma_1 = 1200
expt_s2.peak.broad_gauss_sigma_2 = 900

# %%
expt_n2.peak_profile_type = 'pseudo-voigt'

# %%
expt_n2.peak.broad_gauss_sigma_0 = 300
expt_n2.peak.broad_gauss_sigma_1 = 1200
expt_n2.peak.broad_gauss_sigma_2 = 900

# %% [markdown]
# #### Set Background

# %%
expt_s2.show_supported_background_types()
expt_s2.show_current_background_type()

# %%
# expt_s2.background_type = 'line-segment'

# %%
for idx, (x, y) in enumerate(
    [
        (40111.8789, 0.0170),
        (41193.5664, 0.1484),
        (42041.3750, 0.1848),
        (42713.7734, 0.1975),
        (44409.3945, 0.1891),
        (45198.7344, 0.2147),
        (46251.1875, 0.1887),
        (49350.0742, 0.2194),
        (51289.6836, 0.1991),
        (55245.1992, 0.1981),
        (55679.7070, 0.2276),
        (56383.9102, 0.2439),
        (58956.1797, 0.2907),
        (61536.4570, 0.3067),
        (63768.0469, 0.3242),
        (65581.2109, 0.2973),
        (70183.8516, 0.2575),
        (71787.8203, 0.2321),
        (78343.1094, 0.2158),
        (80016.8047, 0.1694),
        (98141.8516, 0.2400),
        (99262.2344, 0.4335),
        (100985.8516, 0.4375),
        (101933.8516, 0.3427),
        (108656.0312, 0.5339),
        (110896.7500, 0.9537),
        (113137.4844, 1.1668),
        (114430.2031, 1.1164),
        (116929.4844, 0.9161),
        (119428.7422, 0.6885),
        (134506.3438, 0.0692),
    ],
    start=1,
):
    expt_s2.background.create(id=str(idx), x=x, y=y)

# %%
for point in expt_s2.background:
    expt_n2.background.create(id=point.id.value, x=point.x.value, y=point.y.value)

# %% [markdown]
# #### Set Linked Phases

# %%
expt_s2.linked_phases.create(id='ferrite', scale=10)
expt_s2.linked_phases.create(id='austenite', scale=10)

# %%
expt_n2.linked_phases.create(id='ferrite', scale=10)
expt_n2.linked_phases.create(id='austenite', scale=10)

# %% [markdown]
# #### Set Excluded Regions

# %%
expt_s2.excluded_regions.create(id='1', start=0, end=40000)
expt_s2.excluded_regions.create(id='2', start=130000, end=180000)

# %%
expt_n2.excluded_regions.create(id='1', start=0, end=40000)
expt_n2.excluded_regions.create(id='2', start=130000, end=180000)

# %% [markdown]
# ## Define Project
#
# The project object is used to manage the structure, experiments,
# and analysis
#
# #### Create Project

# %%
project = Project(name='beer')
project.save_as(dir_path='beer')

# %% [markdown]
# #### Add Structures

# %%
project.structures.add(ferrite)
project.structures.add(austenite)

# %% [markdown]
# #### Add Experiments

# %%
project.experiments.add(expt_s2)
project.experiments.add(expt_n2)

# %% [markdown]
# #### Plot Measured vs Calculated

# %%
project.plotter.plot_meas_vs_calc(expt_name='expt_s2', show_residual=False)

# %%
project.plotter.plot_meas_vs_calc(expt_name='expt_n2', show_residual=False)

# %% [markdown]
# ## Perform Analysis
#
# This section shows the analysis process, including how to set up
# calculation and fitting engines.
#
# #### Set Fit Mode

# %%
project.analysis.show_supported_fit_mode_types()
project.analysis.show_current_fit_mode_type()

# %%
project.analysis.fit_mode.mode = 'joint'

# %% [markdown]
# #### Set Free Parameters

# %%
project.analysis.display.fittable_params()

# %%
ferrite.atom_sites['Fe'].adp_iso.free = True
austenite.atom_sites['Fe'].adp_iso.free = True

# %%
expt_s2.linked_phases['ferrite'].scale.free = True
expt_s2.linked_phases['austenite'].scale.free = True

expt_s2.peak.broad_gauss_sigma_0.free = True
expt_s2.peak.broad_gauss_sigma_1.free = True
expt_s2.peak.broad_gauss_sigma_2.free = True
expt_s2.peak.broad_lorentz_gamma_0.free = True

expt_s2.instrument.calib_d_to_tof_offset.free = True

for segment in expt_s2.background:
    segment.y.free = True

# %%
expt_n2.linked_phases['ferrite'].scale.free = True
expt_n2.linked_phases['austenite'].scale.free = True

expt_n2.peak.broad_gauss_sigma_0.free = True
expt_n2.peak.broad_gauss_sigma_1.free = True
expt_n2.peak.broad_gauss_sigma_2.free = True
expt_n2.peak.broad_lorentz_gamma_0.free = True

expt_n2.instrument.calib_d_to_tof_offset.free = True

for segment in expt_n2.background:
    segment.y.free = True

# %% [markdown]
# #### Add Constraints

# %%
project.analysis.aliases.create(
    label='s2_ferrite_scale', param=expt_s2.linked_phases['ferrite'].scale
)
project.analysis.aliases.create(
    label='s2_austenite_scale', param=expt_s2.linked_phases['austenite'].scale
)

project.analysis.aliases.create(
    label='n2_ferrite_scale', param=expt_n2.linked_phases['ferrite'].scale
)
project.analysis.aliases.create(
    label='n2_austenite_scale', param=expt_n2.linked_phases['austenite'].scale
)

project.analysis.constraints.create(expression='n2_ferrite_scale = s2_ferrite_scale')
project.analysis.constraints.create(expression='n2_austenite_scale = s2_austenite_scale')

# %% [markdown]
# #### Run Fitting
#
# Run full fitting with all free parameters.

# %%
project.analysis.fit()

# %% [markdown]
# Fix background and run fitting again.

# %%
for segment in expt_s2.background:
    segment.y.free = False
for segment in expt_n2.background:
    segment.y.free = False

# %%
project.analysis.fit()

# %% [markdown]
# Show fit results and parameter correlations.

# %%
project.analysis.display.fit_results()
project.plotter.plot_param_correlations()

# %% [markdown]
# #### Plot Measured vs Calculated
#
# Show full range in TOF.

# %%
project.plotter.plot_meas_vs_calc(expt_name='expt_s2', show_residual=False)

# %%
project.plotter.plot_meas_vs_calc(expt_name='expt_n2', show_residual=False)

# %% [markdown]
# Show selected peaks in d-spacing.

# %%
project.plotter.plot_meas_vs_calc(expt_name='expt_s2', x='d_spacing', x_min=2.08, x_max=2.13)

# %%
project.plotter.plot_meas_vs_calc(expt_name='expt_n2', x='d_spacing', x_min=2.08, x_max=2.13)
