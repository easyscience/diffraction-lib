# %% [markdown]
# # Structure Refinement: PbSO4, XRD
#
# This example demonstrates a more advanced use of the EasyDiffraction
# library by explicitly creating and configuring structures and
# experiments before adding them to a project. It could be more suitable
# for users who are interested in creating custom workflows. This
# tutorial provides minimal explanation and is intended for users
# already familiar with EasyDiffraction.
#
# The tutorial covers a Rietveld refinement of PbSO4 crystal structure
# based on laboratory X-ray powder diffraction data.

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
# ### Experiment: xrd
#
# #### Download Data

# %%
data_path = download_data('meas-pbso4-xray', destination='data')

# %% [markdown]
# #### Create Experiment

# %%
expt = ExperimentFactory.from_data_path(
    name='xrd',
    data_path=data_path,
    radiation_probe='xray',
)

# %% [markdown]
# #### Set Instrument

# %%
expt.instrument.setup_wavelength = 1.540560
expt.instrument.setup_wavelength_2 = 1.544400
expt.instrument.setup_wavelength_2_to_1_ratio = 0.5

expt.instrument.setup_polarization_coefficient = 0.58
expt.instrument.setup_monochromator_twotheta = 28

expt.instrument.calib_twotheta_offset = -0.0292

# %% [markdown]
# #### Set Peak Profile

# %%
expt.peak.type = 'pseudo-voigt + berar-baldinozzi asymmetry'

# %%
expt.peak.broad_gauss_u = 0.0187
expt.peak.broad_gauss_v = -0.0175
expt.peak.broad_gauss_w = 0.0075
expt.peak.broad_lorentz_x = 0
expt.peak.broad_lorentz_y = 0.0655

expt.peak.asym_beba_a0 = -0.2176
expt.peak.asym_beba_b0 = -0.0301

# %% [markdown]
# #### Set Excluded Regions

# %%
expt.excluded_regions.create(id='1', start=0, end=15)
expt.excluded_regions.create(id='2', start=160, end=180)

# %% [markdown]
# #### Set Background

# %% [markdown]
# Select background type.

# %%
expt.background.type = 'chebyshev'

# %% [markdown]
# Add Chebyshev background terms.

# %%
for id, x, y in [
    ('1', 0, 143.9591),
    ('2', 1, 67.1718),
    ('3', 2, 13.7879),
    ('4', 3, -1.2264),
    ('5', 4, 4.4514),
    ('6', 5, -17.7450),
]:
    expt.background.create(id=id, order=x, coef=y)

# %% [markdown]
# #### Set Linked Structures

# %%
expt.linked_structures.create(structure_id='pbso4', scale=0.001)

# %% [markdown]
# ## 📦 Define Project
#
# The project object is used to manage structures, experiments, and
# analysis.
#
# ### Create Project

# %%
project = Project(name='pbso4_xray')

# %% [markdown]
# ### Add Structure

# %%
project.structures.add(struct)

# %% [markdown]
# ### Add Experiment

# %%
project.experiments.add(expt)

# %% [markdown]
# ## 🚀 Perform Analysis
#
# This section outlines the analysis process, including how to configure
# calculation and fitting engines.
#
# ### Set Minimizer

# %%
project.analysis.minimizer.type = 'bumps (lm)'

# %% [markdown]
# ### Set Free Parameters
#
# Set structure parameters to be optimized.

# %%
struct.cell.length_a.free = True
struct.cell.length_b.free = True
struct.cell.length_c.free = True

# for atom_id in ('Pb', 'S', 'O1', 'O2', 'O3'):
#     atom = struct.atom_sites[atom_id]
#     atom.adp_iso.free = True

# %% [markdown]
# Set experiment parameters to be optimized.

# %%
expt.linked_structures['pbso4'].scale.free = True

expt.instrument.calib_twotheta_offset.free = True

expt.peak.broad_gauss_u.free = True
expt.peak.broad_gauss_v.free = True
expt.peak.broad_gauss_w.free = True
expt.peak.broad_lorentz_y.free = True

expt.peak.asym_beba_a0.free = True
expt.peak.asym_beba_b0.free = True

for term in expt.background:
    term.coef.free = True

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
project.display.pattern(expt_name='xrd')

# %%
project.display.pattern(expt_name='xrd', x_min=77.6, x_max=82.2)

# %% [markdown]
# ## 💾 Save Project

# %%
project.save_as(dir_path='projects/refine-pbso4-xray')
