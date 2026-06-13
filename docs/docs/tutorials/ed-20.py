# %% [markdown]
# # Instrument calibration: BEER at ESS
#
# This example demonstrates a Rietveld refinement of a duplex steel
# structure using time-of-flight neutron powder diffraction data
# simulated with McStas.
#
# Two datasets from two symmetrically positioned banks (S2 and N2) of
# the BEER instrument are analyzed in this tutorial.

# %% [markdown]
# ## 🛠️ Import Library

# %%
from easydiffraction import ExperimentFactory
from easydiffraction import Project
from easydiffraction import StructureFactory
from easydiffraction import download_data
from easydiffraction import extract_data_paths_from_zip
from easydiffraction import extract_metadata

# %% [markdown]
# ## 🧩 Define Structures
#
# This section covers how to add structures and modify their
# parameters.
#
# ### Create Ferrite Structure

# %%
ferrite = StructureFactory.from_scratch(name='ferrite')

ferrite.space_group.name_h_m = 'I m -3 m'
ferrite.space_group.it_coordinate_system_code = '1'

ferrite.cell.length_a = 2.886

ferrite.atom_sites.create(
    id='Fe',
    type_symbol='Fe',
    fract_x=0.0,
    fract_y=0.0,
    fract_z=0.0,
    adp_type='Biso',
    adp_iso=1.0,
)

# %% [markdown]
# ### Create Austenite Structure

# %%
austenite = StructureFactory.from_scratch(name='austenite')

austenite.space_group.name_h_m = 'F m -3 m'
austenite.space_group.it_coordinate_system_code = '1'

austenite.cell.length_a = 3.6468

austenite.atom_sites.create(
    id='Fe',
    type_symbol='Fe',
    fract_x=0.0,
    fract_y=0.0,
    fract_z=0.0,
    adp_type='Biso',
    adp_iso=1.0,
)

# %% [markdown]
# ## 🔬 Define Experiments
#
# This section shows how to add experiments, configure their parameters,
# and link the structures defined in the previous step.
#
# ### Download Data

# %%
zip_path = download_data(id=33, destination='data')
data_paths = extract_data_paths_from_zip(zip_path, destination='data/ed-20')

data_path_s2 = data_paths[1]  # 'Duplex_in_HR_for_IRF_S2.dat'
data_path_n2 = data_paths[0]  # 'Duplex_in_HR_for_IRF_N2.dat'

# %% [markdown]
# ### Create Experiment

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
# ### Set Instrument

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
# ### Set Peak Profile

# %%
expt_s2.peak.show_supported()

# %%
expt_s2.peak.type = 'pseudo-voigt'

# %%
expt_s2.peak.broad_gauss_sigma_0 = 300
expt_s2.peak.broad_gauss_sigma_1 = 1200
expt_s2.peak.broad_gauss_sigma_2 = 900

# %%
expt_n2.peak.type = 'pseudo-voigt'

# %%
expt_n2.peak.broad_gauss_sigma_0 = 300
expt_n2.peak.broad_gauss_sigma_1 = 1200
expt_n2.peak.broad_gauss_sigma_2 = 900

# %% [markdown]
# ### Set Background

# %%
expt_s2.background.show_supported()

# %%
expt_s2.background.auto_estimate()

# %%
expt_s2.background.show()

# %%
for point in expt_s2.background:
    expt_n2.background.create(id=point.id.value, x=point.x.value, y=point.y.value)

# %% [markdown]
# ### Set Linked Phases

# %%
expt_s2.linked_phases.create(id='ferrite', scale=10)
expt_s2.linked_phases.create(id='austenite', scale=10)

# %%
expt_n2.linked_phases.create(id='ferrite', scale=10)
expt_n2.linked_phases.create(id='austenite', scale=10)

# %% [markdown]
# ### Set Excluded Regions

# %%
expt_s2.excluded_regions.create(id='1', start=0, end=40500)
expt_s2.excluded_regions.create(id='2', start=130000, end=180000)

# %%
expt_n2.excluded_regions.create(id='1', start=0, end=40500)
expt_n2.excluded_regions.create(id='2', start=130000, end=180000)

# %% [markdown]
# ## 📦 Define Project
#
# The project object is used to manage the structure, experiments,
# and analysis
#
# ### Create Project

# %%
project = Project(name='beer_mcstas')
project.save_as(dir_path='projects/ed_20_beer_mcstas')

# %% [markdown]
# ### Add Structures

# %%
project.structures.add(ferrite)
project.structures.add(austenite)

# %% [markdown]
# ### Add Experiments

# %%
project.experiments.add(expt_s2)
project.experiments.add(expt_n2)

# %% [markdown]
# ### Display Structure

# %%
project.display.structure(struct_name='ferrite')
project.display.structure(struct_name='austenite')

# %% [markdown]
# ### Display Pattern

# %%
project.display.pattern(expt_name='expt_s2')

# %%
project.display.pattern(expt_name='expt_n2')

# %% [markdown]
# ## 🚀 Perform Analysis
#
# This section shows the analysis process, including how to set up
# calculation and fitting engines.
#
# ### Set Fit Mode

# %%
project.analysis.fitting_mode.show_supported()

# %%
project.analysis.fitting_mode.type = 'joint'

# %% [markdown]
# ### Set Free Parameters

# %%
project.display.parameters.fittable()

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
# ### Add Constraints

# %%
project.analysis.aliases.create(
    id='s2_ferrite_scale', param=expt_s2.linked_phases['ferrite'].scale
)
project.analysis.aliases.create(
    id='s2_austenite_scale', param=expt_s2.linked_phases['austenite'].scale
)

project.analysis.aliases.create(
    id='n2_ferrite_scale', param=expt_n2.linked_phases['ferrite'].scale
)
project.analysis.aliases.create(
    id='n2_austenite_scale', param=expt_n2.linked_phases['austenite'].scale
)

project.analysis.constraints.create(expression='n2_ferrite_scale = s2_ferrite_scale')
project.analysis.constraints.create(expression='n2_austenite_scale = s2_austenite_scale')

# %% [markdown]
# ### Run Fitting
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
project.display.fit.results()
project.display.fit.correlations()

# %% [markdown]
# ### Display Pattern
#
# Show full range in TOF.

# %%
project.display.pattern(expt_name='expt_s2')

# %%
project.display.pattern(expt_name='expt_n2')

# %% [markdown]
# Show selected peaks in d-spacing.

# %%
project.display.pattern(
    expt_name='expt_s2',
    x='d_spacing',
    x_min=2.08,
    x_max=2.13,
)

# %%
project.display.pattern(
    expt_name='expt_n2',
    x='d_spacing',
    x_min=2.08,
    x_max=2.13,
)
