# %% [markdown]
# # Tb₂Ti₂O₇ — neutron single crystal, constant wavelength, no extinction

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
structure = StructureFactory.from_scratch(name='tbti')

structure.space_group.name_h_m = 'F d -3 m'  # FullProf Space group symbol

structure.cell.length_a = 10.130  # FullProf a

# Anisotropic sites carry the FullProf β tensor directly: ``adp_type`` is
# set to ``'beta'`` and the dimensionless β components are assigned
# verbatim. F d -3 m is cubic, so site symmetry links the remaining β
# components and only the independent ones are set. FullProf occupancy is
# the site multiplicity over the general multiplicity; CIF/EasyDiffraction
# use 1.0 for a fully occupied site.
structure.atom_sites.create(
    id='Tb',  # FullProf Atom
    type_symbol='Tb',  # FullProf Typ
    fract_x=0.5,  # FullProf X
    fract_y=0.5,  # FullProf Y
    fract_z=0.5,  # FullProf Z
    adp_type='beta',  # FullProf beta tensor
)
aniso = structure.atom_site_aniso['Tb']
aniso.adp_11 = 0.00098991673  # FullProf beta11
aniso.adp_12 = -0.00047650724  # FullProf beta12

structure.atom_sites.create(
    id='Ti',  # FullProf Atom
    type_symbol='Ti',  # FullProf Typ
    fract_x=0,  # FullProf X
    fract_y=0,  # FullProf Y
    fract_z=0,  # FullProf Z
    adp_type='beta',  # FullProf beta tensor
)
aniso = structure.atom_site_aniso['Ti']
aniso.adp_11 = 0.00090989727  # FullProf beta11
aniso.adp_12 = -0.00016990340  # FullProf beta12

structure.atom_sites.create(
    id='O1',  # FullProf Atom
    type_symbol='O',  # FullProf Typ
    fract_x=0.32804,  # FullProf X
    fract_y=0.125,  # FullProf Y
    fract_z=0.125,  # FullProf Z
    adp_type='beta',  # FullProf beta tensor
)
aniso = structure.atom_site_aniso['O1']
aniso.adp_11 = 0.0012294180  # FullProf beta11
aniso.adp_22 = 0.00078215479  # FullProf beta22
aniso.adp_23 = 0.00041246481  # FullProf beta23

structure.atom_sites.create(
    id='O2',  # FullProf Atom
    type_symbol='O',  # FullProf Typ
    fract_x=0.375,  # FullProf X
    fract_y=0.375,  # FullProf Y
    fract_z=0.375,  # FullProf Z
    adp_type='beta',  # FullProf beta tensor
)
aniso = structure.atom_site_aniso['O2']
aniso.adp_11 = 0.00060762477  # FullProf beta11

project.structures.add(structure)

# %%
structure.show_as_cif()

# %% [markdown]
# ## Load the FullProf reference

# %%
FULLPROF_PROJECT_DIR = 'sc-neut-cwl_noext_tbti'
FULLPROF_OUT_FILE = 'tbti.out'
FULLPROF_SCALE = 0.28749475  # FullProf Scale
FULLPROF_WAVELENGTH = 0.7930  # FullProf Lambda

f2calc = verify.load_fullprof_sc_f2calc(FULLPROF_PROJECT_DIR, FULLPROF_OUT_FILE)

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

verify.set_reference_reflections(experiment, f2calc)

project.experiments.add(experiment)

# %% [markdown]
# ## ed-cryspy VS FullProf

# %%
calc_ed_cryspy = verify.calculate_reflections(project, experiment, 'cryspy')
reference, candidate = verify.align_reflections(f2calc, calc_ed_cryspy)

project.display.reflection_comparison(
    'tbti',
    reference=reference,
    candidate=candidate,
    reference_label='FullProf',
    candidate_label='ed-cryspy',
)

# %% [markdown]
# ## Fit ed-cryspy to FullProf

# %%
experiment.calculator.type = 'cryspy'

experiment.linked_structure.scale.free = True

project.analysis.fit()
project.display.fit.results()

calc_ed_cryspy_refined = verify.calculate_reflections(project, experiment, 'cryspy')
reference_refined, candidate_refined = verify.align_reflections(f2calc, calc_ed_cryspy_refined)

project.display.reflection_comparison(
    'tbti',
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
