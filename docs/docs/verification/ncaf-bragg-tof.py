# %% [markdown]
# # NaCaAlF — neutron powder, time-of-flight (Bragg)
#
# Cross-engine and external-reference verification for NaCaAlF
# (Na₂Ca₃Al₂F₁₄) in time-of-flight geometry: the **same** pattern is
# calculated with each EasyDiffraction engine (`cryspy`, `crysfml`) and
# compared against a **FullProf** reference, on identical input
# parameters and **without any fitting**. It also runs as a regression
# check under `pixi run script-tests`.
#
# This Jorgensen–Von Dreele profile has no Lorentzian (`gamma`) term, so
# both engines agree closely with FullProf.

# %%
import easydiffraction as ed
from easydiffraction import ExperimentFactory
from easydiffraction import StructureFactory
from easydiffraction.analysis import verification as verify

# %% [markdown]
# ## Load the FullProf reference
#
# This reference is a two-column ``x y`` profile.

# %%
reference_dir = verify.bundled_reference_dir()
x, calc_fullprof = verify.load_columned_profile(
    str(reference_dir / 'ncaf_tof.sub'),
    skip_rows=1,
    columns=(0, 1),
)

# %% [markdown]
# ## Build the project and define the structure in code

# %%
project = ed.Project()

structure = StructureFactory.from_scratch(name='ncaf')
structure.space_group.name_h_m = 'I 21 3'
structure.cell.length_a = 10.250256
structure.cell.length_b = 10.250256
structure.cell.length_c = 10.250256
structure.atom_sites.create(
    label='Ca', type_symbol='Ca', fract_x=0.46610, fract_y=0.0, fract_z=0.25, adp_iso=0.88770
)
structure.atom_sites.create(
    label='Al',
    type_symbol='Al',
    fract_x=0.25163,
    fract_y=0.25163,
    fract_z=0.25163,
    adp_iso=0.65283,
)
structure.atom_sites.create(
    label='Na',
    type_symbol='Na',
    fract_x=0.08472,
    fract_y=0.08472,
    fract_z=0.08472,
    adp_iso=1.89281,
)
structure.atom_sites.create(
    label='F1', type_symbol='F', fract_x=0.13748, fract_y=0.30533, fract_z=0.11947, adp_iso=0.89562
)
structure.atom_sites.create(
    label='F2', type_symbol='F', fract_x=0.36263, fract_y=0.36333, fract_z=0.18669, adp_iso=1.27227
)
structure.atom_sites.create(
    label='F3', type_symbol='F', fract_x=0.46120, fract_y=0.46120, fract_z=0.46120, adp_iso=0.78071
)

project.structures.add(structure)

# %% [markdown]
# ## Create the experiment on the reference grid

# %%
experiment = ExperimentFactory.from_scratch(
    name='ncaf',
    sample_form='powder',
    beam_mode='time-of-flight',
    radiation_probe='neutron',
    scattering_type='bragg',
)
verify.set_reference_as_measured(experiment, x, calc_fullprof)

experiment.instrument.setup_twotheta_bank = 152.827
experiment.instrument.calib_d_to_tof_linear = 20773.12305
experiment.instrument.calib_d_to_tof_quad = -1.08308
experiment.instrument.calib_d_to_tof_offset = 0.0

experiment.peak.type = 'jorgensen-von-dreele'
experiment.peak.broad_gauss_sigma_0 = 0.0
experiment.peak.broad_gauss_sigma_1 = 0.0
experiment.peak.broad_gauss_sigma_2 = 15.6960
experiment.peak.exp_rise_alpha_0 = -0.009276
experiment.peak.exp_rise_alpha_1 = 0.109623
experiment.peak.exp_decay_beta_0 = 0.006705
experiment.peak.exp_decay_beta_1 = 0.009708

experiment.linked_phases.create(id='ncaf', scale=1.0)

project.experiments.add(experiment)

# %% [markdown]
# ## Calculate the pattern with each engine

# %%
calc_ed_cryspy = verify.calculate_pattern(project, experiment, 'cryspy')
calc_ed_crysfml = verify.calculate_pattern(project, experiment, 'crysfml')

# %% [markdown]
# ## Compare each engine against FullProf

# %%
project.display.pattern_comparison(
    'ncaf',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy,
    reference_label='FullProf',
    candidate_label='EasyDiffraction (cryspy)',
)

# %%
project.display.pattern_comparison(
    'ncaf',
    reference=calc_fullprof,
    candidate=calc_ed_crysfml,
    reference_label='FullProf',
    candidate_label='EasyDiffraction (crysfml)',
)

# %% [markdown]
# ## Compare the two engines with each other

# %%
project.display.pattern_comparison(
    'ncaf',
    reference=calc_ed_crysfml,
    candidate=calc_ed_cryspy,
    reference_label='EasyDiffraction (crysfml)',
    candidate_label='EasyDiffraction (cryspy)',
)

# %% [markdown]
# ## Agreement check

# %%
verify.assert_patterns_agree([
    ('cryspy vs FullProf', calc_fullprof, calc_ed_cryspy),
    ('crysfml vs FullProf', calc_fullprof, calc_ed_crysfml),
    ('cryspy vs crysfml', calc_ed_cryspy, calc_ed_crysfml),
])

# %%
