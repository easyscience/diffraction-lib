# %% [markdown]
# # Pr₂NiO₄ — neutron single crystal, constant wavelength

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
structure = StructureFactory.from_scratch(name='pr2nio4')
structure.space_group.name_h_m = 'F m m m'  # FullProf Space group symbol
structure.cell.length_a = 5.417799  # FullProf a
structure.cell.length_b = 5.414600  # FullProf b
structure.cell.length_c = 12.483399  # FullProf c

cell_lengths = (
    structure.cell.length_a.value,
    structure.cell.length_b.value,
    structure.cell.length_c.value,
)


def beta_to_u(beta: float, axis_i: int, axis_j: int) -> float:
    """Convert a FullProf β component to the CIF U convention."""
    return beta * cell_lengths[axis_i] * cell_lengths[axis_j] / (2.0 * np.pi**2)


# label, type, (x, y, z), CIF occupancy, β11, β22, β33, β12
aniso_sites = [
    ('Pr', 'Pr', (0.50000, 0.50000, 0.35973), 1.000000, 0.00710, 0.00710, 0.00084, 0.00000),
    ('Ni', 'Ni', (0.00000, 0.00000, 0.00000), 1.000000, 0.00280, 0.00280, 0.00151, 0.00000),
    ('O1', 'O', (0.25000, 0.25000, 0.00000), 1.000000, 0.00500, 0.00500, 0.00413, -0.00140),
    ('O2', 'O', (0.00000, 0.00000, 0.17385), 0.701385, 0.01716, 0.01716, 0.00045, 0.00000),
    ('Oi', 'O', (0.25000, 0.25000, 0.25000), 0.074655, 0.01044, 0.01177, 0.00098, 0.00000),
]
for label, symbol, (x, y, z), occupancy, beta_11, beta_22, beta_33, beta_12 in aniso_sites:
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

# The split interstitial oxygen Od is refined with an isotropic B.
structure.atom_sites.create(
    label='Od', type_symbol='O', fract_x=0.07347, fract_y=0.07347, fract_z=0.17349, adp_iso=0.0
)
structure.atom_sites['Od'].occupancy = 0.074654
structure.atom_sites['Od'].adp_type = 'Biso'
structure.atom_sites['Od'].adp_iso = 2.31435

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
    candidate_label='ed-cryspy (refined)',
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
