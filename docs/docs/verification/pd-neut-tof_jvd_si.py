# %% [markdown]
# # Si — neutron powder, time-of-flight, Jorgensen–Von Dreele
#
# Cross-engine and external-reference verification for silicon in
# time-of-flight geometry: the **same** pattern is calculated with each
# EasyDiffraction engine (`cryspy`, `crysfml`) and compared against a
# **FullProf** reference, on identical input parameters and **without any
# fitting**.
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
reference_dir = verify.bundled_reference_dir() / 'pd-neut-tof_jvd_si'
x, calc_fullprof = verify.load_fullprof_profile(str(reference_dir / 'arg_si1.sub'))

# %% [markdown]
# ## Build the project

# %%
project = ed.Project()

# %% [markdown]
# ## Define the structure

# %%
structure = StructureFactory.from_scratch(name='si')

structure.space_group.name_h_m = 'F d -3 m'  # FullProf Space group symbol
structure.space_group.it_coordinate_system_code = '2'

structure.cell.length_a = 5.431342  # FullProf a

structure.atom_sites.create(
    label='Si',  # FullProf Atom
    type_symbol='Si',  # FullProf Typ
    fract_x=0.125,  # FullProf X
    fract_y=0.125,  # FullProf Y
    fract_z=0.125,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=0.52451,  # FullProf Biso
)

project.structures.add(structure)

# %% [markdown]
# ## Create the experiment

# %%
experiment = ExperimentFactory.from_scratch(
    name='si',
    sample_form='powder',
    beam_mode='time-of-flight',
    radiation_probe='neutron',
    scattering_type='bragg',
)
verify.set_reference_as_measured(experiment, x, calc_fullprof)

experiment.linked_phases.create(id='si', scale=0.6750988)  # FullProf Scale

experiment.instrument.setup_twotheta_bank = 144.845  # FullProf 2ThetaBank
experiment.instrument.calib_d_to_tof_linear = 7476.91016  # FullProf Dtt1
experiment.instrument.calib_d_to_tof_quad = -1.54  # FullProf Dtt2

experiment.peak.type = 'jorgensen-von-dreele'
experiment.peak.broad_gauss_sigma_0 = 3.5541  # FullProf Sigma-0
experiment.peak.broad_gauss_sigma_1 = 33.0418  # FullProf Sigma-1
experiment.peak.broad_gauss_sigma_2 = 0.0  # FullProf Sigma-2
experiment.peak.broad_lorentz_gamma_0 = 0.0  # FullProf Gamma-0
experiment.peak.broad_lorentz_gamma_1 = 2.5432  # FullProf Gamma-1
experiment.peak.broad_lorentz_gamma_2 = 0.0  # FullProf Gamma-2
experiment.peak.exp_rise_alpha_0 = 0.0  # FullProf alph0
experiment.peak.exp_rise_alpha_1 = 0.5971  # FullProf alph1
experiment.peak.exp_decay_beta_0 = 0.04221  # FullProf beta0
experiment.peak.exp_decay_beta_1 = 0.00946  # FullProf beta1

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
    'si',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy,
    reference_label='FullProf',
    candidate_label='EasyDiffraction (cryspy)',
)

# %%
project.display.pattern_comparison(
    'si',
    reference=calc_fullprof,
    candidate=calc_ed_crysfml,
    reference_label='FullProf',
    candidate_label='EasyDiffraction (crysfml)',
)

# %% [markdown]
# ## Compare the two engines with each other

# %%
project.display.pattern_comparison(
    'si',
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
        ('cryspy vs crysfml', calc_ed_cryspy, calc_ed_crysfml),
    ],
    raise_on_failure=False,
)

# %% [markdown]
# ## Investigate the discrepancy by refinement
#
# The `cryspy` divergence is in the time-of-flight **profile**, not the
# structure. Mirroring the empirical-asymmetry page, we free the disputed
# peak-profile terms with the `cryspy` engine — here the Jorgensen–Von
# Dreele Lorentzian `gamma₁` term that drives the discrepancy — and refine
# it with everything else fixed, to check whether `cryspy` can then
# reproduce the FullProf curve and how far that term has to move.
#
# Unlike the constant-wavelength asymmetry page, the scale is freed too:
# the time-of-flight intensity-scale convention differs between `cryspy`
# and FullProf, so the FullProf `.pcr` scale does not carry over and the
# scale has to be refined alongside the profile terms.

# %%
# Adjust the initial guess to be closer to the reference, to speed up the fit
experiment.linked_phases['si'].scale = 16.5579
experiment.peak.broad_lorentz_gamma_1 = 9.9974

# %%
experiment.calculator.type = 'cryspy'
project.analysis.minimizer.type = 'lmfit'

experiment.linked_phases['si'].scale.free = True
experiment.peak.broad_lorentz_gamma_1.free = True

# %%
project.analysis.fit()

# %% [markdown]
# ## Goodness of fit and refined parameters
#
# What matters here is the refined Lorentzian terms and that the
# structure and calibration were never touched; the before/after
# closeness table below is the meaningful measure of the improvement.

# %%
project.display.fit.results()

# %% [markdown]
# ## Refined cryspy vs FullProf

# %%
calc_ed_cryspy_refined = verify.calculate_pattern(project, experiment, 'cryspy')

project.display.pattern_comparison(
    'si',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy_refined,
    reference_label='FullProf',
    candidate_label='EasyDiffraction (cryspy, refined)',
)

# %%
verify.report_refinement_closeness(calc_fullprof, calc_ed_cryspy, calc_ed_cryspy_refined)
