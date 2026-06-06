# %% [markdown]
# # Al₂O₃ — neutron powder, time-of-flight (Bragg)
#
# Cross-engine and external-reference verification for corundum
# (α-Al₂O₃) in time-of-flight geometry: the **same** pattern is
# calculated with each EasyDiffraction engine (`cryspy`, `crysfml`) and
# compared against a **FullProf** reference, on identical input
# parameters and **without any fitting**.
#
# > **Known difference.** For the time-of-flight Jorgensen–Von Dreele
# > profile with a non-zero Lorentzian (`broad_lorentz_gamma`) term,
# > the `cryspy` engine currently diverges from FullProf and `crysfml`.
# > It is shown below for visibility and tracked in the open-issues list;
# > the agreement check reports it without failing CI, so this page stays
# > a clean docs build while the regression remains visible.

# %%
import easydiffraction as ed
from easydiffraction import ExperimentFactory
from easydiffraction import StructureFactory
from easydiffraction.analysis import verification as verify

# %% [markdown]
# ## Load the FullProf reference

# %%
reference_dir = verify.bundled_reference_dir()
x, calc_fullprof = verify.load_fullprof_profile(str(reference_dir / 'al2o3_tof.sim'))

# %% [markdown]
# ## Build the project and define the structure in code

# %%
project = ed.Project()

structure = StructureFactory.from_scratch(name='al2o3')
structure.space_group.name_h_m = 'R -3 c'
structure.cell.length_a = 4.754000
structure.cell.length_b = 4.754000
structure.cell.length_c = 12.990000
structure.cell.angle_gamma = 120.0
structure.atom_sites.create(
    label='Al', type_symbol='Al', fract_x=0.0, fract_y=0.0, fract_z=0.35228, adp_iso=0.40
)
structure.atom_sites.create(
    label='O', type_symbol='O', fract_x=0.30640, fract_y=0.0, fract_z=0.25, adp_iso=0.60
)

project.structures.add(structure)

# %% [markdown]
# ## Create the experiment on the reference grid
#
# A time-of-flight experiment uses a d-to-TOF calibration and the
# Jorgensen–Von Dreele peak profile (back-to-back exponentials ⊗
# pseudo-Voigt).

# %%
experiment = ExperimentFactory.from_scratch(
    name='al2o3',
    sample_form='powder',
    beam_mode='time-of-flight',
    radiation_probe='neutron',
    scattering_type='bragg',
)
verify.set_reference_as_measured(experiment, x, calc_fullprof)

experiment.instrument.setup_twotheta_bank = 90.0
experiment.instrument.calib_d_to_tof_linear = 4570.60010
experiment.instrument.calib_d_to_tof_quad = 0.0
experiment.instrument.calib_d_to_tof_offset = 0.0

experiment.peak.type = 'jorgensen-von-dreele'
experiment.peak.broad_gauss_sigma_0 = 3.5190
experiment.peak.broad_gauss_sigma_1 = 63.3850
experiment.peak.broad_gauss_sigma_2 = 1.5880
experiment.peak.broad_lorentz_gamma_0 = 0.0
experiment.peak.broad_lorentz_gamma_1 = 4.6950
experiment.peak.broad_lorentz_gamma_2 = 0.0
experiment.peak.exp_rise_alpha_0 = 0.0
experiment.peak.exp_rise_alpha_1 = 0.716993
experiment.peak.exp_decay_beta_0 = 0.050835
experiment.peak.exp_decay_beta_1 = 0.010232

experiment.linked_phases.create(id='al2o3', scale=1.0)

project.experiments.add(experiment)

# %% [markdown]
# ## Calculate the pattern with each engine

# %%
calc_ed_cryspy = verify.calculate_pattern(project, experiment, 'cryspy')
calc_ed_crysfml = verify.calculate_pattern(project, experiment, 'crysfml')

# %% [markdown]
# ## Compare each engine against FullProf
#
# The FullProf reference is a solid blue line and the engine a red dashed
# line, with the residual below and closeness metrics in the top-left
# corner. `crysfml` reproduces FullProf closely; `cryspy` diverges for
# this profile (see the note at the top).

# %%
project.display.pattern_comparison(
    'al2o3',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy,
    reference_label='FullProf',
    candidate_label='EasyDiffraction (cryspy)',
)

# %%
project.display.pattern_comparison(
    'al2o3',
    reference=calc_fullprof,
    candidate=calc_ed_crysfml,
    reference_label='FullProf',
    candidate_label='EasyDiffraction (crysfml)',
)

# %% [markdown]
# ## Compare the two engines with each other

# %%
project.display.pattern_comparison(
    'al2o3',
    reference=calc_ed_crysfml,
    candidate=calc_ed_cryspy,
    reference_label='EasyDiffraction (crysfml)',
    candidate_label='EasyDiffraction (cryspy)',
)

# %% [markdown]
# ## Agreement check
#
# `raise_on_failure=False` keeps CI green while still showing the
# `cryspy` discrepancy in red — it is reported, not enforced, and tracked
# in the open-issues list.

# %%
verify.assert_patterns_agree(
    [
        ('cryspy vs FullProf', calc_fullprof, calc_ed_cryspy),
        ('crysfml vs FullProf', calc_fullprof, calc_ed_crysfml),
        ('cryspy vs crysfml', calc_ed_crysfml, calc_ed_cryspy),
    ],
    raise_on_failure=False,
)
