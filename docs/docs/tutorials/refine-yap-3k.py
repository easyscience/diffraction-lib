# %% [markdown]
# # Structure Refinement: YAlO3+Al2O3, SPODI
#
# This example demonstrates a staged two-phase Rietveld refinement of
# yttrium aluminium perovskite YAlO3 (or YAP) with a small Al2O3
# impurity using constant wavelength neutron powder diffraction data
# measured at 3 K on SPODI at MLZ.
#
# The workflow defines both structures, configures the experiment, and
# refines the cell, scale, profile, background, and atom parameters of
# both phases in stages.

# %% [markdown]
# ## 🛠️ Import Library

# %%
import easydiffraction as edi

# %% [markdown]
# ## 📦 Define Project
#
# ### Create Project

# %%
project = edi.Project(
    name='yap_3k',
    description='Two-phase YAlO3 and Al2O3 refinement using 3 K data from SPODI at MLZ.',
)

# %% [markdown]
# ### Save Initial Project

# %%
project.save_as(dir_path='projects/refine-yap-3k')

# %% [markdown]
# ## 🧩 Define Structures
#
# ### Create Structure 1: YAlO3
#
# Preserve the orthorhombic Pbnm setting used in FullProf. In
# EasyDiffraction this is represented by the standard space-group
# symbol `P n m a` with coordinate-system code `cab`. The cell axes and
# atom coordinates below therefore stay in the original Pbnm setting.
#
# FullProf's PCR occupancies include the site multiplicity divided by
# the general-position multiplicity. Here each atom site is fully
# occupied: the PCR values 0.5 for Y, Al, and O1, and 1.0 for O2, all
# become an occupancy of 1.0. Displacement parameters are entered as
# Biso, matching the PCR file.

# %%
yap_cif = """
data_yap

_cell.length_a 5.18
_cell.length_b 5.33
_cell.length_c 7.37
_cell.angle_alpha 90.
_cell.angle_beta 90.
_cell.angle_gamma 90.

_space_group.name_h_m "P n m a"
_space_group.coord_system_code cab

loop_
_atom_site.id
_atom_site.type_symbol
_atom_site.fract_x
_atom_site.fract_y
_atom_site.fract_z
_atom_site.occupancy
_atom_site.adp_iso
_atom_site.adp_type
Y  Y   0.0100  0.5500 0.2500 1.0 0.12 Biso
Al Al  0.0000  0.0000 0.0000 1.0 0.13 Biso
O1 O  -0.0800 -0.0200 0.2500 1.0 0.06 Biso
O2 O   0.2000  0.2900 0.0400 1.0 0.14 Biso
"""

# %%
project.structures.add_from_cif_str(yap_cif)

# %%
yap = project.structures['yap']

# %% [markdown]
# ### Display Structure 1: YAlO3

# %%
yap.show_as_text()

# %%
project.display.structure(struct_name='yap')

# %% [markdown]
# ### Create Structure 2: Al2O3
#
# Define the corundum impurity in the hexagonal setting of R-3c. The
# FullProf PCR occupancies of 2/3 for Al and 1 for O also describe fully
# occupied sites. Refine its two independent cell lengths, Al z and O x
# coordinates, and both Biso values, as specified by the PCR codewords.
# The PCR contains a negative Al Biso. EasyDiffraction requires a
# nonnegative input value, so start this parameter at 0.1 Å² and refine
# it alongside O Biso.

# %%
alumina = edi.StructureFactory.from_scratch(name='alumina')

# %% [markdown]
# #### Set Space Group

# %%
alumina.space_group.name_h_m = 'R -3 c'
alumina.space_group.coord_system_code = 'h'

# %% [markdown]
# #### Set Unit Cell

# %%
alumina.cell.length_a = 4.75
alumina.cell.length_c = 12.95

# %% [markdown]
# #### Set Atom Sites

