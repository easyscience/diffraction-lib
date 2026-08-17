# %% [markdown]
# # Structure Refinement: LMO, ECHIDNA
#
# This example refines an LMO structure with Li/Ni site mixing against
# constant-wavelength neutron powder diffraction data collected on the
# ECHIDNA diffractometer at ANSTO. The workflow starts from approximate
# structural and profile parameters, constrains the coupled site
# occupancies, and performs a Rietveld refinement.

# %% [markdown]
# ## 🛠️ Import Library

# %%
import easydiffraction as edi

# %% [markdown]
# ## 📦 Define Project
#
# The project manages the structure, experiment, analysis, and saved
# results used throughout the tutorial.
#
# ### Create Project

# %%
project = edi.Project(
    name='lmo_echidna',
    description='LMO refinement using ECHIDNA neutron powder diffraction data.',
)

# %% [markdown]
# ### Save Initial Project
#
# Create the project directory before fitting so that analysis results
# can be written as they are produced.

# %%
project.save_as(dir_path='projects/refine-lmo-echidna')

# %% [markdown]
# ## 🧩 Define Structure
#
# The rhombohedral LMO model contains two crystallographic cation sites.
# Li1 and Ni1 share the site at z = 1/2, while Li2 and Ni2 share the site
# at z = 0. Their starting occupancies describe a small amount of Li/Ni
# site mixing.
#
# ### Create Structure from CIF
#
# Define the complete starting structure in a compact inline CIF. The
# hexagonal setting of space group R-3m is used, with approximate cell
# dimensions and oxygen z coordinate.

# %%
structure_cif = """
data_lmo

_cell.length_a  2.88
_cell.length_b  2.88
_cell.length_c 14.18
_cell.angle_alpha 90.
_cell.angle_beta  90.
_cell.angle_gamma 120.

_space_group.name_h_m "R -3 m"
_space_group.coord_system_code h

loop_
_atom_site.id
_atom_site.type_symbol
_atom_site.fract_x
_atom_site.fract_y
_atom_site.fract_z
_atom_site.occupancy
_atom_site.adp_iso
_atom_site.adp_type
O   O   0. 0. 0.26  1.0000  0.94645 Biso
Ni1 Ni  0. 0. 0.5   0.0184  1.00000 Biso
Li1 Li  0. 0. 0.5   0.9816  1.00000 Biso
Li2 Li  0. 0. 0.0   0.0184  1.00000 Biso
Ni2 Ni  0. 0. 0.0   0.9816  1.00000 Biso
"""

# %%
project.structures.add_from_cif_str(structure_cif)

# %%
project.structures.show_names()

# %% [markdown]
# Use a short alias to access the structure parameters below.

# %%
structure = project.structures['lmo']

# %% [markdown]
# ### Display Structure
#
# Inspect the structure as text and as an interactive crystal model.

# %%
structure.show_as_text()

# %%
project.display.structure(struct_name='lmo')

# %% [markdown]
# ## 🔬 Define Experiment
#
# Load the measured pattern, choose the calculation engine, configure
# the instrument and peak profile, and link the structure to the data.
#
# ### Download Data
#
# Download the LMO pattern from the EasyDiffraction online data
# repository. The columns contain 2-theta, intensity, and the standard
# uncertainty of the measured intensity.

# %%
data_path = edi.download_data('meas-lmo-echidna', destination='data')

# %% [markdown]
# ### Create Experiment

# %%
project.experiments.add_from_data_path(
    name='echidna',
    data_path=data_path,
    sample_form='powder',
    beam_mode='constant wavelength',
    radiation_probe='neutron',
)

# %% [markdown]
# Use a short alias to access the experiment parameters below.

# %%
experiment = project.experiments['echidna']

# %% [markdown]
# ### Select Calculator
#
# Use the CrysFML calculation engine for this refinement.

# %%
experiment.calculator.show_supported()

# %%
experiment.calculator.type = 'crysfml'

# %% [markdown]
# ### Set Instrument
#
# Set the measured neutron wavelength and approximate calibration
# corrections for the 2-theta zero, sample displacement, and sample
# transparency.

# %%
experiment.instrument.setup_wavelength = 1.6215
experiment.instrument.calib_twotheta_offset = 0.0
experiment.instrument.calib_sample_displacement = 0.03
experiment.instrument.calib_sample_transparency = 0.02

# %% [markdown]
# ### Set Peak Profile
#
# Select the Thompson-Cox-Hastings pseudo-Voigt profile. U, V, and W
# define its Gaussian broadening; Y defines its Lorentzian broadening;
# and the Finger-Cox-Jephcoat terms describe the low-angle asymmetry.

# %%
experiment.peak.show_supported()

# %%
experiment.peak.type = 'thompson-cox-hastings'

# %%
experiment.peak.broad_gauss_u = 0.1
experiment.peak.broad_gauss_v = -0.3
experiment.peak.broad_gauss_w = 0.4
experiment.peak.broad_lorentz_y = 0.1
experiment.peak.asym_fcj_1 = 0.08
experiment.peak.asym_fcj_2 = 0.08

# %% [markdown]
# ### Set Absorption
#
# Apply the Hewat cylindrical-sample absorption correction with an
# approximate value of the dimensionless absorption-radius product.

# %%
experiment.absorption.type = 'cylinder-hewat'
experiment.absorption.mu_r = 0.3

