# %% [markdown]
# # Pr₂NiO₄ — single-crystal neutron CW — basic
#
# Verifies calculated F² values for a constant-wavelength neutron
# single-crystal reference with anisotropic ADPs.
#
# **Refinement:** the overall scale only; all other parameters are
# taken from the FullProf reference.

# %%
import easydiffraction as edi
from easydiffraction import ExperimentFactory
from easydiffraction import StructureFactory
from easydiffraction.analysis import verification as verify

# %% [markdown]
# ## Build the project

# %%
project = edi.Project()

# %% [markdown]
# ## Define the structure

# %%
structure = StructureFactory.from_scratch(name='pr2nio4')

structure.space_group.name_h_m = 'F m m m'  # FullProf Space group symbol

structure.cell.length_a = 5.417799  # FullProf a
structure.cell.length_b = 5.414600  # FullProf b
structure.cell.length_c = 12.483399  # FullProf c

# Anisotropic sites carry the FullProf β tensor directly: ``adp_type`` is
# set to ``'beta'`` and the dimensionless β components are assigned
# verbatim. F m m m is orthorhombic, so β11, β22, β33 are independent —
# each is set explicitly rather than left to a symmetry constraint.
# FullProf occupancy folds in the site multiplicity; the chemical
# occupancy here is the FullProf Occ scaled by the multiplicity (1.0 for
# a full site).
structure.atom_sites.create(
    id='Pr',  # FullProf Atom
    type_symbol='Pr',  # FullProf Typ
    fract_x=0.5,  # FullProf X
    fract_y=0.5,  # FullProf Y
    fract_z=0.35973,  # FullProf Z
    adp_type='beta',  # FullProf beta tensor
)
aniso = structure.atom_site_aniso['Pr']
aniso.adp_11 = 0.00710  # FullProf beta11
aniso.adp_22 = 0.00710  # FullProf beta22
aniso.adp_33 = 0.00084  # FullProf beta33

structure.atom_sites.create(
    id='Ni',  # FullProf Atom
    type_symbol='Ni',  # FullProf Typ
    fract_x=0,  # FullProf X
    fract_y=0,  # FullProf Y
    fract_z=0,  # FullProf Z
    adp_type='beta',  # FullProf beta tensor
)
aniso = structure.atom_site_aniso['Ni']
aniso.adp_11 = 0.00280  # FullProf beta11
aniso.adp_22 = 0.00280  # FullProf beta22
aniso.adp_33 = 0.00151  # FullProf beta33

structure.atom_sites.create(
    id='O1',  # FullProf Atom
    type_symbol='O',  # FullProf Typ
    fract_x=0.25,  # FullProf X
    fract_y=0.25,  # FullProf Y
    fract_z=0,  # FullProf Z
    adp_type='beta',  # FullProf beta tensor
)
aniso = structure.atom_site_aniso['O1']
aniso.adp_11 = 0.00500  # FullProf beta11
aniso.adp_22 = 0.00500  # FullProf beta22
aniso.adp_33 = 0.00413  # FullProf beta33
aniso.adp_12 = -0.00140  # FullProf beta12

structure.atom_sites.create(
    id='O2',  # FullProf Atom
    type_symbol='O',  # FullProf Typ
    fract_x=0,  # FullProf X
    fract_y=0,  # FullProf Y
    fract_z=0.17385,  # FullProf Z
    occupancy=0.722965,  # FullProf Occ 1.44593 / multiplicity
    adp_type='beta',  # FullProf beta tensor
)
aniso = structure.atom_site_aniso['O2']
aniso.adp_11 = 0.01716  # FullProf beta11
aniso.adp_22 = 0.01716  # FullProf beta22
aniso.adp_33 = 0.00045  # FullProf beta33

structure.atom_sites.create(
    id='Oi',  # FullProf Atom
    type_symbol='O',  # FullProf Typ
    fract_x=0.25,  # FullProf X
    fract_y=0.25,  # FullProf Y
    fract_z=0.25,  # FullProf Z
    occupancy=0.074655,  # FullProf Occ 0.14931 / multiplicity
    adp_type='beta',  # FullProf beta tensor
)
aniso = structure.atom_site_aniso['Oi']
aniso.adp_11 = 0.01033  # FullProf beta11
aniso.adp_22 = 0.01176  # FullProf beta22
aniso.adp_33 = 0.00100  # FullProf beta33

# The split interstitial oxygen Od is refined with an isotropic B.
structure.atom_sites.create(
    id='Od',  # FullProf Atom
    type_symbol='O',  # FullProf Typ
    fract_x=0.07347,  # FullProf X
    fract_y=0.07347,  # FullProf Y
    fract_z=0.17349,  # FullProf Z
    occupancy=0.074654,  # FullProf Occ 0.59723 / multiplicity
    adp_type='Biso',  # FullProf Biso
    adp_iso=2.31435,  # FullProf Biso
)

project.structures.add(structure)

# %%
structure.show_as_text()

# %% [markdown]
# ## Load the FullProf reference

# %%
FULLPROF_PROJECT_DIR = 'sc-neut-cwl_pr2nio4_basic'
FULLPROF_OUT_FILE = 'prnio.out'
FULLPROF_SCALE = 4.031  # FullProf Scale
FULLPROF_WAVELENGTH = 0.8302  # FullProf Lambda

f2calc = verify.load_fullprof_sc_f2calc(FULLPROF_PROJECT_DIR, FULLPROF_OUT_FILE)
FULLPROF_LABEL = verify.fullprof_label(FULLPROF_PROJECT_DIR, FULLPROF_OUT_FILE)

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

experiment.linked_structure.structure_id = 'pr2nio4'
experiment.linked_structure.scale = FULLPROF_SCALE
experiment.instrument.setup_wavelength = FULLPROF_WAVELENGTH

verify.set_reference_reflections(experiment, f2calc)

project.experiments.add(experiment)

# %% [markdown]
# ## edi-cryspy VS FullProf

# %%
calc_ed_cryspy = verify.calculate_reflections(project, experiment, 'cryspy')
LABEL_ED_CRYSPY = verify.engine_label('cryspy')
reference, candidate = verify.align_reflections(f2calc, calc_ed_cryspy)

project.display.reflection_comparison(
    'pr2nio4',
    reference=reference,
    candidate=candidate,
    reference_label=FULLPROF_LABEL,
    candidate_label=LABEL_ED_CRYSPY,
)

# %% [markdown]
# ## Fit edi-cryspy to FullProf

# %%
experiment.calculator.type = 'cryspy'

experiment.linked_structure.scale.free = True

project.analysis.fit()
project.display.fit.results()

calc_ed_cryspy_refined = verify.calculate_reflections(project, experiment, 'cryspy')
LABEL_ED_CRYSPY_REFINED = verify.engine_label('cryspy', note='scale only')
reference_refined, candidate_refined = verify.align_reflections(f2calc, calc_ed_cryspy_refined)

project.display.reflection_comparison(
    'pr2nio4',
    reference=reference_refined,
    candidate=candidate_refined,
    reference_label=FULLPROF_LABEL,
    candidate_label=LABEL_ED_CRYSPY_REFINED,
)

verify.report_refinement_closeness(
    reference,
    candidate,
    candidate_refined,
)

# %% [markdown]
# ## Agreement check

# %%
verify.assert_patterns_agree([
    (f'{LABEL_ED_CRYSPY_REFINED} vs {FULLPROF_LABEL}', reference_refined, candidate_refined),
])
