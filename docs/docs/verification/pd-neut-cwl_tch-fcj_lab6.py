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
# ## Build the project and define the structure in code

# %%
project = ed.Project()

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
    adp_iso=0.59716,  # FullProf Biso
)
structure.atom_sites.create(
    label='B',  # FullProf Atom
    type_symbol='B',  # FullProf Typ
    fract_x=0.5,  # FullProf X
    fract_y=0.5,  # FullProf Y
    fract_z=0.19978,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=0.44250,  # FullProf Biso
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

experiment.instrument.setup_wavelength = 1.623891  # FullProf Lambda
experiment.instrument.calib_twotheta_offset = -0.45495  # FullProf Zero
experiment.peak.broad_gauss_u = 0.143360  # FullProf U
experiment.peak.broad_gauss_v = -0.522136  # FullProf V
experiment.peak.broad_gauss_w = 0.590412  # FullProf W
experiment.peak.broad_lorentz_x = 0.0  # FullProf X
experiment.peak.broad_lorentz_y = 0.054265  # FullProf Y
experiment.linked_phases.create(id='lab6', scale=136.0485)  # FullProf Scale

project.experiments.add(experiment)

# %% [markdown]
# ## SyCos / SySin (pending EasyDiffraction support)
#
# FullProf applies sample-displacement (`SyCos`) and transparency
# (`SySin`) peak-position shifts on top of `Zero` (see issue #117). The
# CWL instrument category does not expose them yet, so the two lines
# below are kept commented out with the FullProf `.pcr` values —
# uncomment them once the parameters land to finish this page. As with
# `Zero` (`calib_twotheta_offset` above), the cross-code convention may
# differ, so the values may need the same adjustment when wired in.

# %%
# experiment.instrument.calib_sycos = 0.05395  # FullProf SyCos
# experiment.instrument.calib_sysin = 0.09127  # FullProf SySin

# %% [markdown]
# ## Calculate the pattern with each engine

# %%
calc_ed_cryspy = verify.calculate_pattern(project, experiment, 'cryspy')
calc_ed_crysfml = verify.calculate_pattern(project, experiment, 'crysfml')

# %% [markdown]
# ## Compare each engine against the reference
#
# Until the corrections above are supported the engines will show
# systematic peak-position offsets against the FullProf calculated
# profile, which is the discrepancy this page is being prepared to
# verify.

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
