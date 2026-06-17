# %% [markdown]
# # LBCO — preferred orientation (March–Dollase)
#
# Cross-engine check of the **two-parameter** March–Dollase preferred-
# orientation correction. FullProf applies the standard model (its
# `.out` reports "March-Dollase model for preferred orientation") with
# `Pref1 = 1.2` and `Pref2 = 0.3` along `[0 0 1]`.
#
# EasyDiffraction exposes the standard `march_r` (= `Pref1`) and
# `march_random_fract` (= `Pref2`). CrysPy parametrises the **same**
# model but with the **reciprocal** coefficient `g1 = 1/r` and an
# overall factor that is not volume-normalised; the backend inverts
# `march_r` automatically, and the constant non-normalisation factor is
# absorbed by the scale (so the as-calculated pattern below shows an
# overall offset before fitting). After refining the two March–Dollase
# parameters and the scale, edi-cryspy recovers `march_r ≈ 1.2` and
# `march_random_fract ≈ 0.3` and the patterns agree.

# %%
import easydiffraction as edi
from easydiffraction import ExperimentFactory
from easydiffraction import StructureFactory
from easydiffraction.analysis import verification as verify

# %% [markdown]
# ## Build the project

# %%
project = edi.Project()

# %% [markdown]
# ## Define the structure

# %%
structure = StructureFactory.from_scratch(name='lbco')

structure.space_group.name_h_m = 'P m -3 m'  # FullProf Space group symbol

structure.cell.length_a = 3.890790  # FullProf a

structure.atom_sites.create(
    id='La',  # FullProf Atom
    type_symbol='La',  # FullProf Typ
    fract_x=0.0,  # FullProf X
    fract_y=0.0,  # FullProf Y
    fract_z=0.0,  # FullProf Z
    occupancy=0.5,  # FullProf Occ
    adp_type='Biso',  # FullProf Biso
    adp_iso=0.57511,  # FullProf Biso
)
structure.atom_sites.create(
    id='Ba',  # FullProf Atom
    type_symbol='Ba',  # FullProf Typ
    fract_x=0.0,  # FullProf X
    fract_y=0.0,  # FullProf Y
    fract_z=0.0,  # FullProf Z
    occupancy=0.5,  # FullProf Occ
    adp_type='Biso',  # FullProf Biso
    adp_iso=0.57511,  # FullProf Biso
)
structure.atom_sites.create(
    id='Co',  # FullProf Atom
    type_symbol='Co',  # FullProf Typ
    fract_x=0.5,  # FullProf X
    fract_y=0.5,  # FullProf Y
    fract_z=0.5,  # FullProf Z
    occupancy=1.0,  # FullProf Occ
    adp_type='Biso',  # FullProf Biso
    adp_iso=0.26023,  # FullProf Biso
)
structure.atom_sites.create(
    id='O',  # FullProf Atom
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
FULLPROF_SUM_FILE = 'lbco.sum'
FULLPROF_LABEL = verify.fullprof_label(FULLPROF_PROJECT_DIR, FULLPROF_SUM_FILE)
FULLPROF_BAC_FILE = 'lbco.bac'
FULLPROF_ZERO = 0.62040  # FullProf Zero
FULLPROF_SCALE = 9.405870  # FullProf Scale
FULLPROF_WAVELENGTH = 1.494000  # FullProf Lambda
FULLPROF_U = 0.081547  # FullProf U
FULLPROF_V = -0.115345  # FullProf V
FULLPROF_W = 0.121125  # FullProf W
FULLPROF_X = 0.0  # FullProf X
FULLPROF_Y = 0.083038  # FullProf Y
FULLPROF_PREF_1 = 1.2  # FullProf Pref1
FULLPROF_PREF_2 = 0.3  # FullProf Pref2
FULLPROF_PR_1 = 0  # FullProf Pr1
FULLPROF_PR_2 = 0  # FullProf Pr2
FULLPROF_PR_3 = 1  # FullProf Pr3

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

experiment.linked_structures.create(structure_id='lbco', scale=FULLPROF_SCALE)

experiment.instrument.setup_wavelength = FULLPROF_WAVELENGTH
experiment.instrument.calib_twotheta_offset = FULLPROF_ZERO

experiment.peak.type = 'pseudo-voigt'
experiment.peak.broad_gauss_u = FULLPROF_U
experiment.peak.broad_gauss_v = FULLPROF_V
experiment.peak.broad_gauss_w = FULLPROF_W
experiment.peak.broad_lorentz_x = FULLPROF_X
experiment.peak.broad_lorentz_y = FULLPROF_Y

experiment.preferred_orientation.create(
    structure_id='lbco',
    march_r=FULLPROF_PREF_1,
    march_random_fract=FULLPROF_PREF_2,
    index_h=FULLPROF_PR_1,
    index_k=FULLPROF_PR_2,
    index_l=FULLPROF_PR_3,
)

project.experiments.add(experiment)

# %% [markdown]
# ## edi-cryspy VS FullProf

# %%
experiment.calculator.type = 'cryspy'

project.analysis.calculate()
calc_ed_cryspy = experiment.data.intensity_calc

project.display.pattern_comparison(
    'lbco',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy,
    reference_label=FULLPROF_LABEL,
    candidate_label=verify.engine_label('cryspy'),
)

# %% [markdown]
# ## Fit edi-cryspy to FullProf
#
# Free the two March–Dollase parameters (`march_r`, `march_random_fract`)
# and the scale, then refine. Starting from the FullProf values,
# edi-cryspy converges back to `march_r ≈ Pref1` and
# `march_random_fract ≈ Pref2`, and the patterns agree.

# %%
experiment.linked_structures['lbco'].scale.free = True
experiment.preferred_orientation['lbco'].march_r.free = True
experiment.preferred_orientation['lbco'].march_random_fract.free = True

project.analysis.fit()
project.display.fit.results()

project.analysis.calculate()
calc_ed_cryspy_refined = experiment.data.intensity_calc

project.display.pattern_comparison(
    'lbco',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy_refined,
    reference_label=FULLPROF_LABEL,
    candidate_label=verify.engine_label('cryspy', note='refined'),
)

# %% [markdown]
# ## Agreement check

# %%
verify.assert_patterns_agree(
    [
        (f'{verify.engine_label("cryspy", note="refined")} vs {FULLPROF_LABEL}', calc_fullprof, calc_ed_cryspy_refined),
    ],
)

# %% [markdown]
# The refined `march_r` returns to the FullProf `Pref1 = 1.2` and
# `march_random_fract` to `Pref2 = 0.3` (the latter only approximately,
# because CrysPy's non-normalised factor makes the random-fraction
# correspondence slightly non-linear), with all closeness metrics within
# tolerance. edi-cryspy therefore reproduces the FullProf two-parameter
# March–Dollase correction once its reciprocal/unnormalised convention is
# accounted for by the backend mapping and the scale.
