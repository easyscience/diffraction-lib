# %% [markdown]
# # Structure Refinement: HS, HRPT
#
# This example demonstrates a Rietveld refinement of HS crystal
# structure using constant wavelength neutron powder diffraction data
# from HRPT at PSI.

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
structure = StructureFactory.from_scratch(name='hs')

# %% [markdown]
# ### Set Space Group

# %%
structure.space_group.name_h_m = 'R -3 m'
structure.space_group.coord_system_code = 'h'

# %% [markdown]
# ### Set Unit Cell


# %%
structure.cell.length_a = 6.85
structure.cell.length_c = 14.1

# %% [markdown]
# ### Set Atom Sites

# %%
structure.atom_sites.create(
    id='Zn',
    type_symbol='Zn',
    fract_x=0,
    fract_y=0,
    fract_z=0.5,
    adp_iso=0.5,
)
structure.atom_sites.create(
    id='Cu',
    type_symbol='Cu',
    fract_x=0.5,
    fract_y=0,
    fract_z=0,
    adp_iso=0.5,
)
structure.atom_sites.create(
    id='O',
    type_symbol='O',
    fract_x=0.21,
    fract_y=-0.21,
    fract_z=0.06,
    adp_iso=0.5,
)
structure.atom_sites.create(
    id='Cl',
    type_symbol='Cl',
    fract_x=0,
    fract_y=0,
    fract_z=0.197,
    adp_iso=0.5,
)
structure.atom_sites.create(
    id='H',
    type_symbol='2H',
    fract_x=0.13,
    fract_y=-0.13,
    fract_z=0.08,
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
data_path = download_data('meas-hs-hrpt', destination='data')

# %% [markdown]
# ### Create Experiment

# %%
expt = ExperimentFactory.from_data_path(name='hrpt', data_path=data_path)

# %% [markdown]
# ### Set Instrument

# %%
expt.instrument.setup_wavelength = 1.89
expt.instrument.calib_twotheta_offset = 0.0

# %% [markdown]
# ### Set Peak Profile

# %%
expt.peak.show_supported()

# %%
expt.peak.type = 'pseudo-voigt + berar-baldinozzi asymmetry'

# %%
expt.peak.broad_gauss_u = 0.1
expt.peak.broad_gauss_v = -0.2
expt.peak.broad_gauss_w = 0.2
expt.peak.broad_lorentz_y = 0

# %%
expt.peak.cutoff_fwhm = 8

# %% [markdown]
# ### Set Background

# %%
expt.background.auto_estimate()

# %% [markdown]
# ### Set Linked Structures

# %%
expt.linked_structures.create(structure_id='hs', scale=0.5)

# %% [markdown]
# ## 📦 Define Project
#
# The project object is used to manage the structure, experiment, and
# analysis.
#
# ### Create Project

# %%
project = Project(name='hs_hrpt')

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
#
# ### Display Structure

# %%
project.display.structure(struct_name='hs')

# %% [markdown]
# ### Display Pattern

# %%
project.display.pattern(expt_name='hrpt')

# %%
project.display.pattern(expt_name='hrpt', x_min=48, x_max=51)

# %% [markdown]
# ### Perform Fit 1/4
#
# Set parameters to be refined.

# %%
structure.cell.length_a.free = True
structure.cell.length_c.free = True

expt.linked_structures['hs'].scale.free = True
expt.instrument.calib_twotheta_offset.free = True

# %% [markdown]
# Show free parameters after selection.

# %%
project.display.parameters.free()

# %% [markdown]
# #### Run Fitting

# %%
project.analysis.fit()

# %%
project.display.fit.results()

# %% [markdown]
# #### Display Pattern

# %%
project.display.pattern(expt_name='hrpt')

# %%
project.display.pattern(expt_name='hrpt', x_min=48, x_max=51)

# %% [markdown]
# ### Perform Fit 2/4
#
# Set more parameters to be refined.

# %%
expt.peak.broad_gauss_u.free = True
expt.peak.broad_gauss_v.free = True
expt.peak.broad_gauss_w.free = True
expt.peak.broad_lorentz_y.free = True

for point in expt.background:
    point.intensity.free = True

# %% [markdown]
# Show free parameters after selection.

# %%
project.display.parameters.free()

# %% [markdown]
# #### Run Fitting

# %%
project.analysis.fit()

# %%
project.display.fit.results()

# %% [markdown]
# #### Display Pattern

# %%
project.display.pattern(expt_name='hrpt')

# %%
project.display.pattern(expt_name='hrpt', x_min=48, x_max=51)

# %% [markdown]
# ### Perform Fit 3/4
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
project.display.parameters.free()

# %% [markdown]
# #### Run Fitting

# %%
project.analysis.fit()

# %%
project.display.fit.results()

# %% [markdown]
# #### Display Pattern

# %%
project.display.pattern(expt_name='hrpt')

# %%
project.display.pattern(expt_name='hrpt', x_min=48, x_max=51)

# %% [markdown]
# ### Perform Fit 4/4
#
# Set more parameters to be refined.

# %%
structure.atom_sites['Zn'].adp_iso.free = True
structure.atom_sites['Cu'].adp_iso.free = True
structure.atom_sites['O'].adp_iso.free = True
structure.atom_sites['Cl'].adp_iso.free = True
structure.atom_sites['H'].adp_iso.free = True

expt.peak.asym_beba_a0.free = True
expt.peak.asym_beba_b0.free = True
expt.peak.asym_beba_a1.free = True
expt.peak.asym_beba_b1.free = True

# %% [markdown]
# Show free parameters after selection.

# %%
project.display.parameters.free()

# %% [markdown]
# #### Run Fitting

# %%
project.analysis.fit()

# %%
project.display.fit.results()

# %%
project.display.fit.correlations()

# %% [markdown]
# #### Display Pattern

# %%
project.display.pattern(expt_name='hrpt')

# %%
project.display.pattern(expt_name='hrpt', x_min=48, x_max=51)

# %% [markdown]
# ## 📊 Report
#
# The HTML report is written automatically when the project is saved;
# enable `project.report.pdf` as well for a PDF version.

# %% [markdown]
# ## 💾 Save Project

# %%
project.save_as(dir_path='projects/refine-hs-hrpt')
