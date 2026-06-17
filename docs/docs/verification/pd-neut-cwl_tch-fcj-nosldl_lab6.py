# %% [markdown]
# # LaB₆ — neutron powder, constant wavelength, sample absorption (no FCJ)

# %% [markdown]
# This page isolates the new Debye–Scherrer **sample-absorption**
# correction. The FullProf reference uses μR = 0.7 with the
# Finger–Cox–Jephcoat axial-divergence asymmetry switched off
# (S_L = D_L = 0), so the absorption correction is the only remaining
# angle-dependent intensity effect.
#
# The agreement is asserted against **ed-cryspy**, whose base intensities
# match FullProf for this sample. Without the correction the calculated
# pattern is ≈ 2.9× too intense (the FullProf reference is attenuated by
# absorption); enabling `cylinder-hewat` with μR = 0.7 brings ed-cryspy
# into agreement with FullProf. ed-crysfml is shown for completeness but
# not asserted: it has a separate, pre-existing intensity-convention
# difference with FullProf for LaB₆ that is independent of absorption.

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
structure = StructureFactory.from_scratch(name='lab6')
structure.space_group.name_h_m = 'P m -3 m'  # FullProf Space group symbol
structure.cell.length_a = 4.156885  # FullProf a
structure.atom_sites.create(
    id='La',  # FullProf Atom
    type_symbol='La',  # FullProf Typ
    fract_x=0.0,  # FullProf X
    fract_y=0.0,  # FullProf Y
    fract_z=0.0,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=0.59951,  # FullProf Biso
)
structure.atom_sites.create(
    id='B',  # FullProf Atom
    type_symbol='11B',  # FullProf "B11"
    fract_x=0.19978,  # FullProf X
    fract_y=0.5,  # FullProf Y
    fract_z=0.5,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=0.44499,  # FullProf Biso
)

project.structures.add(structure)

# %% [markdown]
# ## Load the FullProf reference

# %%
FULLPROF_PROJECT_DIR = 'pd-neut-cwl_tch-fcj_lab6'
FULLPROF_PRF_FILE = 'ECH0030684_LaB6_1p622A_noSLDL.prf'
FULLPROF_BAC_FILE = 'ECH0030684_LaB6_1p622A_noSLDL.bac'
FULLPROF_ZERO = -0.21110  # FullProf Zero
FULLPROF_SCALE = 141.1285  # FullProf Scale
FULLPROF_WAVELENGTH = 1.622527  # FullProf Lambda
FULLPROF_U = 0.089664  # FullProf U
FULLPROF_V = -0.375792  # FullProf V
FULLPROF_W = 0.476524  # FullProf W
FULLPROF_X = 0.0  # FullProf X
FULLPROF_Y = 0.052425  # FullProf Y
FULLPROF_SYCOS = 0.05281  # FullProf SyCos
FULLPROF_SYSIN = 0.09068  # FullProf SySin
FULLPROF_MU_R = 0.7  # FullProf muR (cylindrical absorption)

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
    name='lab6',
    sample_form='powder',
    beam_mode='constant wavelength',
    radiation_probe='neutron',
    scattering_type='bragg',
)
verify.set_reference_as_measured(experiment, x, calc_fullprof)

experiment.linked_structures.create(structure_id='lab6', scale=FULLPROF_SCALE)

experiment.instrument.setup_wavelength = FULLPROF_WAVELENGTH
experiment.instrument.calib_twotheta_offset = FULLPROF_ZERO

experiment.peak.broad_gauss_u = FULLPROF_U
experiment.peak.broad_gauss_v = FULLPROF_V
experiment.peak.broad_gauss_w = FULLPROF_W
experiment.peak.broad_lorentz_x = FULLPROF_X
experiment.peak.broad_lorentz_y = FULLPROF_Y

# Sample absorption (Debye-Scherrer cylinder, muR = 0.7) is modelled by
# both engines via the calculator-independent A(theta) envelope. No FCJ
# asymmetry is applied (the reference has S_L = D_L = 0).
experiment.absorption.type = 'cylinder-hewat'
experiment.absorption.mu_r = FULLPROF_MU_R

project.experiments.add(experiment)

# %% [markdown]
# ## ed-cryspy VS FullProf

# %%
experiment.calculator.type = 'cryspy'

experiment.instrument.calib_sample_displacement = FULLPROF_SYCOS
experiment.instrument.calib_sample_transparency = FULLPROF_SYSIN

project.analysis.calculate()
calc_ed_cryspy = experiment.data.intensity_calc

project.display.pattern_comparison(
    'lab6',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy,
    reference_label='FullProf',
    candidate_label='ed-cryspy',
)

# %% [markdown]
# ## ed-crysfml VS FullProf

# %%
experiment.calculator.type = 'crysfml'

experiment.peak.type = 'thompson-cox-hastings'
experiment.instrument.calib_twotheta_offset = FULLPROF_ZERO
experiment.peak.broad_gauss_u = FULLPROF_U
experiment.peak.broad_gauss_v = FULLPROF_V
experiment.peak.broad_gauss_w = FULLPROF_W
experiment.peak.broad_lorentz_x = FULLPROF_X
experiment.peak.broad_lorentz_y = FULLPROF_Y

project.analysis.calculate()
calc_ed_crysfml = experiment.data.intensity_calc

project.display.pattern_comparison(
    'lab6',
    reference=calc_fullprof,
    candidate=calc_ed_crysfml,
    reference_label='FullProf',
    candidate_label='ed-crysfml',
)

# %% [markdown]
# ## Agreement check
#
# Only ed-cryspy is asserted (see the note at the top): enabling the
# `cylinder-hewat` absorption brings it into agreement with the
# absorption-corrected FullProf reference.

# %%
verify.assert_patterns_agree(
    [
        ('cryspy vs FullProf', calc_fullprof, calc_ed_cryspy),
    ],
    raise_on_failure=True,
)
