# %% [markdown]
# # LBCO — preferred orientation (March–Dollase): ed-cryspy VS FullProf
#
# This page documents a **known divergence**, not an agreement. FullProf
# applies the *standard* March–Dollase preferred-orientation correction
# (its `.out` reports "March-Dollase model for preferred orientation").
# CrysPy 0.11.0 applies a *different*, non-intensity-conserving "Modified
# March" function. Feeding the **same** nominal March coefficient `r` to
# both therefore produces visibly different patterns, and no single `r`
# reconciles them. See the upstream report prepared in
# `tmp/cryspy/preferred-orientation/` and ADR
# `preferred-orientation-category` (Decision 6).

# %%
import easydiffraction as ed
from easydiffraction import ExperimentFactory
from easydiffraction import StructureFactory
from easydiffraction.analysis import verification as verify

# %% [markdown]
# ## Build the project

# %%
project = ed.Project()

# %% [markdown]
# ## Define the structure (same La0.5Ba0.5CoO3 as `pd-neut-cwl_pv_lbco`)

# %%
structure = StructureFactory.from_scratch(name='lbco')

structure.space_group.name_h_m = 'P m -3 m'  # FullProf Space group symbol

structure.cell.length_a = 3.890790  # FullProf a

structure.atom_sites.create(
    label='La',
    type_symbol='La',
    fract_x=0.0,
    fract_y=0.0,
    fract_z=0.0,
    occupancy=0.5,
    adp_type='Biso',
    adp_iso=0.57511,
)
structure.atom_sites.create(
    label='Ba',
    type_symbol='Ba',
    fract_x=0.0,
    fract_y=0.0,
    fract_z=0.0,
    occupancy=0.5,
    adp_type='Biso',
    adp_iso=0.57511,
)
structure.atom_sites.create(
    label='Co',
    type_symbol='Co',
    fract_x=0.5,
    fract_y=0.5,
    fract_z=0.5,
    occupancy=1.0,
    adp_type='Biso',
    adp_iso=0.26023,
)
structure.atom_sites.create(
    label='O',
    type_symbol='O',
    fract_x=0.0,
    fract_y=0.5,
    fract_z=0.5,
    occupancy=0.97856,
    adp_type='Biso',
    adp_iso=1.36662,
)

project.structures.add(structure)

# %% [markdown]
# ## Load the FullProf reference (March–Dollase, `Pref1 = 1.2`, axis `[0 0 1]`)

# %%
FULLPROF_PROJECT_DIR = 'pd-neut-cwl_pv-march_lbco'
FULLPROF_PRF_FILE = 'lbco.prf'
FULLPROF_BAC_FILE = 'lbco.bac'
FULLPROF_ZERO = 0.62040  # FullProf Zero
FULLPROF_SCALE = 9.405870  # FullProf Scale
FULLPROF_WAVELENGTH = 1.494000  # FullProf Lambda
FULLPROF_U = 0.081547  # FullProf U
FULLPROF_V = -0.115345  # FullProf V
FULLPROF_W = 0.121125  # FullProf W
FULLPROF_X = 0.0  # FullProf X
FULLPROF_Y = 0.083038  # FullProf Y
FULLPROF_MARCH_R = 1.2  # FullProf Pref1 (March coefficient)

x, calc_fullprof = verify.load_fullprof_calc_profile(
    FULLPROF_PROJECT_DIR,
    FULLPROF_PRF_FILE,
    FULLPROF_BAC_FILE,
    FULLPROF_ZERO,
)

# %% [markdown]
# ## Create the experiment

# %%
experiment = ExperimentFactory.from_scratch(
    name='lbco',
    sample_form='powder',
    beam_mode='constant wavelength',
    radiation_probe='neutron',
    scattering_type='bragg',
)
verify.set_reference_as_measured(experiment, x, calc_fullprof)

experiment.linked_phases.create(id='lbco', scale=FULLPROF_SCALE)

experiment.instrument.setup_wavelength = FULLPROF_WAVELENGTH
experiment.instrument.calib_twotheta_offset = FULLPROF_ZERO

experiment.peak.type = 'pseudo-voigt'
experiment.peak.broad_gauss_u = FULLPROF_U
experiment.peak.broad_gauss_v = FULLPROF_V
experiment.peak.broad_gauss_w = FULLPROF_W
experiment.peak.broad_lorentz_x = FULLPROF_X
experiment.peak.broad_lorentz_y = FULLPROF_Y

# Same nominal March coefficient and direction as FullProf.
experiment.preferred_orientation.create(
    phase_id='lbco',
    r=FULLPROF_MARCH_R,
    index_h=0,
    index_k=0,
    index_l=1,
)

project.experiments.add(experiment)
experiment.calculator.type = 'cryspy'

# %% [markdown]
# ## ed-cryspy (`r = 1.2`) VS FullProf — same nominal March coefficient
#
# Despite using the identical coefficient and direction, the patterns
# differ markedly: CrysPy's texture function is not the standard
# March–Dollase one.

# %%
project.analysis.calculate()
calc_ed_cryspy_po = experiment.data.intensity_calc

project.display.pattern_comparison(
    'lbco',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy_po,
    reference_label='FullProf (March–Dollase r=1.2)',
    candidate_label='ed-cryspy (r=1.2)',
)

# %% [markdown]
# ## ed-cryspy (no texture, `r = 1`) VS FullProf
#
# Turning CrysPy's correction off (`r = 1`) is actually *closer* to the
# textured FullProf pattern than feeding CrysPy the matching `r = 1.2` —
# direct evidence that CrysPy's correction does not converge to
# March–Dollase for any coefficient.

# %%
experiment.preferred_orientation['lbco'].r = 1.0
project.analysis.calculate()
calc_ed_cryspy_nopo = experiment.data.intensity_calc

project.display.pattern_comparison(
    'lbco',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy_nopo,
    reference_label='FullProf (March–Dollase r=1.2)',
    candidate_label='ed-cryspy (no texture)',
)

# %% [markdown]
# ## Agreement table (documents the mismatch)
#
# Rendered with `raise_on_failure=False` so the page builds: the metrics
# are expected to be **out of tolerance** for `r = 1.2`, confirming the
# CrysPy↔FullProf March–Dollase divergence. This page is a standing
# reminder to revisit the mapping once CrysPy adopts the standard,
# intensity-conserving function.

# %%
verify.assert_patterns_agree(
    [
        ('cryspy r=1.2 vs FullProf', calc_fullprof, calc_ed_cryspy_po),
        ('cryspy no-texture vs FullProf', calc_fullprof, calc_ed_cryspy_nopo),
    ],
    raise_on_failure=False,
)
