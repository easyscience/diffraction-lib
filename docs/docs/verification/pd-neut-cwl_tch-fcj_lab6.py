# %% [markdown]
# # LaB₆ — neutron powder, constant wavelength, Thompson–Cox–Hastings
#
# This page calculates the **same** LaB₆ diffraction pattern with each
# EasyDiffraction engine (`cryspy`, `crysfml`) and compares both against a
# **FullProf** reference profile on identical input parameters, then
# investigates the discrepancy by refinement. It uses the real LaB₆
# dataset from
# [cryspy issue #38](https://github.com/ikibalin/cryspy/issues/38).
#
# The page targets the FullProf `SyCos`/`SySin` systematic peak-position
# corrections (sample displacement and transparency), which map to
# `calib_sample_displacement` and `calib_sample_transparency` on the CWL
# powder instrument. Only the `cryspy` engine applies them, and only with
# the functionality added in
# [cryspy PR #46](https://github.com/ikibalin/cryspy/pull/46); the
# `crysfml` engine has no equivalent. Because FullProf and cryspy use
# different coefficient conventions for these corrections (and a
# different absolute-intensity scale), the FullProf values are used as
# starting points and the discrepancy is investigated by refining
# `scale`, `calib_sample_displacement` and `calib_sample_transparency`
# with `cryspy`. The page stays listed in `ci_skip.txt` until a released
# cryspy ships the PR #46 corrections.

# %%
import easydiffraction as ed
from easydiffraction import ExperimentFactory
from easydiffraction import StructureFactory
from easydiffraction.analysis import verification as verify

# %% [markdown]
# ## Load the FullProf reference
#
# The FullProf **calculated** profile is exported as a two-column
# (2θ, intensity) `.sub` holding the Bragg contribution only (no
# background), so the engines are compared against FullProf's own
# calculation, consistent with the other Verification pages.

# %%
reference_dir = verify.bundled_reference_dir() / 'pd-neut-cwl_tch-fcj_lab6'
x, calc_fullprof = verify.load_columned_profile(
    str(reference_dir / 'ECH0030684_LaB6_1p622A1.sub'),
    skip_rows=1,
    columns=(0, 1),
)

# %% [markdown]
# ## Build the project

# %%
project = ed.Project()

# %% [markdown]
# ## Define the structure
#
# Boron is the ¹¹B isotope (FullProf `B11`). The `cryspy` engine resolves
# the isotope directly; the `crysfml` engine resolves scattering by
# element and silently drops the isotope number (`11B` → `B`).

# %%
structure = StructureFactory.from_scratch(name='lab6')
structure.space_group.name_h_m = 'P m -3 m'  # FullProf Space group symbol
structure.cell.length_a = 4.156885  # FullProf a
structure.atom_sites.create(
    label='La',  # FullProf Atom
    type_symbol='La',  # FullProf Typ
    fract_x=0.0,  # FullProf X
    fract_y=0.0,  # FullProf Y
    fract_z=0.0,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=0.53399,  # FullProf Biso
)
structure.atom_sites.create(
    label='B',  # FullProf Atom
    type_symbol='11B',  # FullProf "B11     0.66500    0.00000   0"
    fract_x=0.19972,  # FullProf X
    fract_y=0.5,  # FullProf Y
    fract_z=0.5,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=0.39406,  # FullProf Biso
)

project.structures.add(structure)

# %% [markdown]
# ## Create the experiment
#
# Starting values are taken from `ECH0030684_LaB6_1p622A.pcr`.

# %%
experiment = ExperimentFactory.from_scratch(
    name='lab6',
    sample_form='powder',
    beam_mode='constant wavelength',
    radiation_probe='neutron',
    scattering_type='bragg',
)
verify.set_reference_as_measured(experiment, x, calc_fullprof)

experiment.linked_phases.create(id='lab6', scale=136.0507)  # FullProf Scale

