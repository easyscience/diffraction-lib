# %% [markdown]
# # Structure Refinement: PbSO4, NPD + XRD
#
# This example demonstrates a more advanced use of the EasyDiffraction
# library by explicitly creating and configuring structures and
# experiments before adding them to a project. It could be more suitable
# for users who are interested in creating custom workflows. This
# tutorial provides minimal explanation and is intended for users
# already familiar with EasyDiffraction.
#
# The tutorial covers a Rietveld refinement of PbSO4 crystal structure
# based on the joint fit of both X-ray and neutron diffraction data.

# %% [markdown]
# ## 🛠️ Import Library

# %%
from easydiffraction import ExperimentFactory
from easydiffraction import Project
from easydiffraction import StructureFactory
from easydiffraction import download_data

# %% [markdown]
# ## 🧩 Define Structure
#
# This section shows how to add structures and modify their
# parameters.
#
# ### Create Structure

# %%
struct = StructureFactory.from_scratch(name='pbso4')

# %% [markdown]
# ### Set Space Group

# %%
struct.space_group.name_h_m = 'P n m a'

# %% [markdown]
# ### Set Unit Cell

# %%
struct.cell.length_a = 8.47
struct.cell.length_b = 5.39
struct.cell.length_c = 6.95

# %% [markdown]
# ### Set Atom Sites

# %%
struct.atom_sites.create(
    id='Pb',
    type_symbol='Pb',
    fract_x=0.1876,
    fract_y=0.25,
    fract_z=0.167,
    adp_type='Biso',
    adp_iso=1.37,
)
struct.atom_sites.create(
    id='S',
    type_symbol='S',
    fract_x=0.0654,
    fract_y=0.25,
    fract_z=0.684,
    adp_type='Biso',
    adp_iso=0.3796,
)
struct.atom_sites.create(
    id='O1',
    type_symbol='O',
    fract_x=0.9082,
    fract_y=0.25,
    fract_z=0.5954,
    adp_type='Biso',
    adp_iso=1.9840,
)
struct.atom_sites.create(
    id='O2',
    type_symbol='O',
    fract_x=0.1935,
    fract_y=0.25,
    fract_z=0.5432,
    adp_type='Biso',
    adp_iso=1.4383,
)
struct.atom_sites.create(
    id='O3',
    type_symbol='O',
    fract_x=0.0811,
    fract_y=0.0272,
    fract_z=0.8086,
    adp_type='Biso',
    adp_iso=1.2808,
)

# %% [markdown]
# ## 🔬 Define Experiments
#
# This section shows how to add experiments, configure their parameters,
# and link the structures defined in the previous step.
#
# ### Experiment 1: npd
#
# #### Download Data

# %%
data_path1 = download_data('meas-pbso4-d1a', destination='data')

# %% [markdown]
# #### Create Experiment

# %%
expt1 = ExperimentFactory.from_data_path(
    name='npd',
    data_path=data_path1,
    radiation_probe='neutron',
)

# %% [markdown]
# #### Set Instrument

# %%
expt1.instrument.setup_wavelength = 1.91
expt1.instrument.calib_twotheta_offset = -0.1018

# %% [markdown]
# #### Set Peak Profile

# %%
expt1.peak.type = 'pseudo-voigt + berar-baldinozzi asymmetry'

# %%
expt1.peak.broad_gauss_u = 0.1678
expt1.peak.broad_gauss_v = -0.4636
expt1.peak.broad_gauss_w = 0.4168
expt1.peak.broad_lorentz_x = 0
expt1.peak.broad_lorentz_y = 0.0879

expt1.peak.asym_beba_a0 = -0.4327
expt1.peak.asym_beba_b0 = -0.0182
expt1.peak.asym_beba_a1 = 0.1976
expt1.peak.asym_beba_b1 = -0.0575

expt1.peak.cutoff_fwhm = 6

# %% [markdown]
# #### Set Background

# %% [markdown]
# Select the background type.

# %%
expt1.background.type = 'line-segment'

# %% [markdown]
# Add background points.

# %%
for id, x, y in [
    ('1', 11.0, 206.4940),
    ('2', 15.0, 194.7316),
    ('3', 20.0, 194.5190),
    ('4', 30.0, 188.3431),
    ('5', 50.0, 207.7130),
    ('6', 70.0, 201.6635),
    ('7', 120.0, 244.1902),
    ('8', 153.0, 226.3376),
]:
    expt1.background.create(id=id, position=x, intensity=y)

