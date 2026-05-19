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
structure = StructureFactory.from_scratch(name='cosio')

# %% [markdown]
# #### Set Space Group

# %%
structure.space_group.name_h_m = 'P n m a'
structure.space_group.it_coordinate_system_code = 'abc'

# %% [markdown]
# #### Set Unit Cell

# %%
structure.cell.length_a = 10.3
structure.cell.length_b = 6.0
structure.cell.length_c = 4.8

# %% [markdown]
# #### Set Atom Sites

# %%
structure.atom_sites.create(
    label='Co1',
    type_symbol='Co',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    wyckoff_letter='a',
    adp_iso=0.5,
)
structure.atom_sites.create(
    label='Co2',
    type_symbol='Co',
    fract_x=0.279,
    fract_y=0.25,
    fract_z=0.985,
    wyckoff_letter='c',
    adp_iso=0.5,
)
structure.atom_sites.create(
    label='Si',
    type_symbol='Si',
    fract_x=0.094,
    fract_y=0.25,
    fract_z=0.429,
    wyckoff_letter='c',
    adp_iso=0.5,
)
structure.atom_sites.create(
    label='O1',
    type_symbol='O',
    fract_x=0.091,
    fract_y=0.25,
    fract_z=0.771,
    wyckoff_letter='c',
    adp_iso=0.5,
)
structure.atom_sites.create(
    label='O2',
    type_symbol='O',
    fract_x=0.448,
    fract_y=0.25,
    fract_z=0.217,
    wyckoff_letter='c',
    adp_iso=0.5,
)
structure.atom_sites.create(
    label='O3',
    type_symbol='O',
    fract_x=0.164,
    fract_y=0.032,
    fract_z=0.28,
    wyckoff_letter='d',
    adp_iso=0.5,
)

# %% [markdown]
# ## Define Experiment
#
# This section shows how to add experiments, configure their parameters,
# and link the structures defined in the previous step.
#
# #### Download Measured Data

# %%
data_path = download_data(id=12, destination='data')

# %% [markdown]
# #### Create Experiment

# %%
expt = ExperimentFactory.from_data_path(name='d20', data_path=data_path)

# %% [markdown]
# #### Set Instrument

# %%
expt.instrument.setup_wavelength = 1.87
expt.instrument.calib_twotheta_offset = 0.1

# %% [markdown]
# #### Set Peak Profile

# %%
expt.show_peak_profile_types()

# %%
expt.peak_profile_type = 'pseudo-voigt + empirical asymmetry'

# %%
expt.peak.broad_gauss_u = 0.3
expt.peak.broad_gauss_v = -0.5
expt.peak.broad_gauss_w = 0.4

# %% [markdown]
# #### Set Background

# %%
expt.show_background_types()

# %%
expt.background.create(id='1', x=8, y=500)
expt.background.create(id='2', x=9, y=500)
expt.background.create(id='3', x=10, y=500)
expt.background.create(id='4', x=11, y=500)
expt.background.create(id='5', x=12, y=500)
expt.background.create(id='6', x=15, y=500)
expt.background.create(id='7', x=25, y=500)
expt.background.create(id='8', x=30, y=500)
expt.background.create(id='9', x=50, y=500)
expt.background.create(id='10', x=70, y=500)
expt.background.create(id='11', x=90, y=500)
expt.background.create(id='12', x=110, y=500)
expt.background.create(id='13', x=130, y=500)
expt.background.create(id='14', x=150, y=500)

# %% [markdown]
# #### Set Linked Phases

# %%
expt.linked_phases.create(id='cosio', scale=1.0)

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
# #### Plot Measured vs Calculated

# %%
project.display.pattern(expt_name='d20')

# %%
project.display.pattern(expt_name='d20', x_min=41, x_max=54)

# %% [markdown]
# #### Set Free Parameters

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
expt.linked_phases['cosio'].scale.free = True

expt.instrument.calib_twotheta_offset.free = True

expt.peak.broad_gauss_u.free = True
expt.peak.broad_gauss_v.free = True
expt.peak.broad_gauss_w.free = True
expt.peak.broad_lorentz_y.free = True

expt.peak.asym_empir_2.free = True

for point in expt.background:
    point.y.free = True

# %% [markdown]
# Show free parameters after selection.

# %%
project.display.parameters.free()

# %% [markdown]
# #### Set Constraints
#
# Set aliases for parameters.

# %%
project.analysis.aliases.create(
    label='biso_Co1',
    param=project.structures['cosio'].atom_sites['Co1'].adp_iso,
)
project.analysis.aliases.create(
    label='biso_Co2',
    param=project.structures['cosio'].atom_sites['Co2'].adp_iso,
)

# %% [markdown]
# Set constraints.

# %%
project.analysis.constraints.create(expression='biso_Co2 = biso_Co1')


# %% [markdown]
# #### Run Fitting

# %%
project.analysis.fit()

# %%
project.display.fit.results()

# %%
project.display.fit.correlations()

# %% [markdown]
# #### Plot Measured vs Calculated

# %%
project.display.pattern(expt_name='d20')

# %%
project.display.pattern(expt_name='d20', x_min=42, x_max=52)

# %% [markdown]
# ## Summary
#
# This final section shows how to review the results of the analysis.

# %% [markdown]
# #### Show Project Summary

# %%
project.summary.show_report()