experiment.instrument.setup_wavelength = 1.623891  # FullProf Lambda
experiment.instrument.calib_sample_displacement = 0.01052  # FullProf SyCos
experiment.instrument.calib_sample_transparency = 0.24192  # FullProf SySin

experiment.peak.broad_gauss_u = 0.143363  # FullProf U
experiment.peak.broad_gauss_v = -0.522167  # FullProf V
experiment.peak.broad_gauss_w = 0.590411  # FullProf W
experiment.peak.broad_lorentz_x = 0.0  # FullProf X
experiment.peak.broad_lorentz_y = 0.054276  # FullProf Y

project.experiments.add(experiment)

# %% [markdown]
# ## Calculate the pattern with each engine

# %%
calc_ed_cryspy = verify.calculate_pattern(project, experiment, 'cryspy')
calc_ed_crysfml = verify.calculate_pattern(project, experiment, 'crysfml')

# %% [markdown]
# ## Compare each engine against FullProf
#
# At the FullProf input values the engines differ from the FullProf
# reference: the absolute-intensity scale and the `SyCos`/`SySin`
# coefficient conventions are not shared between codes, and `crysfml`
# cannot apply the corrections at all.

# %%
project.display.pattern_comparison(
    'lab6',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy,
    reference_label='FullProf',
    candidate_label='EasyDiffraction (cryspy)',
)

# %%
project.display.pattern_comparison(
    'lab6',
    reference=calc_fullprof,
    candidate=calc_ed_crysfml,
    reference_label='FullProf',
    candidate_label='EasyDiffraction (crysfml)',
)

# %% [markdown]
# ## Compare the two engines with each other

# %%
project.display.pattern_comparison(
    'lab6',
    reference=calc_ed_crysfml,
    candidate=calc_ed_cryspy,
    reference_label='EasyDiffraction (crysfml)',
    candidate_label='EasyDiffraction (cryspy)',
)

# %% [markdown]
# ## Agreement check
#
# Reported without failing CI (`raise_on_failure=False`); the page is also
# skipped via `ci_skip.txt` while the corrections require an unreleased
# cryspy.

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
# Because the FullProf profile is already loaded as the measured data, we
# can test directly whether `cryspy` can reproduce it: refine the
# absolute `scale` together with `calib_sample_displacement` and
# `calib_sample_transparency`, keeping the structure and every other
# parameter fixed, and check how far the corrections have to move to
# match FullProf. `crysfml` is not refined — it has no `SyCos`/`SySin`
# equivalent.

# %%
experiment.calculator.type = 'cryspy'
project.analysis.minimizer.type = 'lmfit'

# Free only the absolute scale and the two peak-position corrections; the
# structure stays fixed, so a good fit confirms the difference is a
# scale/correction-convention difference, not a structural disagreement.
experiment.linked_phases['lab6'].scale.free = True
experiment.instrument.calib_sample_displacement.free = True
experiment.instrument.calib_sample_transparency.free = True

# %%
project.analysis.fit()

# %% [markdown]
# ## Goodness of fit and refined parameters
#
# The reference is a calculation-only profile with unit uncertainties, so
# the absolute reduced χ² and R-factors are not normalised goodness-of-fit
# values; the **scale-independent before/after closeness table** below is
# the meaningful measure of the improvement.

# %%
project.display.fit.results()

# %% [markdown]
# ## Refined cryspy vs FullProf
#
# The refined `cryspy` pattern overlaid on the FullProf reference, then a
# before/after table of the closeness metrics. A residual profile-shape
# difference remains, which is why the page is not yet a passing
# regression check.

# %%
calc_ed_cryspy_refined = verify.calculate_pattern(project, experiment, 'cryspy')

project.display.pattern_comparison(
    'lab6',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy_refined,
    reference_label='FullProf',
    candidate_label='EasyDiffraction (cryspy, refined)',
)

# %%
verify.report_refinement_closeness(calc_fullprof, calc_ed_cryspy, calc_ed_cryspy_refined)
