# %% [markdown]
# # Si — powder neutron TOF — Jorgensen-Von Dreele + size/strain
#
# Verifies the isotropic microstructural size/strain broadening on top of
# the Jorgensen-Von Dreele pseudo-Voigt profile for a silicon
# time-of-flight powder pattern.
#
# **Reference:** the FullProf scale and all other parameters are
# taken from the FullProf reference.

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
FULLPROF_PROJECT_DIR = 'pd-neut-tof_si_jorgensen-von-dreele-size-strain'
FULLPROF_PRF_FILE = 'arg_si.prf'
FULLPROF_SUM_FILE = 'arg_si.sum'
FULLPROF_BAC_FILE = 'arg_si.bac'
FULLPROF_LABEL = verify.fullprof_label(FULLPROF_PROJECT_DIR, FULLPROF_SUM_FILE)

FULLPROF_ZERO = -9.18766  # FullProf Zero
FULLPROF_SCALE = 388.8488  # FullProf Scale
FULLPROF_TWOTHETA_BANK = 144.845  # FullProf 2ThetaBank
FULLPROF_DTT1 = 7476.91016  # FullProf Dtt1
FULLPROF_DTT2 = -1.54  # FullProf Dtt2
# FullProf Sigma-2/Sigma-1 carry the Gaussian size/strain; Gamma-2/Gamma-1
# carry the Lorentzian size/strain (raw coefficients).
FULLPROF_SIGMA_0 = 3.5544  # FullProf Sigma-0
FULLPROF_SIGMA_1 = 38.0419  # FullProf Sigma-1 = base 33.0419 + G-strain 5
FULLPROF_SIGMA_2 = 20.0  # FullProf Sigma-2 = G-size 20
FULLPROF_GAMMA_0 = 0.0  # FullProf Gamma-0
FULLPROF_GAMMA_1 = 3.5430  # FullProf Gamma-1 = base 2.5430 + L-strain 1
FULLPROF_GAMMA_2 = 2.0  # FullProf Gamma-2 = L-size 2
FULLPROF_ALPHA_0 = 0.0  # FullProf alph0
FULLPROF_ALPHA_1 = 0.597100  # FullProf alph1
FULLPROF_BETA_0 = 0.042210  # FullProf beta0
FULLPROF_BETA_1 = 0.009460  # FullProf beta1
FULLPROF_WDT = 8.2  # FullProf Wdt

# cryspy raw size/strain coefficients (additive to the base sigma/gamma)
SIZE_G = 20.0  # adds to sigma_2 (Gaussian size, d⁴)
STRAIN_G = 5.0  # adds to sigma_1 (Gaussian strain, d²)
SIZE_L = 2.0  # adds to gamma_2 (Lorentzian size, d²)
STRAIN_L = 1.0  # adds to gamma_1 (Lorentzian strain, d)

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
# Base broadening (size/strain are supplied separately as additive terms)
experiment.peak.broad_gauss_sigma_0 = FULLPROF_SIGMA_0
experiment.peak.broad_gauss_sigma_1 = FULLPROF_SIGMA_1 - STRAIN_G
experiment.peak.broad_gauss_sigma_2 = FULLPROF_SIGMA_2 - SIZE_G
experiment.peak.broad_lorentz_gamma_0 = FULLPROF_GAMMA_0
experiment.peak.broad_lorentz_gamma_1 = FULLPROF_GAMMA_1 - STRAIN_L
experiment.peak.broad_lorentz_gamma_2 = FULLPROF_GAMMA_2 - SIZE_L
# Microstructural size/strain components
experiment.peak.broad_gauss_size_g = SIZE_G
experiment.peak.broad_gauss_strain_g = STRAIN_G
experiment.peak.broad_lorentz_size_l = SIZE_L
experiment.peak.broad_lorentz_strain_l = STRAIN_L
experiment.peak.rise_alpha_0 = FULLPROF_ALPHA_0
experiment.peak.rise_alpha_1 = FULLPROF_ALPHA_1
experiment.peak.decay_beta_0 = FULLPROF_BETA_0
experiment.peak.decay_beta_1 = FULLPROF_BETA_1

experiment.excluded_regions.create(id='1', start=0, end=5000)
experiment.excluded_regions.create(id='2', start=10000, end=100000)

experiment.peak.cutoff_fwhm = FULLPROF_WDT

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
# ## Agreement check
#
# With the cryspy TOF size/strain wiring and Jorgensen-Von Dreele fix
# (cryspy issue #49), the cryspy pattern now agrees with FullProf.

# %%
verify.assert_patterns_agree(
    [
        (
            f'{LABEL_ED_CRYSPY} vs {FULLPROF_LABEL}',
            verify.restrict_to_included(experiment, calc_fullprof),
            calc_ed_cryspy,
        ),
    ],
)