# %% [markdown]
# ### Set Excluded Regions
#
# Exclude the low- and high-angle regions outside the useful measured
# range from 12 to 162 degrees.

# %%
experiment.excluded_regions.create(id='1', start=0.0, end=12.0)
experiment.excluded_regions.create(id='2', start=162.0, end=180.0)

# %% [markdown]
# ### Set Background
#
# Estimate initial background points from the measured pattern.

# %%
experiment.background.show_supported()

# %%
experiment.background.auto_estimate()

# %%
experiment.background.show()

# %% [markdown]
# ### Set Linked Structure
#
# Link the LMO model to the experiment and provide an initial estimate
# for its scale factor.

# %%
experiment.linked_structures.create(structure_id='lmo', scale=10.0)

# %% [markdown]
# ### Inspect Experiment
#
# Display the configured experiment as text.

# %%
experiment.show_as_text()

# %% [markdown]
# ## 🚀 Perform Analysis
#
# Inspect the starting calculation, constrain the coupled site-mixing
# parameters, select the independent refinement parameters, and fit the
# model to the measured pattern.
#
# ### Display Initial Pattern

# %%
project.display.pattern(expt_name='echidna')

# %% [markdown]
# ### Set Constraints
#
# First create readable aliases for the displacement and occupancy
# parameters involved in the constraints.

# %%
project.analysis.aliases.create(
    id='biso_Li1',
    param=structure.atom_sites['Li1'].adp_iso,
)
project.analysis.aliases.create(
    id='biso_Li2',
    param=structure.atom_sites['Li2'].adp_iso,
)
project.analysis.aliases.create(
    id='biso_Ni1',
    param=structure.atom_sites['Ni1'].adp_iso,
)
project.analysis.aliases.create(
    id='biso_Ni2',
    param=structure.atom_sites['Ni2'].adp_iso,
)

project.analysis.aliases.create(
    id='occ_Li1',
    param=structure.atom_sites['Li1'].occupancy,
)
project.analysis.aliases.create(
    id='occ_Li2',
    param=structure.atom_sites['Li2'].occupancy,
)
project.analysis.aliases.create(
    id='occ_Ni1',
    param=structure.atom_sites['Ni1'].occupancy,
)
project.analysis.aliases.create(
    id='occ_Ni2',
    param=structure.atom_sites['Ni2'].occupancy,
)

# %% [markdown]
# Atoms sharing a crystallographic site use the same Biso value. The
# occupancy constraints keep each shared site fully occupied and couple
# the same Li/Ni exchange fraction across both sites. Consequently,
# `occ_Li1` is the only independent occupancy parameter.

# %%
project.analysis.constraints.create(
    id='1',
    expression='biso_Ni1 = biso_Li1',
)
project.analysis.constraints.create(
    id='2',
    expression='biso_Li2 = biso_Ni2',
)
project.analysis.constraints.create(
    id='3',
    expression='occ_Ni1 = 1 - occ_Li1',
)
project.analysis.constraints.create(
    id='4',
    expression='occ_Li2 = 1 - occ_Li1',
)
project.analysis.constraints.create(
    id='5',
    expression='occ_Ni2 = occ_Li1',
)

# %%
project.analysis.constraints.show()

# %% [markdown]
# ### Set Free Parameters
#
# Refine the two independent cell lengths, oxygen z coordinate, the two
# independent cation Biso values, and the independent Li occupancy.

# %%
structure.cell.length_a.free = True
structure.cell.length_c.free = True

structure.atom_sites['O'].fract_z.free = True
structure.atom_sites['Li1'].adp_iso.free = True
structure.atom_sites['Ni2'].adp_iso.free = True
structure.atom_sites['Li1'].occupancy.free = True

# %% [markdown]
# Refine the scale, instrument calibration terms, U/V/W/Y profile terms,
# and active background-point intensities. The asymmetry and absorption
# parameters remain fixed at their approximate values.

# %%
experiment.linked_structures['lmo'].scale.free = True

experiment.instrument.calib_twotheta_offset.free = True
experiment.instrument.calib_sample_displacement.free = True
experiment.instrument.calib_sample_transparency.free = True

experiment.peak.broad_gauss_u.free = True
experiment.peak.broad_gauss_v.free = True
experiment.peak.broad_gauss_w.free = True
experiment.peak.broad_lorentz_y.free = True

for point in experiment.background:
    point.intensity.free = True

# %% [markdown]
# Display all parameters selected for refinement.

# %%
project.display.parameters.free()

# %% [markdown]
# ### Select Minimizer
#
# Use the Levenberg-Marquardt optimizer provided by Bumps.

# %%
project.analysis.minimizer.show_supported()

# %%
project.analysis.minimizer.type = 'bumps (lm)'

# %% [markdown]
# ### Fit Model

# %%
project.analysis.fit()

# %% [markdown]
# ### Inspect Results
#
# Review the fit statistics, refined parameters, and parameter
# correlations, then compare the refined calculation with the data.

# %%
project.display.fit.results()

# %%
project.display.fit.correlations()

# %%
project.display.pattern(expt_name='echidna')

# %% [markdown]
# ## 💾 Save Project
#
# Save the refined parameters and analysis results in the project
# directory created near the beginning of the tutorial.

# %%
project.save()
