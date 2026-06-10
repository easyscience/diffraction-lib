# %% [markdown]
# # Tb2Ti2O7 — neutron single crystal, constant wavelength

# %%
import numpy as np

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
structure.cell.length_b = 10.130  # FullProf b
structure.cell.length_c = 10.130  # FullProf c

cell_lengths = (
    structure.cell.length_a.value,
    structure.cell.length_b.value,
    structure.cell.length_c.value,
)


def beta_to_u(beta: float, axis_i: int, axis_j: int) -> float:
    """Convert a FullProf β component to the CIF U convention."""
    return beta * cell_lengths[axis_i] * cell_lengths[axis_j] / (2.0 * np.pi**2)


# label, type, (x, y, z), CIF occupancy, β11, β22, β33, β12, β13, β23
# FullProf occupancy is site-multiplicity divided by general-multiplicity.
# EasyDiffraction/CIF files use occupancy=1.0 for fully occupied sites.
anisotropic_sites = [
    ('Tb', 'Tb', (0.50000, 0.50000, 0.50000), 1.0, 0.00098991673, 0.00098991673, 0.00098991673, -0.00047650724, -0.00047650724, -0.00047650724),
    ('Ti', 'Ti', (0.00000, 0.00000, 0.00000), 1.0, 0.00090989727, 0.00090989727, 0.00090989727, -0.00016990340, -0.00016990340, -0.00016990340),
    ('O1', 'O', (0.32804, 0.12500, 0.12500), 1.0, 0.0012294180, 0.00078215479, 0.00078215479, 0.00000, 0.00000, 0.00041246481),
    ('O2', 'O', (0.37500, 0.37500, 0.37500), 1.0, 0.00060762477, 0.00060762477, 0.00060762477, 0.00000, 0.00000, 0.00000),
]
for label, symbol, (x, y, z), occupancy, beta_11, beta_22, beta_33, beta_12, beta_13, beta_23 in anisotropic_sites:
    structure.atom_sites.create(
        label=label, type_symbol=symbol, fract_x=x, fract_y=y, fract_z=z, adp_iso=0.0
    )
    structure.atom_sites[label].occupancy = occupancy
    structure.atom_sites[label].adp_type = 'Uani'
    aniso = structure.atom_site_aniso[label]
    aniso.adp_11 = beta_to_u(beta_11, 0, 0)
    aniso.adp_22 = beta_to_u(beta_22, 1, 1)
    aniso.adp_33 = beta_to_u(beta_33, 2, 2)
    aniso.adp_12 = beta_to_u(beta_12, 0, 1)
    aniso.adp_13 = beta_to_u(beta_13, 0, 2)
    aniso.adp_23 = beta_to_u(beta_23, 1, 2)

project.structures.add(structure)

# %% [markdown]
# ## Load the FullProf reference

# %%
FULLPROF_PROJECT_DIR = 'sg-neut-cwl_noext_tbti'
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
experiment.linked_crystal.id = 'tbti'
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

experiment.linked_crystal.scale.free = True

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
