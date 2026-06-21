# %% [markdown]
# # Fe - powder neutron TOF - pseudo-Voigt profile
#
# Verifies the simple non-convoluted pseudo-Voigt time-of-flight peak
# profile.
#
# **Refinement:** the overall scale only; all other parameters are
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
structure = StructureFactory.from_scratch(name='fe')
structure.space_group.name_h_m = 'I m -3 m'  # FullProf Space group symbol
structure.cell.length_a = 2.886  # FullProf a
structure.atom_sites.create(
    id='Fe',  # FullProf Atom
    type_symbol='Fe',  # FullProf Typ
    fract_x=0.0,  # FullProf X
    fract_y=0.0,  # FullProf Y
    fract_z=0.0,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=1.71513,  # FullProf Biso
)

project.structures.add(structure)

# %% [markdown]
# ## Load the FullProf reference

# %%
FULLPROF_PROJECT_DIR = 'pd-neut-tof_fe_pseudo-voigt'
FULLPROF_PRF_FILE = 'fe_1.prf'
FULLPROF_SUM_FILE = 'fe.sum'
FULLPROF_BAC_FILE = 'fe_1.bac'
FULLPROF_LABEL = verify.fullprof_label(FULLPROF_PROJECT_DIR, FULLPROF_SUM_FILE)

FULLPROF_ZERO = -10.29183  # FullProf Zero
FULLPROF_SCALE = 401.4629  # FullProf Scale
FULLPROF_TWOTHETA_BANK = 90.0  # FullProf 2ThetaBank
FULLPROF_DTT1 = 54902.18750  # FullProf Dtt1
FULLPROF_DTT2 = 0.0  # FullProf Dtt2
FULLPROF_SIGMA_0 = 893.6397  # FullProf Sigma-0
FULLPROF_SIGMA_1 = 1283.6387  # FullProf Sigma-1
FULLPROF_SIGMA_2 = 311.7041  # FullProf Sigma-2
FULLPROF_GAMMA_0 = 5.0330  # FullProf Gamma-0
FULLPROF_GAMMA_1 = 0.0  # FullProf Gamma-1
FULLPROF_GAMMA_2 = 0.0  # FullProf Gamma-2

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
    name='fe',
    sample_form='powder',
    beam_mode='time-of-flight',
    radiation_probe='neutron',
    scattering_type='bragg',
)
verify.set_reference_as_measured(experiment, x, calc_fullprof)

experiment.linked_structures.create(structure_id='fe', scale=FULLPROF_SCALE)

experiment.instrument.setup_twotheta_bank = FULLPROF_TWOTHETA_BANK
experiment.instrument.calib_d_to_tof_offset = FULLPROF_ZERO
experiment.instrument.calib_d_to_tof_linear = FULLPROF_DTT1
experiment.instrument.calib_d_to_tof_quadratic = FULLPROF_DTT2

experiment.peak.type = 'pseudo-voigt'
experiment.peak.broad_gauss_sigma_0 = FULLPROF_SIGMA_0
experiment.peak.broad_gauss_sigma_1 = FULLPROF_SIGMA_1
experiment.peak.broad_gauss_sigma_2 = FULLPROF_SIGMA_2
experiment.peak.broad_lorentz_gamma_0 = FULLPROF_GAMMA_0
experiment.peak.broad_lorentz_gamma_1 = FULLPROF_GAMMA_1
experiment.peak.broad_lorentz_gamma_2 = FULLPROF_GAMMA_2

experiment.excluded_regions.create(id='1', start=0.0, end=40000.0)
experiment.excluded_regions.create(id='2', start=130000.0, end=180000.0)

# Match cryspy's peak-range cutoff to the FullProf Wdt used for
# this reference (12.0 FWHM) so both engines truncate identically.
experiment.peak.cutoff_fwhm = 12.0

project.experiments.add(experiment)

# %% [markdown]
# ## edi-cryspy VS FullProf

# %%
experiment.calculator.type = 'cryspy'

project.analysis.calculate()
calc_ed_cryspy = experiment.data.intensity_calc
LABEL_ED_CRYSPY = verify.engine_label('cryspy')

project.display.pattern_comparison(
    'fe',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy,
    reference_label=FULLPROF_LABEL,
    candidate_label=LABEL_ED_CRYSPY,
)

# %% [markdown]
# ## Fit edi-cryspy to FullProf

# %%
experiment.linked_structures['fe'].scale.free = True

project.analysis.fit()
project.display.fit.results()

project.analysis.calculate()
calc_ed_cryspy_refined = experiment.data.intensity_calc
LABEL_ED_CRYSPY_REFINED = verify.engine_label('cryspy', note='scale only')

project.display.pattern_comparison(
    'fe',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy_refined,
    reference_label=FULLPROF_LABEL,
    candidate_label=LABEL_ED_CRYSPY_REFINED,
)

# %% [markdown]
# ## Agreement check

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