# %% [markdown]
# #### Set Linked Structures

# %%
expt1.linked_structures.create(structure_id='pbso4', scale=1.5)

# %% [markdown]
# ### Experiment 2: xrd
#
# #### Download Data

# %%
data_path2 = download_data('meas-pbso4-xray', destination='data')

# %% [markdown]
# #### Create Experiment

# %%
expt2 = ExperimentFactory.from_data_path(
    name='xrd',
    data_path=data_path2,
    radiation_probe='xray',
)

# %% [markdown]
# #### Set Instrument

# %%
expt2.instrument.setup_wavelength = 1.540560
expt2.instrument.setup_wavelength_2 = 1.544400
expt2.instrument.setup_wavelength_2_to_1_ratio = 0.5

expt2.instrument.setup_polarization_coefficient = 0.58
expt2.instrument.setup_monochromator_twotheta = 28

expt2.instrument.calib_twotheta_offset = -0.0292

# %% [markdown]
# #### Set Peak Profile

# %%
expt2.peak.type = 'pseudo-voigt + berar-baldinozzi asymmetry'

# %%
expt2.peak.broad_gauss_u = 0.0197
expt2.peak.broad_gauss_v = -0.0185
expt2.peak.broad_gauss_w = 0.0079
expt2.peak.broad_lorentz_y = 0.0645

expt2.peak.asym_beba_a0 = -0.2188
expt2.peak.asym_beba_b0 = -0.0301

expt2.peak.cutoff_fwhm = 6

# %% [markdown]
# #### Set Excluded Regions

# %%
expt2.excluded_regions.create(id='1', start=0, end=15)
expt2.excluded_regions.create(id='2', start=160, end=180)

# %% [markdown]
# #### Set Background

# %% [markdown]
# Select background type.

# %%
expt2.background.type = 'chebyshev'

# %% [markdown]
# Add Chebyshev background terms.

# %%
for id, x, y in [
    ('1', 0, 153.17),
    ('2', 1, 62.93),
    ('3', 2, 9.86),
    ('4', 3, 10.81),
    ('5', 4, -6.61),
    ('6', 5, -7.12),
]:
    expt2.background.create(id=id, order=x, coef=y)

# %% [markdown]
# #### Set Linked Structures

# %%
expt2.linked_structures.create(structure_id='pbso4', scale=0.001)

# %% [markdown]
# ## 📦 Define Project
#
# The project object is used to manage structures, experiments, and
# analysis.
#
# ### Create Project

# %%
project = Project(name='pbso4_joint')

# %% [markdown]
# ### Add Structure

# %%
project.structures.add(struct)

# %% [markdown]
# ### Add Experiments

# %%
project.experiments.add(expt1)
project.experiments.add(expt2)

# %% [markdown]
# ## 🚀 Perform Analysis
#
# This section outlines the analysis process, including how to configure
# calculation and fitting engines.
#
# ### Set Fit Mode

# %%
project.analysis.fitting_mode.type = 'joint'

# %% [markdown]
# ### Set Free Parameters
#
# Set structure parameters to be optimized.

# %%
struct.cell.length_a.free = True
struct.cell.length_b.free = True
struct.cell.length_c.free = True

for atom_id in ('Pb', 'S', 'O1', 'O2', 'O3'):
    atom = struct.atom_sites[atom_id]
    atom.adp_iso.free = True

# %% [markdown]
# Set experiment parameters to be optimized.

# %%
expt1.linked_structures['pbso4'].scale.free = True
expt1.instrument.calib_twotheta_offset.free = True
expt1.instrument.setup_wavelength.free = True

# %%
expt2.linked_structures['pbso4'].scale.free = True
expt2.instrument.calib_twotheta_offset.free = True

# %% [markdown]
# ### Run Fitting

# %%
project.analysis.fit()

# %%
project.display.fit.results()

# %% [markdown]
# #### Display Correlations

# %%
project.display.fit.correlations()

# %% [markdown]
# ### Display Pattern

# %%
project.display.pattern(expt_name='npd')

# %%
project.display.pattern(expt_name='xrd')

# %% [markdown]
# ### Display Structure

# %%
project.display.structure(struct_name='pbso4')

# %% [markdown]
# ## 💾 Save Project

# %%
project.save_as(dir_path='projects/refine-pbso4-joint')
