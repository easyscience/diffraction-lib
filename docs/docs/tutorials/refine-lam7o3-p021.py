# %% [markdown]
# # Structure Refinement: LaM(7)O3, P02.1 Synchrotron XRD
#
# This example refines the compositionally complex LaM(7)O3 perovskite,
# with La on the A site and an equimolar mixture of Ti, Cr, Mn, Fe, Co,
# Ni, and Cu on the B site. The low-temperature synchrotron X-ray powder
# diffraction pattern was collected at the P02.1 beamline at PETRA III.
# The workflow starts from approximate structural and profile parameters,
# estimates the background from the measured pattern, and improves the
# model in two fitting stages.

# %% [markdown]
# ## 🛠️ Import Library

# %%
import easydiffraction as edi

# %% [markdown]
# ## 📦 Define Project
#
# The project manages the structures, experiments, analysis, and saved
# results used throughout the tutorial.
#
# ### Create Project

# %%
project = edi.Project(
    name='lam7o3_p021',
    description='LaM(7)O3 refinement using P02.1 synchrotron X-ray data.',
)

# %% [markdown]
# ### Save Initial Project
#
# Create the project directory before fitting so that analysis results
# can be written as they are produced.

# %%
project.save_as(dir_path='projects/refine-lam7o3-p021')

# %% [markdown]
# ## 🧩 Define Structure
#
# The Pnma structure is initialized from approximate values rather than
# the final refined values.
#
# ### Create Structure
#
# Define the structure as an inline CIF. Empty uncertainty parentheses,
# such as `5.5()`, mark a parameter as free without assigning an initial
# standard uncertainty. Values without parentheses remain fixed.

# %%
structure_cif = """
data_lam7o3

_cell.length_a 5.5()
_cell.length_b 7.7()
_cell.length_c 5.5()
_cell.angle_alpha 90.
_cell.angle_beta  90.
_cell.angle_gamma 90.

_space_group.name_h_m "P n m a"
_space_group.coord_system_code abc

loop_
_atom_site.id
_atom_site.type_symbol
_atom_site.fract_x
_atom_site.fract_y
_atom_site.fract_z
_atom_site.occupancy
_atom_site.adp_iso
_atom_site.adp_type
La La  0.48()  0.25   0.004()   1.        0.1() Biso
Ti Ti  0.      0.     0.        0.14286   0.1() Biso
Cr Cr  0.      0.     0.        0.14286   0.1   Biso
Mn Mn  0.      0.     0.        0.14286   0.1   Biso
Fe Fe  0.      0.     0.        0.14286   0.1   Biso
Co Co  0.      0.     0.        0.14286   0.1   Biso
Ni Ni  0.      0.     0.        0.14286   0.1   Biso
Cu Cu  0.      0.     0.        0.14286   0.1   Biso
O1 O   0.51()  0.25   0.57()    1.        0.1() Biso
O2 O   0.22()  0.03() 0.27()    1.        0.1   Biso
"""

# %%
project.structures.add_from_cif_str(structure_cif)

# %%
project.structures.show_names()

# %% [markdown]
# Use a short alias to access the structure parameters below.

# %%
structure = project.structures['lam7o3']

# %% [markdown]
# ### Display Structure
#
# Inspect the structure as text and as an interactive crystal model.

# %%
structure.show_as_text()

# %%
project.display.structure(struct_name='lam7o3')

# %% [markdown]
# ## 🔬 Define Experiment
#
# Load the measured pattern, configure the instrument and peak profile,
# and link the structure to the experiment.
#
# ### Download Data
#
# The first two columns contain 2-theta and intensity. When a third
# column of standard uncertainties is absent, EasyDiffraction estimates
# it from the square root of the intensity.

# %%
data_path = edi.download_data('meas-hep7c-xray-synchrotron', destination='data')

# %% [markdown]
# ### Create P02.1 Experiment

# %%
project.experiments.add_from_data_path(
    name='p021',
    data_path=data_path,
    sample_form='powder',
    beam_mode='constant wavelength',
    radiation_probe='xray',
)

# %% [markdown]
# Use a short alias to access the P02.1 experiment parameters below.

# %%
experiment = project.experiments['p021']

# %% [markdown]
# ### Set Linked Structures
#
# Link the structural model to the measured pattern and use an
# order-of-magnitude estimate for the scale factor.

# %%
experiment.linked_structures.create(
    structure_id='lam7o3',
    scale=0.000005,
)

# %% [markdown]
# ### Set P02.1 Instrument Parameters
#
# Set the monochromatic X-ray wavelength reported for the P02.1
# beamline measurement and initialize the unknown 2-theta zero shift at
# zero.

# %%
experiment.instrument.setup_wavelength = 0.207109
experiment.instrument.calib_twotheta_offset = 0.0

# %% [markdown]
# ### Set Peak Profile
#
# Select a pseudo-Voigt profile and provide approximate broadening
# parameters. U, V, and W define the Gaussian contribution; X and Y
# define the Lorentzian contribution.

# %%
experiment.peak.show_supported()

# %%
experiment.peak.type = 'pseudo-voigt'

# %%
experiment.peak.broad_gauss_u = 0.04
experiment.peak.broad_gauss_v = -0.01
experiment.peak.broad_gauss_w = 0.001
experiment.peak.broad_lorentz_x = 0.1
experiment.peak.broad_lorentz_y = 0.0

# %% [markdown]
# ### Set Excluded Regions
#
# Restrict the fit to the useful measured range from 2 to 15 degrees.

# %%
experiment.excluded_regions.create(id='1', start=0.0, end=2.0)
experiment.excluded_regions.create(id='2', start=15.0, end=20.0)

