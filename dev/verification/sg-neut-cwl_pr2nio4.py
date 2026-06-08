# %% [markdown]
# # Pr₂NiO₄ — neutron single crystal, constant wavelength
#
# This page verifies the EasyDiffraction `cryspy` single-crystal
# structure-factor calculation against **FullProf**, using the real
# Pr₂NiO₄:Sr crystal-option refinement from
# [cryspy issue #38](https://github.com/ikibalin/cryspy/issues/38). The
# structure is built **in code**, the calculated F² of every reflection
# is taken straight from the FullProf `.out` file, and the two are
# overlaid on a y=x scatter — **without any fitting**. Single-crystal
# Bragg calculations are supported by `cryspy` only, so `crysfml` and
# FullProf-vs-`crysfml` panels are omitted here.
#
# The FullProf job is a **neutron** single-crystal refinement (Job = 1,
# λ = 0.8302 Å with neutron scattering lengths).

# %%
import numpy as np

import easydiffraction as ed
from easydiffraction import ExperimentFactory
from easydiffraction import StructureFactory
from easydiffraction.analysis import verification as verify

# %% [markdown]
# ## Load the FullProf reference
#
# `load_fullprof_sc_f2calc` reads the integrated-intensity reflection
# table from `prnio.out` and returns `F2cal` keyed by `(h, k, l)`.
# FullProf reports `F2cal = scale · Corr · |F|²`; the extinction
# correction here is below 0.11 %, so once the absolute scale convention
# is refined out (below) this is effectively a pure `|F|²` comparison.

# %%
reference_dir = verify.bundled_reference_dir() / 'sg-neut-cwl_pr2nio4'
f2calc = verify.load_fullprof_sc_f2calc(str(reference_dir / 'prnio.out'))

# %% [markdown]
# ## Build the project

# %%
project = ed.Project()

# %% [markdown]
# ## Define the structure
#
# Pr₂NiO₄:Sr is a K₂NiF₄-type oxide in space group `F m m m`. Two
# FullProf conventions are converted to the EasyDiffraction (CIF)
# convention as the structure is built:
#
# - **Anisotropic ADPs.** FullProf stores the dimensionless β tensor;
#   EasyDiffraction uses U (Å²). For the orthorhombic cell
#   `U_ij = β_ij · aᵢ · aⱼ / (2π²)`, since `a*ᵢ = 1/aᵢ`.
# - **Occupancies.** FullProf folds the F-centring into its occupancy,
#   so its `Occ` equals the CIF site occupancy times the number of
#   equivalent atoms per primitive cell (the site multiplicity divided
#   by 4). The CIF occupancies below divide that factor back out.

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
# ## Create the experiment
#
# `set_reference_reflections` creates one reflection per `(h, k, l)` in
# the FullProf table, so `cryspy` calculates F² for exactly the same
# set. The Becker–Coppens extinction left at its default is negligible
# here, matching FullProf's sub-percent correction.

# %%
experiment = ExperimentFactory.from_scratch(
    name='pr2nio4',
    sample_form='single crystal',
    beam_mode='constant wavelength',
    radiation_probe='neutron',
    scattering_type='bragg',
)
experiment.linked_crystal.id = 'pr2nio4'
experiment.linked_crystal.scale = 0.06298  # FullProf Scale
experiment.instrument.setup_wavelength = 0.8302  # FullProf Lambda
verify.set_reference_reflections(experiment, f2calc)

project.experiments.add(experiment)

# %% [markdown]
# ## Calculate the structure factors with cryspy

# %%
calc_ed_cryspy = verify.calculate_reflections(project, experiment, 'cryspy')
reference, candidate = verify.align_reflections(f2calc, calc_ed_cryspy)

# %% [markdown]
# ## Compare cryspy against FullProf
#
# Each point is one reflection: FullProf F² on the x-axis, the cryspy F²
# on the y-axis, at their absolute scale. Points fall on the y=x line
# when the two calculations agree, with closeness metrics in the top-left
# corner.

# %%
project.display.reflection_comparison(
    'pr2nio4',
    reference=reference,
    candidate=candidate,
    reference_label='FullProf',
    candidate_label='EasyDiffraction (cryspy)',
)

# %% [markdown]
# ## Agreement check
#
# cryspy reproduces the relative reflection intensities but at a
# different absolute F² scale from FullProf's F2cal (which folds in
# FullProf's refined scale), so the absolute comparison is reported here
# (`raise_on_failure=False`) and the scale convention is investigated
# below.

# %%
verify.assert_patterns_agree(
    [
        ('cryspy vs FullProf', reference, candidate),
    ],
    raise_on_failure=False,
)

# %% [markdown]
# ## Investigate the discrepancy by refinement
#
# Free **only** the scale and refine with cryspy, keeping the structure
# fixed. If a scale-only fit brings the points onto the diagonal, the
# difference is an absolute F²-scale convention, not a per-reflection
# structure-factor disagreement.

# %%
experiment.calculator.type = 'cryspy'
project.analysis.minimizer.type = 'lmfit'

experiment.linked_crystal.scale.free = True

project.analysis.fit()

# %% [markdown]
# ## Goodness of fit and refined parameters

# %%
project.display.fit.results()

# %% [markdown]
# ## Refined cryspy vs FullProf

# %%
calc_ed_cryspy_refined = verify.calculate_reflections(project, experiment, 'cryspy')
reference_after, candidate_after = verify.align_reflections(f2calc, calc_ed_cryspy_refined)

project.display.reflection_comparison(
    'pr2nio4',
    reference=reference_after,
    candidate=candidate_after,
    reference_label='FullProf',
    candidate_label='EasyDiffraction (cryspy, refined)',
)

# %%
verify.report_refinement_closeness(reference, candidate, candidate_after)
