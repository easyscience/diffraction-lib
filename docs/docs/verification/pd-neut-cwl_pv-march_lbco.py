# %% [markdown]
# # LBCO — preferred orientation (March–Dollase)
#
# Cross-engine check of the **two-parameter** March–Dollase preferred-
# orientation correction. FullProf applies the standard model (its
# `.out` reports "March-Dollase model for preferred orientation") with
# `Pref1 = 1.2` and `Pref2 = 0.3` along `[0 0 1]`.
#
# EasyDiffraction's `march_r` and `march_random_fract` map to FullProf's
# `Pref1` and `Pref2`. CrysPy parametrises the same model with the
# **reciprocal** coefficient `g1 = 1/r`, so the backend inverts
# `march_r`; CrysPy's function is also not volume-normalised, which is a
# constant per-phase factor absorbed by the scale. Holding the two
# March–Dollase parameters at the FullProf values and refining only the
# scale, ed-cryspy reproduces the FullProf pattern.

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
# ## Define the structure

# %%
structure = StructureFactory.from_scratch(name='lbco')

structure.space_group.name_h_m = 'P m -3 m'  # FullProf Space group symbol

structure.cell.length_a = 3.890790  # FullProf a

structure.atom_sites.create(
    label='La',  # FullProf Atom
    type_symbol='La',  # FullProf Typ
    fract_x=0.0,  # FullProf X
    fract_y=0.0,  # FullProf Y
    fract_z=0.0,  # FullProf Z
    occupancy=0.5,  # FullProf Occ
    adp_type='Biso',  # FullProf Biso
    adp_iso=0.57511,  # FullProf Biso
)
structure.atom_sites.create(
    label='Ba',  # FullProf Atom
    type_symbol='Ba',  # FullProf Typ
    fract_x=0.0,  # FullProf X
    fract_y=0.0,  # FullProf Y
    fract_z=0.0,  # FullProf Z
    occupancy=0.5,  # FullProf Occ
    adp_type='Biso',  # FullProf Biso
    adp_iso=0.57511,  # FullProf Biso
)
structure.atom_sites.create(
    label='Co',  # FullProf Atom
    type_symbol='Co',  # FullProf Typ
    fract_x=0.5,  # FullProf X
    fract_y=0.5,  # FullProf Y
    fract_z=0.5,  # FullProf Z
    occupancy=1.0,  # FullProf Occ
    adp_type='Biso',  # FullProf Biso
    adp_iso=0.26023,  # FullProf Biso
)
structure.atom_sites.create(
    label='O',  # FullProf Atom
    type_symbol='O',  # FullProf Typ
    fract_x=0.0,  # FullProf X
    fract_y=0.5,  # FullProf Y
    fract_z=0.5,  # FullProf Z
    occupancy=0.97856,  # FullProf Occ
    adp_type='Biso',  # FullProf Biso
    adp_iso=1.36662,  # FullProf Biso
)

project.structures.add(structure)

# %% [markdown]
# ## Load the FullProf reference

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
    march_r=FULLPROF_MARCH_R,
    march_random_fract=FULLPROF_MARCH_FRACTION,
    index_h=0,
    index_k=0,
    index_l=1,
)

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
# Keep the two March–Dollase parameters fixed at the FullProf values
# (`march_r = Pref1`, `march_random_fract = Pref2`) and refine only the
# scale. The scale
# absorbs CrysPy's constant non-normalisation factor, and the patterns
# agree — so ed-cryspy reproduces the FullProf two-parameter
# March–Dollase pattern from the known coefficients.

# %%
experiment.linked_phases['lbco'].scale.free = True

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
