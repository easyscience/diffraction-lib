# %% [markdown]
# # Pr₂NiO₄ — neutron single crystal, constant wavelength

# %%
import easydiffraction as ed
from easydiffraction import ExperimentFactory
from easydiffraction import StructureFactory
from easydiffraction.analysis import verification as verify

# %% [markdown]
# ## Build the project

# %%
project = ed.Project()

# %% [markdown]
# ## Define the structure

# %%
structure = StructureFactory.from_scratch(name='pr2nio4')

structure.space_group.name_h_m = 'F m m m'  # FullProf Space group symbol

structure.cell.length_a = 5.417799  # FullProf a
structure.cell.length_b = 5.414600  # FullProf b
structure.cell.length_c = 12.483399  # FullProf c

# Anisotropic sites carry the FullProf β tensor directly: ``adp_type`` is
# set to ``'beta'`` after the atom is added (the type switch needs the
# unit cell), then the dimensionless β components are assigned verbatim.
# F m m m is orthorhombic, so β11, β22, β33 are independent — each is set
# explicitly rather than left to a symmetry constraint. FullProf
# occupancy folds in the site multiplicity; the chemical occupancy here
# is the FullProf Occ scaled by the multiplicity (1.0 for a full site).
structure.atom_sites.create(
    label='Pr',  # FullProf Atom
    type_symbol='Pr',  # FullProf Typ
    fract_x=0.50000,  # FullProf X
    fract_y=0.50000,  # FullProf Y
    fract_z=0.35973,  # FullProf Z
)
structure.atom_sites['Pr'].adp_type = 'beta'  # FullProf β tensor
aniso = structure.atom_site_aniso['Pr']
aniso.adp_11 = 0.00710  # FullProf β11
aniso.adp_22 = 0.00710  # FullProf β22
aniso.adp_33 = 0.00084  # FullProf β33

structure.atom_sites.create(
    label='Ni',  # FullProf Atom
    type_symbol='Ni',  # FullProf Typ
    fract_x=0.00000,  # FullProf X
    fract_y=0.00000,  # FullProf Y
    fract_z=0.00000,  # FullProf Z
)
structure.atom_sites['Ni'].adp_type = 'beta'  # FullProf β tensor
aniso = structure.atom_site_aniso['Ni']
aniso.adp_11 = 0.00280  # FullProf β11
aniso.adp_22 = 0.00280  # FullProf β22
aniso.adp_33 = 0.00151  # FullProf β33

structure.atom_sites.create(
    label='O1',  # FullProf Atom
    type_symbol='O',  # FullProf Typ
    fract_x=0.25000,  # FullProf X
    fract_y=0.25000,  # FullProf Y
    fract_z=0.00000,  # FullProf Z
)
structure.atom_sites['O1'].adp_type = 'beta'  # FullProf β tensor
aniso = structure.atom_site_aniso['O1']
aniso.adp_11 = 0.00500  # FullProf β11
aniso.adp_22 = 0.00500  # FullProf β22
aniso.adp_33 = 0.00413  # FullProf β33
aniso.adp_12 = -0.00140  # FullProf β12

structure.atom_sites.create(
    label='O2',  # FullProf Atom
    type_symbol='O',  # FullProf Typ
    fract_x=0.00000,  # FullProf X
    fract_y=0.00000,  # FullProf Y
    fract_z=0.17385,  # FullProf Z
    occupancy=0.722965,  # FullProf Occ 1.44593 / multiplicity
)
structure.atom_sites['O2'].adp_type = 'beta'  # FullProf β tensor
aniso = structure.atom_site_aniso['O2']
aniso.adp_11 = 0.01716  # FullProf β11
aniso.adp_22 = 0.01716  # FullProf β22
aniso.adp_33 = 0.00045  # FullProf β33

structure.atom_sites.create(
    label='Oi',  # FullProf Atom
    type_symbol='O',  # FullProf Typ
    fract_x=0.25000,  # FullProf X
    fract_y=0.25000,  # FullProf Y
    fract_z=0.25000,  # FullProf Z
    occupancy=0.074655,  # FullProf Occ 0.14931 / multiplicity
)
structure.atom_sites['Oi'].adp_type = 'beta'  # FullProf β tensor
aniso = structure.atom_site_aniso['Oi']
aniso.adp_11 = 0.01033  # FullProf β11
aniso.adp_22 = 0.01176  # FullProf β22
aniso.adp_33 = 0.00100  # FullProf β33

# The split interstitial oxygen Od is refined with an isotropic B.
structure.atom_sites.create(
    label='Od',  # FullProf Atom
    type_symbol='O',  # FullProf Typ
    fract_x=0.07347,  # FullProf X
    fract_y=0.07347,  # FullProf Y
    fract_z=0.17349,  # FullProf Z
    occupancy=0.074654,  # FullProf Occ 0.59723 / multiplicity
    adp_type='Biso',  # FullProf Biso
    adp_iso=2.31435,  # FullProf Biso
)

project.structures.add(structure)

# %% [markdown]
# ## Load the FullProf reference

# %%
FULLPROF_PROJECT_DIR = 'sg-neut-cwl_pr2nio4'
FULLPROF_OUT_FILE = 'prnio.out'
FULLPROF_SCALE = 0.06298  # FullProf Scale
FULLPROF_WAVELENGTH = 0.8302  # FullProf Lambda

f2calc = verify.load_fullprof_sc_f2calc(FULLPROF_PROJECT_DIR, FULLPROF_OUT_FILE)

# %% [markdown]
# ## Create the experiment

# %%
experiment = ExperimentFactory.from_scratch(
    name='pr2nio4',
    sample_form='single crystal',
    beam_mode='constant wavelength',
    radiation_probe='neutron',
    scattering_type='bragg',
)
experiment.linked_crystal.id = 'pr2nio4'
experiment.linked_crystal.scale = FULLPROF_SCALE
experiment.instrument.setup_wavelength = FULLPROF_WAVELENGTH
verify.set_reference_reflections(experiment, f2calc)

project.experiments.add(experiment)

# %% [markdown]
# ## ed-cryspy VS FullProf

# %%
calc_ed_cryspy = verify.calculate_reflections(project, experiment, 'cryspy')
reference, candidate = verify.align_reflections(f2calc, calc_ed_cryspy)

project.display.reflection_comparison(
    'pr2nio4',
    reference=reference,
    candidate=candidate,
    reference_label='FullProf',
    candidate_label='ed-cryspy',
)

# %% [markdown]
# ## Fit ed-cryspy to FullProf

# %%
experiment.calculator.type = 'cryspy'
experiment.linked_crystal.scale.free = True

project.analysis.fit()
project.display.fit.results()

calc_ed_cryspy_refined = verify.calculate_reflections(project, experiment, 'cryspy')
reference_refined, candidate_refined = verify.align_reflections(f2calc, calc_ed_cryspy_refined)

project.display.reflection_comparison(
    'pr2nio4',
    reference=reference_refined,
    candidate=candidate_refined,
    reference_label='FullProf',
    candidate_label='ed-cryspy (scale only)',
)

verify.report_refinement_closeness(
    reference,
    candidate,
    candidate_refined,
)

# %% [markdown]
# ## Agreement check

# %%
verify.assert_patterns_agree(
    [
        ('cryspy vs FullProf', reference_refined, candidate_refined),
    ],
    raise_on_failure=False,
)