# %% [markdown]
# ### Set Background
#
# Estimate initial background points from the measured pattern alone.

# %%
experiment.background.auto_estimate(use_model=False)

# %%
experiment.background.show()

# %% [markdown]
# ### Inspect Experiment
#
# Display the configured experiment as text.

# %%
experiment.show_as_text()

# %% [markdown]
# ## 🚀 Perform Analysis
#
# Select the refinement parameters, apply the shared-Biso constraints,
# and improve the model in two fitting stages.
#
# ### Set Free Parameters
#
# The independent cell lengths, selected fractional coordinates, and
# three independent Biso values were marked free by `()` in the inline
# CIF. They do not need to be selected again here.

# %% [markdown]
# Refine the scale factor, zero shift, U/V/W/X profile terms, and active
# background-point intensities.

# %%
experiment.linked_structures['lam7o3'].scale.free = True

experiment.instrument.calib_twotheta_offset.free = True

experiment.peak.broad_gauss_u.free = True
experiment.peak.broad_gauss_v.free = True
experiment.peak.broad_gauss_w.free = True
experiment.peak.broad_lorentz_x.free = True

for point in experiment.background:
    point.intensity.free = True

# %% [markdown]
# Display all parameters selected for refinement.

# %%
project.display.parameters.free()

# %% [markdown]
# ### Set Constraints
#
# Create aliases for the constrained Biso parameters. The seven
# elements share one B site and therefore one Biso value; O1 and O2
# are also modeled with one shared Biso value.

# %%
# B sites: Ti, Cr, Mn, Fe, Co, Ni, Cu
project.analysis.aliases.create(
    id='biso_Ti',
    param=structure.atom_sites['Ti'].adp_iso,
)
project.analysis.aliases.create(
    id='biso_Cr',
    param=structure.atom_sites['Cr'].adp_iso,
)
project.analysis.aliases.create(
    id='biso_Mn',
    param=structure.atom_sites['Mn'].adp_iso,
)
project.analysis.aliases.create(
    id='biso_Fe',
    param=structure.atom_sites['Fe'].adp_iso,
)
project.analysis.aliases.create(
    id='biso_Co',
    param=structure.atom_sites['Co'].adp_iso,
)
project.analysis.aliases.create(
    id='biso_Ni',
    param=structure.atom_sites['Ni'].adp_iso,
)
project.analysis.aliases.create(
    id='biso_Cu',
    param=structure.atom_sites['Cu'].adp_iso,
)

# O sites: O1, O2
project.analysis.aliases.create(
    id='biso_O1',
    param=structure.atom_sites['O1'].adp_iso,
)
project.analysis.aliases.create(
    id='biso_O2',
    param=structure.atom_sites['O2'].adp_iso,
)

# %% [markdown]
# Apply the equality constraints using the aliases.

# %%
project.analysis.constraints.create(id='1', expression='biso_Cr = biso_Ti')
project.analysis.constraints.create(id='2', expression='biso_Mn = biso_Ti')
project.analysis.constraints.create(id='3', expression='biso_Fe = biso_Ti')
project.analysis.constraints.create(id='4', expression='biso_Co = biso_Ti')
project.analysis.constraints.create(id='5', expression='biso_Ni = biso_Ti')
project.analysis.constraints.create(id='6', expression='biso_Cu = biso_Ti')

project.analysis.constraints.create(id='7', expression='biso_O2 = biso_O1')

# %% [markdown]
# Display the defined constraints.

# %%
project.analysis.display.constraints()

# %% [markdown]
# ### Fit Initial Model
#
# The first fit uses a background estimated directly from the measured
# pattern.
#
# #### Display Pattern (Before Fit)
#
# Compare the measured pattern with the calculation from the starting
# model before optimization.

# %%
project.display.pattern(expt_name='p021')

# %%
project.display.pattern(expt_name='p021', x_min=2.2, x_max=4.0)

# %% [markdown]
# #### Run Fitting

# %%
project.analysis.fit()

# %% [markdown]
# Display the initial fit summary and the strongest parameter
# correlations.

# %%
project.display.fit.results()

# %%
project.display.fit.correlations(max_parameters=5)

# %% [markdown]
# #### Display Pattern (After Initial Fit)
#
# Inspect the full fitted pattern and the nonuniform low-angle
# background region.

# %%
project.display.pattern(expt_name='p021')

# %%
project.display.pattern(expt_name='p021', x_min=2.2, x_max=4.0)

# %% [markdown]
# ### Improve Background Estimate
#
# With a fitted peak model available, repeat automatic estimation using
# the calculated peak contribution. This replaces the original points
# with a model-guided estimate. Replacement points are fixed by default,
# so mark their intensities free again.

# %%
experiment.background.auto_estimate(use_model=True)

# %%
experiment.background.show()

# %%
for point in experiment.background:
    point.intensity.free = True

# %% [markdown]
# #### Run Fitting

# %%
project.analysis.fit()

# %%
project.display.fit.results()

# %%
project.display.fit.correlations(max_parameters=5)

# %% [markdown]
# #### Display Pattern (After Final Fit)

# %%
project.display.pattern(expt_name='p021')

# %%
project.display.pattern(expt_name='p021', x_min=2.2, x_max=4.0)

# %% [markdown]
# ## 📊 Report
#
# The HTML report is written automatically when the project is saved.
# PDF generation can be enabled before the final save when required.

# %%
# Enable PDF report generation before the last save (time consuming)
# project.report.pdf = True

# %% [markdown]
# ## 💾 Save Project

# %%
project.save()

# %%
