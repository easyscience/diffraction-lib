# %% [markdown]
# # LBCO — preferred orientation (March–Dollase): ed-cryspy VS FullProf
#
# Cross-engine check of the **two-parameter** March–Dollase preferred-
# orientation correction. FullProf applies the standard model (its
# `.out` reports "March-Dollase model for preferred orientation") with
# `Pref1 = 1.2` and `Pref2 = 0.3` along `[0 0 1]`.
#
# EasyDiffraction's `r` and `fraction` map to FullProf's `Pref1` and
# `Pref2`. CrysPy parametrises the same model with the **reciprocal**
# coefficient `g1 = 1/r`, so the backend inverts `r`; CrysPy's function
# is also not volume-normalised, which is a constant per-phase factor
# absorbed by the scale (and slightly distorts the `fraction` ↔ `Pref2`
# correspondence). After refining the two preferred-orientation
# parameters and the scale, ed-cryspy reproduces the FullProf pattern
# and recovers `r ≈ 1.2`, `fraction ≈ 0.3`.

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
# ## Load the FullProf reference (March–Dollase `Pref1 = 1.2`, `Pref2 = 0.3`, axis `[0 0 1]`)

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
FULLPROF_MARCH_FRACTION = 0.3  # FullProf Pref2 (random fraction)

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

# Both preferred-orientation parameters, matching FullProf Pref1/Pref2.
experiment.preferred_orientation.create(
    phase_id='lbco',
    r=FULLPROF_MARCH_R,
    index_h=0,
    index_k=0,
    index_l=1,
)
experiment.preferred_orientation['lbco'].fraction = FULLPROF_MARCH_FRACTION

project.experiments.add(experiment)
experiment.calculator.type = 'cryspy'

# %% [markdown]
# ## ed-cryspy VS FullProf
#
# With FullProf's scale, the calculated pattern shows an overall offset:
# CrysPy's texture function is not volume-normalised, so the textured
# total intensity differs by a constant per-phase factor. The peak
# *shape* already matches; the scale is reconciled by the fit below.

# %%
project.analysis.calculate()
calc_ed_cryspy = experiment.data.intensity_calc

project.display.pattern_comparison(
    'lbco',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy,
    reference_label='FullProf',
    candidate_label='ed-cryspy',
)

# %% [markdown]
# ## Fit ed-cryspy to FullProf
#
# Refine the three parameters that carry the preferred-orientation
# information: the two March–Dollase parameters (`r`, `fraction`) and the
# scale. ed-cryspy converges back to the FullProf values
# (`r ≈ 1.2 = Pref1`, `fraction ≈ 0.3 = Pref2`) and the patterns agree.

# %%
experiment.linked_phases['lbco'].scale.free = True
experiment.preferred_orientation['lbco'].r.free = True
experiment.preferred_orientation['lbco'].fraction.free = True

project.analysis.fit()
project.display.fit.results()

project.analysis.calculate()
calc_ed_cryspy_refined = experiment.data.intensity_calc

project.display.pattern_comparison(
    'lbco',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy_refined,
    reference_label='FullProf',
    candidate_label='ed-cryspy (refined)',
)

# %% [markdown]
# ## Agreement check

# %%
verify.assert_patterns_agree(
    [
        ('cryspy refined vs FullProf', calc_fullprof, calc_ed_cryspy_refined),
    ],
)
