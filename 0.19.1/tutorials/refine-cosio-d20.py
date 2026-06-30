# %% [markdown]
# # Structure Refinement: Co2SiO4, D20
#
# This example demonstrates a Rietveld refinement of Co2SiO4 crystal
# structure using constant wavelength neutron powder diffraction data
# from D20 at ILL.
#
# It also shows different ways to set free parameters: standard
# one-by-one and batch setting.

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
structure = StructureFactory.from_scratch(name='cosio')

# %% [markdown]
# ### Set Space Group

# %%
structure.space_group.name_h_m = 'P n m a'
structure.space_group.coord_system_code = 'abc'

# %% [markdown]
# ### Set Unit Cell

# %%
structure.cell.length_a = 10.3
structure.cell.length_b = 6.0
structure.cell.length_c = 4.8

# %% [markdown]
# ### Set Atom Sites

# %%
structure.atom_sites.create(
    id='Co1',
    type_symbol='Co',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    adp_iso=0.5,
)
structure.atom_sites.create(
    id='Co2',
    type_symbol='Co',
    fract_x=0.279,
    fract_y=0.25,
    fract_z=0.985,
    adp_iso=0.5,
)
structure.atom_sites.create(
    id='Si',
    type_symbol='Si',
    fract_x=0.094,
    fract_y=0.25,
    fract_z=0.429,
    adp_iso=0.5,
)
structure.atom_sites.create(
    id='O1',
    type_symbol='O',
    fract_x=0.091,
    fract_y=0.25,
    fract_z=0.771,
    adp_iso=0.5,
)
structure.atom_sites.create(
    id='O2',
    type_symbol='O',
    fract_x=0.448,
    fract_y=0.25,
    fract_z=0.217,
    adp_iso=0.5,
)
structure.atom_sites.create(
    id='O3',
    type_symbol='O',
    fract_x=0.164,
    fract_y=0.032,
    fract_z=0.28,
    adp_iso=0.5,
)

# %% [markdown]
# ## 🔬 Define Experiment
#
# This section shows how to add experiments, configure their parameters,
# and link the structures defined in the previous step.
#
# ### Download Data

# %%
data_path = download_data('meas-cosio-d20', destination='data')

# %% [markdown]
# ### Create Experiment

# %%
expt = ExperimentFactory.from_data_path(name='d20', data_path=data_path)

# %% [markdown]
# ### Set Instrument

# %%
expt.instrument.setup_wavelength = 1.87
expt.instrument.calib_twotheta_offset = 0.1

# %% [markdown]
# ### Set Peak Profile

# %%
expt.peak.show_supported()

# %%
expt.peak.type = 'pseudo-voigt + berar-baldinozzi asymmetry'

# %%
expt.peak.broad_gauss_u = 0.3
expt.peak.broad_gauss_v = -0.5
expt.peak.broad_gauss_w = 0.4

# %%
expt.peak.cutoff_fwhm = 8

# %% [markdown]
# ### Set Background

# %%
expt.background.show_supported()

# %%
expt.background.create(id='1', position=8, intensity=500)
expt.background.create(id='2', position=9, intensity=500)
expt.background.create(id='3', position=10, intensity=500)
expt.background.create(id='4', position=11, intensity=500)
expt.background.create(id='5', position=12, intensity=500)
expt.background.create(id='6', position=15, intensity=500)
expt.background.create(id='7', position=25, intensity=500)
expt.background.create(id='8', position=30, intensity=500)
expt.background.create(id='9', position=50, intensity=500)
expt.background.create(id='10', position=70, intensity=500)
expt.background.create(id='11', position=90, intensity=500)
expt.background.create(id='12', position=110, intensity=500)
expt.background.create(id='13', position=130, intensity=500)
expt.background.create(id='14', position=150, intensity=500)

# %% [markdown]
# ### Set Linked Structures

# %%
expt.linked_structures.create(structure_id='cosio', scale=1.0)

# %% [markdown]
# ## 📦 Define Project
#
# The project object is used to manage the structure, experiment, and
# analysis.
#
# ### Create Project

# %%
project = Project(name='cosio_d20')

# %%
project.save_as(dir_path='projects/refine-cosio-d20')

# %% [markdown]
# ### Add Structure

# %%
project.structures.add(structure)

# %% [markdown]
# ### Add Experiment

# %%
project.experiments.add(expt)

# %% [markdown]
# ## 🚀 Perform Analysis
#
# This section shows the analysis process, including how to set up
# calculation and fitting engines.
#
# ### Display Structure

# %%
project.display.structure(struct_name='cosio')

# %% [markdown]
# ### Display Pattern

# %%
project.display.pattern(expt_name='d20')

# %%
project.display.pattern(expt_name='d20', x_min=41, x_max=54)

# %% [markdown]
# ### Set Free Parameters

# %%
structure.cell.length_a.free = True
structure.cell.length_b.free = True
structure.cell.length_c.free = True

for atom_site in structure.atom_sites:
    for parameter in ('fract_x', 'fract_y', 'fract_z'):
        getattr(atom_site, parameter).free = True

for atom_site in structure.atom_sites:
    atom_site.adp_iso.free = True

for label in ('O1', 'O2', 'O3'):
    atom_site = structure.atom_sites[label]
    atom_site.occupancy.free = True

# %%
expt.linked_structures['cosio'].scale.free = True

expt.instrument.calib_twotheta_offset.free = True

expt.peak.broad_gauss_u.free = True
expt.peak.broad_gauss_v.free = True
expt.peak.broad_gauss_w.free = True
expt.peak.broad_lorentz_y.free = True

expt.peak.asym_beba_b0.free = True

for point in expt.background:
    point.intensity.free = True

# %% [markdown]
# Show free parameters after selection.

# %%
project.display.parameters.free()

# %% [markdown]
# ### Set Constraints
#
# Set aliases for parameters.

# %%
project.analysis.aliases.create(
    id='biso_Co1',
    param=project.structures['cosio'].atom_sites['Co1'].adp_iso,
)
project.analysis.aliases.create(
    id='biso_Co2',
    param=project.structures['cosio'].atom_sites['Co2'].adp_iso,
)

# %% [markdown]
# Set constraints.

# %%
project.analysis.constraints.create(expression='biso_Co2 = biso_Co1')


# %% [markdown]
# ### Run Fitting

# %%
project.analysis.fit()

# %%
project.display.fit.results()

# %%
project.display.fit.correlations()

# %% [markdown]
# ### Display Pattern

# %%
project.display.pattern(expt_name='d20')

# %%
project.display.pattern(expt_name='d20', x_min=42, x_max=52)

# %% [markdown]
# ## 📊 Report
#
# The HTML report is written automatically when the project is saved;
# enable `project.report.pdf` as well for a PDF version.
