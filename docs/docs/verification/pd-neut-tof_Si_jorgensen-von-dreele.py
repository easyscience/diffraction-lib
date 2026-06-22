# %% [markdown]
# # Si — powder neutron TOF — Jorgensen-Von Dreele profile
#
# Verifies the Jorgensen-Von Dreele pseudo-Voigt profile for a silicon
# time-of-flight powder pattern.
#
# **Refinement:** the overall scale only; the Lorentzian γ₁ is held at
# its FullProf value. With the cryspy Jorgensen-Von Dreele single-FWHM
# fix and the TOF Lorentz-factor fix (cryspy issue #49), the refined
# pattern agrees with FullProf.

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
structure = StructureFactory.from_scratch(name='si')

structure.space_group.name_h_m = 'F d -3 m'  # FullProf Space group symbol
structure.space_group.coord_system_code = '2'

structure.cell.length_a = 5.431342  # FullProf a

structure.atom_sites.create(
    id='Si',  # FullProf Atom
    type_symbol='Si',  # FullProf Typ
    fract_x=0.125,  # FullProf X
    fract_y=0.125,  # FullProf Y
    fract_z=0.125,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=0.52448,  # FullProf Biso
)

project.structures.add(structure)

# %% [markdown]
# ## Load the FullProf reference

# %%
FULLPROF_PROJECT_DIR = 'pd-neut-tof_si_jorgensen-von-dreele'
FULLPROF_PRF_FILE = 'arg_si.prf'
FULLPROF_SUM_FILE = 'arg_si.sum'
FULLPROF_BAC_FILE = 'arg_si.bac'
FULLPROF_LABEL = verify.fullprof_label(FULLPROF_PROJECT_DIR, FULLPROF_SUM_FILE)

FULLPROF_ZERO = -9.18766  # FullProf Zero
FULLPROF_SCALE = 0.6750847  # FullProf Scale
FULLPROF_TWOTHETA_BANK = 144.845  # FullProf 2ThetaBank
FULLPROF_DTT1 = 7476.91016  # FullProf Dtt1
FULLPROF_DTT2 = -1.54  # FullProf Dtt2
FULLPROF_SIGMA_0 = 3.5544  # FullProf Sigma-0
FULLPROF_SIGMA_1 = 33.0419  # FullProf Sigma-1
FULLPROF_SIGMA_2 = 0.0  # FullProf Sigma-2
FULLPROF_GAMMA_0 = 0.0  # FullProf Gamma-0
FULLPROF_GAMMA_1 = 2.5430  # FullProf Gamma-1
FULLPROF_GAMMA_2 = 0.0  # FullProf Gamma-2
FULLPROF_ALPHA_0 = 0.0  # FullProf alph0
FULLPROF_ALPHA_1 = 0.597100  # FullProf alph1
FULLPROF_BETA_0 = 0.042210  # FullProf beta0
FULLPROF_BETA_1 = 0.009460  # FullProf beta1

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
    name='si',
    sample_form='powder',
    beam_mode='time-of-flight',
    radiation_probe='neutron',
    scattering_type='bragg',
)
verify.set_reference_as_measured(experiment, x, calc_fullprof)

experiment.linked_structures.create(structure_id='si', scale=FULLPROF_SCALE)

experiment.instrument.setup_twotheta_bank = FULLPROF_TWOTHETA_BANK
experiment.instrument.calib_d_to_tof_offset = FULLPROF_ZERO
experiment.instrument.calib_d_to_tof_linear = FULLPROF_DTT1
experiment.instrument.calib_d_to_tof_quadratic = FULLPROF_DTT2

experiment.peak.type = 'jorgensen-von-dreele'
experiment.peak.broad_gauss_sigma_0 = FULLPROF_SIGMA_0
experiment.peak.broad_gauss_sigma_1 = FULLPROF_SIGMA_1
experiment.peak.broad_gauss_sigma_2 = FULLPROF_SIGMA_2
experiment.peak.broad_lorentz_gamma_0 = FULLPROF_GAMMA_0
experiment.peak.broad_lorentz_gamma_1 = FULLPROF_GAMMA_1
experiment.peak.broad_lorentz_gamma_2 = FULLPROF_GAMMA_2
experiment.peak.rise_alpha_0 = FULLPROF_ALPHA_0
experiment.peak.rise_alpha_1 = FULLPROF_ALPHA_1
experiment.peak.decay_beta_0 = FULLPROF_BETA_0
experiment.peak.decay_beta_1 = FULLPROF_BETA_1

experiment.excluded_regions.create(id='1', start=0, end=5000)
experiment.excluded_regions.create(id='2', start=10000, end=100000)

# Match cryspy's peak-range cutoff to the FullProf Wdt used for
# this reference (8.2 FWHM) so both engines truncate identically.
experiment.peak.cutoff_fwhm = 8.2

project.experiments.add(experiment)

# %% [markdown]
# ## edi-cryspy VS FullProf

# %%
experiment.calculator.type = 'cryspy'

experiment.linked_structures['si'].scale = FULLPROF_SCALE

project.analysis.calculate()
calc_ed_cryspy = experiment.data.intensity_calc
LABEL_ED_CRYSPY = verify.engine_label('cryspy')

project.display.pattern_comparison(
    'si',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy,
    reference_label=FULLPROF_LABEL,
    candidate_label=LABEL_ED_CRYSPY,
)

# %% [markdown]
# ## Fit edi-cryspy to FullProf

# %%
# experiment.linked_structures['si'].scale = 16.558439186694915
# experiment.peak.broad_lorentz_gamma_1 = 9.998261092381231
experiment.linked_structures['si'].scale.free = True
# experiment.peak.broad_lorentz_gamma_1.free = True

project.analysis.fit()
project.display.fit.results()

project.analysis.calculate()
calc_ed_cryspy_refined = experiment.data.intensity_calc
LABEL_ED_CRYSPY_REFINED = verify.engine_label('cryspy', note='refined')

project.display.pattern_comparison(
    'si',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy_refined,
    reference_label=FULLPROF_LABEL,
    candidate_label=LABEL_ED_CRYSPY_REFINED,
)

# %%
experiment.linked_structures['si'].scale

# %%
experiment.peak.broad_lorentz_gamma_1

# %% [markdown]
# ## Agreement check
#
# With the cryspy Jorgensen-Von Dreele single-FWHM fix and the TOF
# Lorentz-factor fix (cryspy issue #49), the refined cryspy pattern now
# agrees with FullProf.

# %%
verify.assert_patterns_agree(
    [
        (
            f'{LABEL_ED_CRYSPY_REFINED} vs {FULLPROF_LABEL}',
            verify.restrict_to_included(experiment, calc_fullprof),
            calc_ed_cryspy_refined,
        ),
    ],
)

# %%
