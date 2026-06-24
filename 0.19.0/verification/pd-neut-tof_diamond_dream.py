# %% [markdown]
# # Diamond — powder neutron TOF — DREAM (ESS, McStas)
#
# Verifies the Jorgensen back-to-back exponential TOF profile against a
# FullProf reference fitted to McStas-simulated reduced data from the
# DREAM diffractometer at ESS.
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
structure = StructureFactory.from_scratch(name='diamond')

structure.space_group.name_h_m = 'F d -3 m'  # FullProf Space group symbol
structure.space_group.coord_system_code = '1'  # FullProf ":1" origin choice

structure.cell.length_a = 3.567  # FullProf a

structure.atom_sites.create(
    id='C',  # FullProf Atom
    type_symbol='C',  # FullProf Typ
    fract_x=0.125,  # FullProf X
    fract_y=0.125,  # FullProf Y
    fract_z=0.125,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=0.89263,  # FullProf Biso
)

project.structures.add(structure)

# %% [markdown]
# ## Load the FullProf reference

# %%
FULLPROF_PROJECT_DIR = 'pd-neut-tof_diamond_dream'
FULLPROF_PRF_FILE = 'diamond.prf'
FULLPROF_SUM_FILE = 'diamond.sum'
FULLPROF_BAC_FILE = 'diamond.bac'
FULLPROF_LABEL = verify.fullprof_label(FULLPROF_PROJECT_DIR, FULLPROF_SUM_FILE)

FULLPROF_ZERO = 0.0  # FullProf Zero
FULLPROF_SCALE = 0.1011780  # FullProf Scale
FULLPROF_TWOTHETA_BANK = 90.0  # FullProf 2ThetaBank
FULLPROF_DTT1 = 28385.86133  # FullProf Dtt1
FULLPROF_DTT2 = 0.0  # FullProf Dtt2
FULLPROF_SIGMA_0 = 46937.7188  # FullProf Sigma-0
FULLPROF_SIGMA_1 = 4887.9180  # FullProf Sigma-1
FULLPROF_SIGMA_2 = 0.0  # FullProf Sigma-2
FULLPROF_ALPHA_0 = 0.0  # FullProf alph0
FULLPROF_ALPHA_1 = 0.022544  # FullProf alph1
FULLPROF_BETA_0 = 0.014330  # FullProf beta0
FULLPROF_BETA_1 = 0.0  # FullProf beta1
FULLPROF_WDT = 30.0  # FullProf Wdt

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
    name='diamond',
    sample_form='powder',
    beam_mode='time-of-flight',
    radiation_probe='neutron',
    scattering_type='bragg',
)
verify.set_reference_as_measured(experiment, x, calc_fullprof)

experiment.linked_structures.create(structure_id='diamond', scale=FULLPROF_SCALE)

experiment.instrument.setup_twotheta_bank = FULLPROF_TWOTHETA_BANK
experiment.instrument.calib_d_to_tof_offset = FULLPROF_ZERO
experiment.instrument.calib_d_to_tof_linear = FULLPROF_DTT1
experiment.instrument.calib_d_to_tof_quadratic = FULLPROF_DTT2

experiment.peak.type = 'jorgensen'
experiment.peak.broad_gauss_sigma_0 = FULLPROF_SIGMA_0
experiment.peak.broad_gauss_sigma_1 = FULLPROF_SIGMA_1
experiment.peak.broad_gauss_sigma_2 = FULLPROF_SIGMA_2
experiment.peak.rise_alpha_0 = FULLPROF_ALPHA_0
experiment.peak.rise_alpha_1 = FULLPROF_ALPHA_1
experiment.peak.decay_beta_0 = FULLPROF_BETA_0
experiment.peak.decay_beta_1 = FULLPROF_BETA_1

experiment.excluded_regions.create(id='1', start=0, end=10000)
experiment.excluded_regions.create(id='2', start=70000, end=200000)

experiment.peak.cutoff_fwhm = FULLPROF_WDT

project.experiments.add(experiment)

# %% [markdown]
# ## edi-cryspy VS FullProf

# %%
experiment.calculator.type = 'cryspy'

experiment.linked_structures['diamond'].scale = FULLPROF_SCALE

project.analysis.calculate()
calc_ed_cryspy = experiment.data.intensity_calc
LABEL_ED_CRYSPY = verify.engine_label('cryspy')

project.display.pattern_comparison(
    'diamond',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy,
    reference_label=FULLPROF_LABEL,
    candidate_label=LABEL_ED_CRYSPY,
)

# %% [markdown]
# ## Fit edi-cryspy to FullProf

# %%
experiment.linked_structures['diamond'].scale.free = True

project.analysis.fit()
project.display.fit.results()

project.analysis.calculate()
calc_ed_cryspy_refined = experiment.data.intensity_calc
LABEL_ED_CRYSPY_REFINED = verify.engine_label('cryspy', note='refined')

project.display.pattern_comparison(
    'diamond',
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