# %%
alumina.atom_sites.create(
    id='Al1',
    type_symbol='Al',
    fract_x=0.0,
    fract_y=0.0,
    fract_z=0.33351,
    occupancy=1.0,
    adp_type='Biso',
    adp_iso=0.1,
)
alumina.atom_sites.create(
    id='O1',
    type_symbol='O',
    fract_x=0.3503,
    fract_y=0.0,
    fract_z=0.25,
    occupancy=1.0,
    adp_type='Biso',
    adp_iso=1.22884,
)

# %%
project.structures.add(alumina)

# %% [markdown]
# ### Display Structure 2: Al2O3

# %%
alumina.show_as_text()

# %%
project.display.structure(struct_name='alumina')

# %% [markdown]
# ## 🔬 Define Experiment
#
# ### Download Measured Data
#
# Download the YAlO3 + Al2O3 pattern from the EasyDiffraction online
# data repository. The three columns contain 2-theta in degrees,
# intensity, and its standard uncertainty. They are copied from the
# original SPODI dataset without changing the measured values.

# %%
data_path = edi.download_data('meas-yap-spodi', destination='data')

# %%
project.experiments.add_from_data_path(
    name='yap_3k',
    data_path=data_path,
    sample_form='powder',
    beam_mode='constant wavelength',
    radiation_probe='neutron',
)

# %%
expt = project.experiments['yap_3k']

# %% [markdown]
# ### Set Instrument
#
# Use the neutron wavelength reported for the SPODI dataset and start
# with zero 2-theta offset.

# %%
expt.instrument.setup_wavelength = 1.54816
expt.instrument.calib_twotheta_offset = 0.0

# %% [markdown]
# ### Set Peak Profile
#
# Use a pseudo-Voigt profile with Bérar-Baldinozzi asymmetry.

# %%
expt.peak.show_supported()

# %%
expt.peak.type = 'pseudo-voigt + berar-baldinozzi asymmetry'

# %%
expt.peak.broad_gauss_u = 0.04
expt.peak.broad_gauss_v = -0.05
expt.peak.broad_gauss_w = 0.10
expt.peak.broad_lorentz_x = 0.0
expt.peak.broad_lorentz_y = 0.01

# %%
expt.peak.asym_beba_a0 = 0.0
expt.peak.asym_beba_b0 = 0.0
expt.peak.asym_beba_a1 = 0.0
expt.peak.asym_beba_b1 = 0.0

# %%
expt.peak.cutoff_fwhm = 8.0

# %% [markdown]
# ### Set Absorption
#
# Apply the cylindrical-sample Hewat correction with the absorption
# radius product from FullProf.

# %%
expt.absorption.type = 'cylinder-hewat'
expt.absorption.mu_r = 0.0221

# %% [markdown]
# ### Set Excluded Regions

# %%
expt.excluded_regions.create(id='1', start=0.0, end=4.0)
expt.excluded_regions.create(id='2', start=153.95, end=180.0)

# %% [markdown]
# ### Set Background
#
# Estimate the initial line-segment background from the measured pattern.
# This first estimate does not use a calculated structural model.

# %%
expt.background.auto_estimate(use_model=False)

# %%
expt.background.show()

# %% [markdown]
# ### Set Linked Structures
#
# Give each phase an independent scale factor. Scale factors are fitted
# intensity multipliers, rather than phase weight fractions.

# %%
expt.linked_structures.create(structure_id='yap', scale=30)
expt.linked_structures.create(structure_id='alumina', scale=0.1)

# %%
expt.show_as_text()

# %% [markdown]
# ## 🚀 Perform Analysis
#
# ### Display Initial Pattern

# %%
project.display.pattern(expt_name='yap_3k')


# %%
project.display.pattern(expt_name='yap_3k', x_min=134, x_max=146)

# %% [markdown]
# ### Select Calculator

# %%
expt.calculator.show_supported()

