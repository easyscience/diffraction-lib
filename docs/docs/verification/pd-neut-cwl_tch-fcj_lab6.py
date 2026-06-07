# %% [markdown]
# # LaB₆ — neutron powder, constant wavelength, Thompson–Cox–Hastings
#
# A **prepared** verification for the FullProf `SyCos`/`SySin` systematic
# peak-position corrections (sample displacement and transparency), using
# the real LaB6 dataset from
# [cryspy issue #38](https://github.com/ikibalin/cryspy/issues/38). The
# FullProf model applies `Zero = -0.21356`, `SyCos = 0.05395`, and
# `SySin = 0.09127`, a Thompson–Cox–Hastings profile with Finger–Cox–
# Jephcoat axial-divergence asymmetry, a polynomial background, and a
# custom ¹¹B scattering length.
#
# > **Pending — this page is skipped in CI.** EasyDiffraction does not
# > yet expose `SyCos`/`SySin`, the ¹¹B scattering length, the
# > Thompson–Cox–Hastings profile, or the FullProf polynomial background.
# > Until those land, the engines cannot reproduce this model, so the
# > page is listed in `ci_skip.txt` and is committed only as a
# > ready-to-finish skeleton. The cryspy side of `SyCos`/`SySin` is added
# > in [cryspy PR #46](https://github.com/ikibalin/cryspy/pull/46).

# %%
import easydiffraction as ed
from easydiffraction import ExperimentFactory
from easydiffraction import StructureFactory
from easydiffraction.analysis import verification as verify

# %% [markdown]
# ## Load the FullProf reference
#
# The issue #38 project ships the measured data and the `.pcr` model but
# no pre-calculated profile, so the measured pattern is used as the
# reference for now.

# %%
reference_dir = verify.bundled_reference_dir() / 'pd-neut-cwl_tch-fcj_lab6'
x, calc_fullprof = verify.load_columned_profile(
    str(reference_dir / 'ECH0030684_LaB6_1p622A.dat'),
    skip_rows=0,
    columns=(0, 1),
)

# %% [markdown]
# ## Build the project and define the structure in code

# %%
project = ed.Project()

structure = StructureFactory.from_scratch(name='lab6')
structure.space_group.name_h_m = 'P m -3 m'
structure.cell.length_a = 4.156885
structure.cell.length_b = 4.156885
structure.cell.length_c = 4.156885
structure.atom_sites.create(
    label='La', type_symbol='La', fract_x=0.0, fract_y=0.0, fract_z=0.0, adp_iso=0.59716
)
structure.atom_sites.create(
    label='B', type_symbol='B', fract_x=0.5, fract_y=0.5, fract_z=0.19978, adp_iso=0.44250
)

project.structures.add(structure)

# %% [markdown]
# ## Create the experiment on the reference grid

# %%
experiment = ExperimentFactory.from_scratch(
    name='lab6',
    sample_form='powder',
    beam_mode='constant wavelength',
    radiation_probe='neutron',
    scattering_type='bragg',
)
verify.set_reference_as_measured(experiment, x, calc_fullprof)

experiment.instrument.setup_wavelength = 1.622536
experiment.instrument.calib_twotheta_offset = -0.21356  # FullProf Zero
experiment.peak.broad_gauss_u = 0.089876
experiment.peak.broad_gauss_v = -0.377516
experiment.peak.broad_gauss_w = 0.476188
experiment.peak.broad_lorentz_x = 0.0
experiment.peak.broad_lorentz_y = 0.052654
experiment.linked_phases.create(id='lab6', scale=1.0)

project.experiments.add(experiment)

# %% [markdown]
# ## SyCos / SySin (pending EasyDiffraction support)
#
# The systematic peak-position corrections cannot be set yet; once a
# category exists they would be applied here, e.g.:
#
# ```python
# experiment.instrument.calib_sycos = 0.05395
# experiment.instrument.calib_sysin = 0.09127
# ```

# %% [markdown]
# ## Calculate the pattern with each engine

# %%
calc_ed_cryspy = verify.calculate_pattern(project, experiment, 'cryspy')
calc_ed_crysfml = verify.calculate_pattern(project, experiment, 'crysfml')

# %% [markdown]
# ## Compare each engine against the reference
#
# Until the corrections above are supported the engines will show
# systematic peak-position offsets against the measured data, which is
# the discrepancy this page is being prepared to verify.

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
# Reported without failing CI (`raise_on_failure=False`) while the
# corrections are unsupported; the page is also skipped via `ci_skip.txt`.

# %%
verify.assert_patterns_agree(
    [
        ('cryspy vs FullProf', calc_fullprof, calc_ed_cryspy),
        ('crysfml vs FullProf', calc_fullprof, calc_ed_crysfml),
        ('cryspy vs crysfml', calc_ed_cryspy, calc_ed_crysfml),
    ],
    raise_on_failure=False,
)
