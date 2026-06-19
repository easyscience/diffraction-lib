# %% [markdown]
# # Tb2Ti2O7 - single-crystal neutron CW - isotropic extinction
#
# Verifies the cryspy isotropic extinction model against a FullProf
# single-crystal reference with isotropic ADPs.
#
# **Refinement:** the overall scale and the extinction radius. Known
# difference: cryspy and FullProf use different extinction conventions.

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
structure = StructureFactory.from_scratch(name='tbti')

structure.space_group.name_h_m = 'F d -3 m'  # FullProf Space group symbol

structure.cell.length_a = 10.130  # FullProf a

structure.atom_sites.create(
    id='Tb',  # FullProf Atom
    type_symbol='Tb',  # FullProf Typ
    fract_x=0.5,  # FullProf X
    fract_y=0.5,  # FullProf Y
    fract_z=0.5,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=0.0,  # FullProf Biso
)
structure.atom_sites.create(
    id='Ti',  # FullProf Atom
    type_symbol='Ti',  # FullProf Typ
    fract_x=0.0,  # FullProf X
    fract_y=0.0,  # FullProf Y
    fract_z=0.0,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=0.0,  # FullProf Biso
)
structure.atom_sites.create(
    id='O1',  # FullProf Atom
    type_symbol='O',  # FullProf Typ
    fract_x=0.32804,  # FullProf X
    fract_y=0.125,  # FullProf Y
    fract_z=0.125,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=0.0,  # FullProf Biso
)
structure.atom_sites.create(
    id='O2',  # FullProf Atom
    type_symbol='O',  # FullProf Typ
    fract_x=0.375,  # FullProf X
    fract_y=0.375,  # FullProf Y
    fract_z=0.375,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=0.0,  # FullProf Biso
)

project.structures.add(structure)

# %%
structure.show_as_text()

# %% [markdown]
# ## Load the FullProf reference

# %%
FULLPROF_PROJECT_DIR = 'sc-neut-cwl_tbti_isotropic-extinction'
FULLPROF_OUT_FILE = 'tbti.out'
FULLPROF_SCALE = 0.2609  # FullProf Scale
FULLPROF_WAVELENGTH = 0.7930  # FullProf Lambda
# cryspy uses Becker-Coppens isotropic extinction, not the one from
# FullProf.
EXTINCTION_RADIUS = 10.0
EXTINCTION_MOSAICITY = 35000.0

f2calc = verify.load_fullprof_sc_f2calc(FULLPROF_PROJECT_DIR, FULLPROF_OUT_FILE)
FULLPROF_LABEL = verify.fullprof_label(FULLPROF_PROJECT_DIR, FULLPROF_OUT_FILE)

# %% [markdown]
# ## Create the experiment

# %%
experiment = ExperimentFactory.from_scratch(
    name='tbti',
    sample_form='single crystal',
    beam_mode='constant wavelength',
    radiation_probe='neutron',
    scattering_type='bragg',
)
experiment.linked_structure.structure_id = 'tbti'
experiment.linked_structure.scale = FULLPROF_SCALE
experiment.instrument.setup_wavelength = FULLPROF_WAVELENGTH
experiment.extinction.type = 'becker-coppens'
experiment.extinction.model = 'gauss'
experiment.extinction.radius.value = EXTINCTION_RADIUS
experiment.extinction.mosaicity.value = EXTINCTION_MOSAICITY

verify.set_reference_reflections(experiment, f2calc)

project.experiments.add(experiment)

# %% [markdown]
# ## edi-cryspy VS FullProf

# %%
calc_ed_cryspy = verify.calculate_reflections(project, experiment, 'cryspy')
LABEL_ED_CRYSPY = verify.engine_label('cryspy')
reference, candidate = verify.align_reflections(f2calc, calc_ed_cryspy)

project.display.reflection_comparison(
    'tbti',
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
experiment.extinction.radius.free = True

project.analysis.fit()
project.display.fit.results()

calc_ed_cryspy_refined = verify.calculate_reflections(project, experiment, 'cryspy')
LABEL_ED_CRYSPY_REFINED = verify.engine_label('cryspy', note='scale + ext radius')
reference_refined, candidate_refined = verify.align_reflections(f2calc, calc_ed_cryspy_refined)

project.display.reflection_comparison(
    'tbti',
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
verify.assert_patterns_agree(
    [
        (f'{LABEL_ED_CRYSPY_REFINED} vs {FULLPROF_LABEL}', reference_refined, candidate_refined),
    ],
    known_discrepancy=True,
    reason='cryspy and FullProf use different extinction conventions.',
)
