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
structure = StructureFactory.from_scratch(name='pbso4')

# %% [markdown]
# ### Set Space Group

# %%
structure.space_group.name_h_m = 'P n m a'

# %% [markdown]
# ### Set Unit Cell

# %%
structure.cell.length_a = 8.47
structure.cell.length_b = 5.39
structure.cell.length_c = 6.95

# %% [markdown]
# ### Set Atom Sites

# %%
structure.atom_sites.create(
    id='Pb',
    type_symbol='Pb',
    fract_x=0.1876,
    fract_y=0.25,
    fract_z=0.167,
    adp_iso=1.37,
)
structure.atom_sites.create(
    id='S',
    type_symbol='S',
    fract_x=0.0654,
    fract_y=0.25,
    fract_z=0.684,
    adp_iso=0.3777,
)
structure.atom_sites.create(
    id='O1',
    type_symbol='O',
    fract_x=0.9082,
    fract_y=0.25,
    fract_z=0.5954,
    adp_iso=1.9764,
)
structure.atom_sites.create(
    id='O2',
    type_symbol='O',
    fract_x=0.1935,
    fract_y=0.25,
    fract_z=0.5432,
    adp_iso=1.4456,
)
structure.atom_sites.create(
    id='O3',
    type_symbol='O',
    fract_x=0.0811,
    fract_y=0.0272,
    fract_z=0.8086,
    adp_iso=1.2822,
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
data_path1 = download_data(id=13, destination='data')

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
expt1.instrument.calib_twotheta_offset = -0.1406

# %% [markdown]
# #### Set Peak Profile

# %%
expt1.peak.broad_gauss_u = 0.139
expt1.peak.broad_gauss_v = -0.412
expt1.peak.broad_gauss_w = 0.386
expt1.peak.broad_lorentz_x = 0
expt1.peak.broad_lorentz_y = 0.088

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
    ('1', 11.0, 206.1624),
    ('2', 15.0, 194.75),
    ('3', 20.0, 194.505),
    ('4', 30.0, 188.4375),
    ('5', 50.0, 207.7633),
    ('6', 70.0, 201.7002),
    ('7', 120.0, 244.4525),
    ('8', 153.0, 226.0595),
]:
    expt1.background.create(id=id, x=x, y=y)

# %% [markdown]
# #### Set Linked Phases

# %%
expt1.linked_phases.create(id='pbso4', scale=1.5)

# %% [markdown]
# ### Experiment 2: xrd
#
# #### Download Data

# %%
data_path2 = download_data(id=16, destination='data')

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
expt2.instrument.setup_wavelength = 1.540567
expt2.instrument.calib_twotheta_offset = -0.05181

# %% [markdown]
# #### Set Peak Profile

# %%
expt2.peak.broad_gauss_u = 0.304138
expt2.peak.broad_gauss_v = -0.112622
expt2.peak.broad_gauss_w = 0.021272
expt2.peak.broad_lorentz_x = 0
expt2.peak.broad_lorentz_y = 0.057691

# %% [markdown]
# #### Set Background

# %% [markdown]
# Select background type.

# %%
expt2.background.type = 'chebyshev'

# %% [markdown]
# Add background points.

# %%
for id, x, y in [
    ('1', 0, 119.195),
    ('2', 1, 6.221),
    ('3', 2, -45.725),
    ('4', 3, 8.119),
    ('5', 4, 54.552),
    ('6', 5, -20.661),
]:
    expt2.background.create(id=id, order=x, coef=y)

# %% [markdown]
# #### Set Linked Phases

# %%
expt2.linked_phases.create(id='pbso4', scale=0.001)

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
project.structures.add(structure)

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
# ### Set Minimizer

# %%
project.analysis.minimizer.type = 'lmfit'

# %% [markdown]
# ### Set Free Parameters
#
# Set structure parameters to be optimized.

# %%
structure.cell.length_a.free = True
structure.cell.length_b.free = True
structure.cell.length_c.free = True

# %% [markdown]
# Set experiment parameters to be optimized.

# %%
expt1.linked_phases['pbso4'].scale.free = True

expt1.instrument.calib_twotheta_offset.free = True

expt1.peak.broad_gauss_u.free = True
expt1.peak.broad_gauss_v.free = True
expt1.peak.broad_gauss_w.free = True
expt1.peak.broad_lorentz_y.free = True

# %%
expt2.linked_phases['pbso4'].scale.free = True

expt2.instrument.calib_twotheta_offset.free = True

expt2.peak.broad_gauss_u.free = True
expt2.peak.broad_gauss_v.free = True
expt2.peak.broad_gauss_w.free = True
expt2.peak.broad_lorentz_y.free = True

for term in expt2.background:
    term.coef.free = True

# %% [markdown]
# ### Run Fitting

# %% [markdown]
# ### Display Structure

# %%
project.display.structure(struct_name='pbso4')

# %% [markdown]
# ### Display Pattern

# %%
project.display.pattern(expt_name='npd', x_min=35.5, x_max=38.3)

# %%
project.display.pattern(expt_name='xrd', x_min=29.0, x_max=30.4)

# %% [markdown]
# ## 💾 Save Project

# %%
project.save_as(dir_path='projects/ed_4_pbso4_joint')
