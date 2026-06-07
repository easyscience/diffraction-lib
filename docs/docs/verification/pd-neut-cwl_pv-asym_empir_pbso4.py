# %% [markdown]
# # PbSO₄ — neutron powder, constant wavelength, pseudo-Voigt with empirical asymmetry
#
# This page calculates the **same** PbSO₄ diffraction pattern with each
# EasyDiffraction engine (`cryspy`, `crysfml`) and compares both against a
# **FullProf** reference profile — all on identical input parameters and
# **without any fitting**. It doubles as a regression check run by
# `pixi run script-tests`.
#
# The peak shape here is a **pseudo-Voigt with empirical (FullProf-style)
# axial-divergence asymmetry**; a companion page repeats the comparison
# with a plain pseudo-Voigt. The structure is defined directly in code,
# and the experiment grid and FullProf reference come from the project's
# reference profile.

# %%
import easydiffraction as ed
from easydiffraction import ExperimentFactory
from easydiffraction import StructureFactory
from easydiffraction.analysis import verification as verify

# %% [markdown]
# ## Load the FullProf reference
#
# The reference profile provides both the x-grid the engines calculate on
# and the reference curve `calc_fullprof`.

# %%
reference_dir = verify.bundled_reference_dir() / 'pd-neut-cwl_pv-asym_empir_pbso4'
x, calc_fullprof = verify.load_fullprof_profile(str(reference_dir / 'pbso41.sub'))

# %% [markdown]
# ## Build the project

# %%
project = ed.Project()

# %% [markdown]
# ## Define the structure

# %%
structure = StructureFactory.from_scratch(name='pbso4')

structure.space_group.name_h_m = 'P n m a'

structure.cell.length_a = 8.479502
structure.cell.length_b = 5.397251
structure.cell.length_c = 6.958967

structure.atom_sites.create(
    label='Pb', type_symbol='Pb', fract_x=0.18752, fract_y=0.25, fract_z=0.16705, adp_iso=1.39083
)
structure.atom_sites.create(
    label='S', type_symbol='S', fract_x=0.06549, fract_y=0.25, fract_z=0.68374, adp_iso=0.39372
)
structure.atom_sites.create(
    label='O1', type_symbol='O', fract_x=0.90816, fract_y=0.25, fract_z=0.59544, adp_iso=1.99362
)
structure.atom_sites.create(
    label='O2', type_symbol='O', fract_x=0.19355, fract_y=0.25, fract_z=0.54330, adp_iso=1.47816
)
structure.atom_sites.create(
    label='O3', type_symbol='O', fract_x=0.08109, fract_y=0.02727, fract_z=0.80869, adp_iso=1.30171
)

project.structures.add(structure)

# %% [markdown]
# ## Create the experiment

# %%
experiment = ExperimentFactory.from_scratch(
    name='pbso4',
    sample_form='powder',
    beam_mode='constant wavelength',
    radiation_probe='neutron',
    scattering_type='bragg',
)
verify.set_reference_as_measured(experiment, x, calc_fullprof)

experiment.linked_phases.create(id='pbso4', scale=1.0)

experiment.instrument.setup_wavelength = 1.912

experiment.peak.type = 'pseudo-voigt + empirical asymmetry'
experiment.peak.broad_gauss_u = 0.153464
experiment.peak.broad_gauss_v = -0.453189
experiment.peak.broad_gauss_w = 0.419443
experiment.peak.broad_lorentz_x = 0.0
experiment.peak.broad_lorentz_y = 0.086819
experiment.peak.asym_empir_1 = 0.29460
experiment.peak.asym_empir_2 = 0.02255
experiment.peak.asym_empir_3 = -0.10957
experiment.peak.asym_empir_4 = 0.04956

project.experiments.add(experiment)

# %% [markdown]
# ## Calculate the pattern with each engine

# %%
calc_ed_cryspy = verify.calculate_pattern(project, experiment, 'cryspy')
calc_ed_crysfml = verify.calculate_pattern(project, experiment, 'crysfml')

# %% [markdown]
# ## Compare each engine against FullProf
#
# The FullProf reference is drawn as a solid blue line and the engine as
# a red dashed line, with the residual below and closeness metrics in the
# top-left corner.

# %%
project.display.pattern_comparison(
    'pbso4',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy,
    reference_label='FullProf',
    candidate_label='EasyDiffraction (cryspy)',
)

# %%
project.display.pattern_comparison(
    'pbso4',
    reference=calc_fullprof,
    candidate=calc_ed_crysfml,
    reference_label='FullProf',
    candidate_label='EasyDiffraction (crysfml)',
)

# %% [markdown]
# ## Compare the two engines with each other

# %%
project.display.pattern_comparison(
    'pbso4',
    reference=calc_ed_crysfml,
    candidate=calc_ed_cryspy,
    reference_label='EasyDiffraction (crysfml)',
    candidate_label='EasyDiffraction (cryspy)',
)

# %% [markdown]
# ## Agreement check
#
# A single table scores every pair against documented tolerances, with a
# check/cross per metric; an out-of-tolerance value is shown in red and
# raises, so the page fails as a regression check.

# %%
verify.assert_patterns_agree([
    ('cryspy vs FullProf', calc_fullprof, calc_ed_cryspy),
    ('crysfml vs FullProf', calc_fullprof, calc_ed_crysfml),
    ('cryspy vs crysfml', calc_ed_cryspy, calc_ed_crysfml),
])