# %%
expt.calculator.type = 'cryspy'

# %% [markdown]
# ### Select Minimizer

# %%
project.analysis.minimizer.show_supported()

# %%
project.analysis.minimizer.type = 'bumps (lm)'

# %%
project.analysis.minimizer.max_iterations = 500
project.analysis.minimizer.chi_square_change_tolerance = 1e-2

# %% [markdown]
# ### Perform Fit 1/3: Cell, Scale, and Background
#
# First refine the independent cell lengths of both phases, both phase
# scales, the instrument zero offset, and the automatically estimated
# background intensities. Hexagonal symmetry couples the Al2O3 b length
# to a, leaving only a and c independent.

# %%
yap.cell.length_a.free = True
yap.cell.length_b.free = True
yap.cell.length_c.free = True

alumina.cell.length_a.free = True
alumina.cell.length_c.free = True

expt.linked_structures['yap'].scale.free = True
expt.linked_structures['alumina'].scale.free = True

expt.instrument.calib_twotheta_offset.free = True

for point in expt.background:
    point.intensity.free = True

# %%
project.display.parameters.free()

# %%
project.analysis.fit()

# %%
project.display.fit.results()

# %% [markdown]
# ### Perform Fit 2/3: Peak Profile
#
# Add the Gaussian and Lorentzian broadening and asymmetry parameters
# to the refinement. The background intensities remain free.

# %%
expt.peak.broad_gauss_u.free = True
expt.peak.broad_gauss_v.free = True
expt.peak.broad_gauss_w.free = True
expt.peak.broad_lorentz_y.free = True

expt.peak.asym_beba_a0.free = True
# expt.peak.asym_beba_b0.free = True
# expt.peak.asym_beba_a1.free = True
expt.peak.asym_beba_b1.free = True

# %%
project.display.parameters.free()

# %%
project.analysis.fit()

# %%
project.display.fit.results()

# %% [markdown]
# ### Perform Fit 3/3: Model-Guided Background and Atom Parameters
#
# Replace the initial background with a new estimate based on the fitted
# peak model. Automatically generated points are fixed by default, so
# mark their intensities free before fitting them with the atom parameters.

# %%
expt.background.auto_estimate(use_model=True)

# %%
expt.background.show()

# %%
for point in expt.background:
    point.intensity.free = True

# %% [markdown]
# Refine the independent Y and O coordinates in Pbnm and the
# isotropic displacement parameters of both phases. Symmetry keeps Y
# and O1 in YAlO3 at z = 1/4 and Al at the origin. For Al2O3, refine
# Al1 z and O1 x. Occupancies remain fixed
# at 1.0, and all coordinates fixed by symmetry remain fixed.

# %%
yap.atom_sites['Y'].fract_x.free = True
yap.atom_sites['Y'].fract_y.free = True
yap.atom_sites['O1'].fract_x.free = True
yap.atom_sites['O1'].fract_y.free = True
yap.atom_sites['O2'].fract_x.free = True
yap.atom_sites['O2'].fract_y.free = True
yap.atom_sites['O2'].fract_z.free = True

alumina.atom_sites['Al1'].fract_z.free = True
alumina.atom_sites['O1'].fract_x.free = True

for structure in (yap, alumina):
    for atom in structure.atom_sites:
        atom.adp_iso.free = True

# %%
project.display.parameters.free()

# %%
project.analysis.fit()

# %% [markdown]
# ### Inspect Results
#
# Review the fit statistics, refined parameters, and correlations.
# Inspect the full pattern and a closer view with impurity reflections.

# %%
project.display.fit.results()

# %%
project.display.fit.correlations()

# %%
project.display.pattern(expt_name='yap_3k')

# %%
project.display.pattern(expt_name='yap_3k', x_min=134, x_max=146)

# %% [markdown]
# ## 💾 Save Project
#
# Save the refined model and analysis results in the project directory.

# %%
project.save()
