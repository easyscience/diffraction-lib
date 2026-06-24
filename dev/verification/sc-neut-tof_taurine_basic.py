# %% [markdown]
# # Taurine - single-crystal neutron TOF - basic
#
# Verifies calculated F2 values for a no-extinction neutron
# single-crystal time-of-flight baseline with isotropic ADPs.
#
# **Refinement:** the overall scale only; all other parameters are
# taken from the FullProf reference. Extinction is set to zero in the
# FullProf model so the comparison focuses on the structure-factor
# physics shared by cryspy and FullProf.

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
structure = StructureFactory.from_scratch(name='taurine')

structure.space_group.name_h_m = 'P 21/c'  # FullProf Space group symbol

structure.cell.length_a = 5.272901  # FullProf a
structure.cell.length_b = 11.656488  # FullProf b
structure.cell.length_c = 7.838297  # FullProf c
structure.cell.angle_beta = 94.010994  # FullProf beta

# fmt: off
_ATOMS = [
    ('S1', 'S', 0.19448, 0.35173, 0.34730, 1.37018),
    ('O1', 'O', 0.31207, 0.23951, 0.35143, 2.68011),
    ('O2', 'O', -0.05909, 0.33563, 0.29636, 3.50515),
    ('O3', 'O', 0.22105, 0.41215, 0.50573, 1.83513),
    ('N1', 'N', 0.26340, 0.62808, 0.33048, 2.07364),
    ('H1', 'H', 0.12861, 0.58669, 0.41769, 3.31527),
    ('H2', 'H', 0.18953, 0.71385, 0.31124, 4.46988),
    ('H3', 'H', 0.43970, 0.62023, 0.34592, 4.34151),
    ('C1', 'C', 0.34384, 0.44116, 0.20155, 1.73667),
    ('H11', 'H', 0.55246, 0.43345, 0.24304, 3.32279),
    ('H12', 'H', 0.32537, 0.38970, 0.08264, 3.05746),
    ('C2', 'C', 0.20029, 0.55716, 0.18272, 1.66017),
    ('H21', 'H', 0.27650, 0.60004, 0.07688, 2.15403),
    ('H22', 'H', -0.00383, 0.54767, 0.15762, 4.71303),
]
# fmt: on

for _id, _type, _x, _y, _z, _biso in _ATOMS:
    structure.atom_sites.create(
        id=_id,  # FullProf Atom
        type_symbol=_type,  # FullProf Typ
        fract_x=_x,  # FullProf X
        fract_y=_y,  # FullProf Y
        fract_z=_z,  # FullProf Z
        adp_type='Biso',  # FullProf Biso
        adp_iso=_biso,  # FullProf Biso
    )

project.structures.add(structure)

# %%
structure.show_as_text()

# %% [markdown]
# ## Load the FullProf reference

# %%
FULLPROF_PROJECT_DIR = 'sc-neut-tof_taurine_basic'
FULLPROF_OUT_FILE = 'taurine.out'
FULLPROF_SCALE = 2.711  # FullProf Scale

f2calc = verify.load_fullprof_sc_f2calc(FULLPROF_PROJECT_DIR, FULLPROF_OUT_FILE)
FULLPROF_LABEL = verify.fullprof_label(FULLPROF_PROJECT_DIR, FULLPROF_OUT_FILE)

# %% [markdown]
# ## Create the experiment

# %%
experiment = ExperimentFactory.from_scratch(
    name='taurine',
    sample_form='single crystal',
    beam_mode='time-of-flight',
    radiation_probe='neutron',
    scattering_type='bragg',
)

experiment.linked_structure.structure_id = 'taurine'
experiment.linked_structure.scale = FULLPROF_SCALE

verify.set_reference_reflections(experiment, f2calc)

project.experiments.add(experiment)

# %% [markdown]
# ## edi-cryspy VS FullProf

# %%
calc_ed_cryspy = verify.calculate_reflections(project, experiment, 'cryspy')
LABEL_ED_CRYSPY = verify.engine_label('cryspy')
reference, candidate = verify.align_reflections(f2calc, calc_ed_cryspy)

project.display.reflection_comparison(
    'taurine',
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
    'taurine',
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
