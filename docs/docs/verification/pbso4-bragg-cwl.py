# %% [markdown]
# # PbSO₄ — neutron powder, constant wavelength (Bragg)
#
# This page calculates the **same** PbSO₄ diffraction pattern with each
# EasyDiffraction engine (`cryspy`, `crysfml`) and compares both against a
# **FullProf** reference profile — all on identical input parameters and
# **without any fitting**. It doubles as a regression check run by
# `pixi run script-tests`.
#
# The structure is defined directly in code; the experiment grid and the
# FullProf reference come from the bundled reference profile.

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
reference_dir = verify.bundled_reference_dir()
x, calc_fullprof = verify.load_fullprof_profile(str(reference_dir / 'pbso4_cw.sub'))

# %% [markdown]
# ## Build the project and define the structure in code

# %%
project = ed.Project()

structure = StructureFactory.from_scratch(name='pbso4')
structure.space_group.name_h_m = 'P n m a'
structure.cell.length_a = 8.478440
structure.cell.length_b = 5.396774
structure.cell.length_c = 6.958105
structure.atom_sites.create(
    label='Pb', type_symbol='Pb', fract_x=0.18754, fract_y=0.25, fract_z=0.16707, adp_iso=1.39453
)
structure.atom_sites.create(
    label='S', type_symbol='S', fract_x=0.06539, fract_y=0.25, fract_z=0.68414, adp_iso=0.37766
)
structure.atom_sites.create(
    label='O1', type_symbol='O', fract_x=0.90823, fract_y=0.25, fract_z=0.59539, adp_iso=2.04014
)
structure.atom_sites.create(
    label='O2', type_symbol='O', fract_x=0.19380, fract_y=0.25, fract_z=0.54354, adp_iso=1.51662
)
structure.atom_sites.create(
    label='O3', type_symbol='O', fract_x=0.08116, fract_y=0.02720, fract_z=0.80856, adp_iso=1.35764
)

project.structures.add(structure)

# %% [markdown]
# ## Create the experiment on the reference grid
#
# The experiment is defined in code with the FullProf reference as its
# measured points, so every engine calculates on exactly the same x-grid.

# %%
experiment = ExperimentFactory.from_scratch(
    name='pbso4',
    sample_form='powder',
    beam_mode='constant wavelength',
    radiation_probe='neutron',
    scattering_type='bragg',
)
verify.set_reference_as_measured(experiment, x, calc_fullprof)

experiment.instrument.setup_wavelength = 1.912
experiment.peak.broad_gauss_u = 0.140090
experiment.peak.broad_gauss_v = -0.415422
experiment.peak.broad_gauss_w = 0.390087
experiment.peak.broad_lorentz_x = 0.0
experiment.peak.broad_lorentz_y = 0.084535
experiment.linked_phases.create(id='pbso4', scale=1.0)

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

# %%
