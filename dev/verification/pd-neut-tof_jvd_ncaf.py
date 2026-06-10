# %% [markdown]
# # Na₂Ca₃Al₂F₁₄ — neutron powder, time-of-flight, Jorgensen–Von Dreele

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
structure = StructureFactory.from_scratch(name='ncaf')
structure.space_group.name_h_m = 'I 21 3'  # FullProf Space group symbol
structure.cell.length_a = 10.250256  # FullProf a
structure.atom_sites.create(
    label='Ca',  # FullProf Atom
    type_symbol='Ca',  # FullProf Typ
    fract_x=0.46610,  # FullProf X
    fract_y=0.0,  # FullProf Y
    fract_z=0.25,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=0.88721,  # FullProf Biso
)
structure.atom_sites.create(
    label='Al',  # FullProf Atom
    type_symbol='Al',  # FullProf Typ
    fract_x=0.25163,  # FullProf X
    fract_y=0.25163,  # FullProf Y
    fract_z=0.25163,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=0.65230,  # FullProf Biso
)
structure.atom_sites.create(
    label='Na',  # FullProf Atom
    type_symbol='Na',  # FullProf Typ
    fract_x=0.08472,  # FullProf X
    fract_y=0.08472,  # FullProf Y
    fract_z=0.08472,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=1.89168,  # FullProf Biso
)
structure.atom_sites.create(
    label='F1',  # FullProf Atom
    type_symbol='F',  # FullProf Typ
    fract_x=0.13748,  # FullProf X
    fract_y=0.30533,  # FullProf Y
    fract_z=0.11947,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=0.89535,  # FullProf Biso
)
structure.atom_sites.create(
    label='F2',  # FullProf Atom
    type_symbol='F',  # FullProf Typ
    fract_x=0.36263,  # FullProf X
    fract_y=0.36333,  # FullProf Y
    fract_z=0.18669,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=1.27175,  # FullProf Biso
)
structure.atom_sites.create(
    label='F3',  # FullProf Atom
    type_symbol='F',  # FullProf Typ
    fract_x=0.46120,  # FullProf X
    fract_y=0.46120,  # FullProf Y
    fract_z=0.46120,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=0.78029,  # FullProf Biso
)

project.structures.add(structure)

# %% [markdown]
# ## Load the FullProf reference

# %%
FULLPROF_PROJECT_DIR = 'pd-neut-tof_jvd_ncaf'
FULLPROF_PRF_FILE = 'tmpl_one_bank.prf'
FULLPROF_BAC_FILE = 'tmpl_one_bank.bac'
FULLPROF_SUM_FILE = 'tmpl_one_bank.sum'
FULLPROF_LABEL = verify.fullprof_label(FULLPROF_PROJECT_DIR, FULLPROF_SUM_FILE)
FULLPROF_ZERO = -13.88128  # FullProf Zero
FULLPROF_SCALE = 4.019304  # FullProf Scale
FULLPROF_TWOTHETA_BANK = 152.827  # FullProf 2ThetaBank
FULLPROF_DTT1 = 20773.12305  # FullProf Dtt1
FULLPROF_DTT2 = -1.08308  # FullProf Dtt2
FULLPROF_SIGMA_0 = 0.0  # FullProf Sigma-0
FULLPROF_SIGMA_1 = 0.0  # FullProf Sigma-1
FULLPROF_SIGMA_2 = 15.6959  # FullProf Sigma-2
FULLPROF_GAMMA_0 = 0.0  # FullProf Gamma-0
FULLPROF_GAMMA_1 = 0.0  # FullProf Gamma-1
FULLPROF_GAMMA_2 = 0.0  # FullProf Gamma-2
FULLPROF_ALPHA_0 = -0.009276  # FullProf alph0
FULLPROF_ALPHA_1 = 0.109622  # FullProf alph1
FULLPROF_BETA_0 = 0.006705  # FullProf beta0
FULLPROF_BETA_1 = 0.009708  # FullProf beta1

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
    name='ncaf',
    sample_form='powder',
    beam_mode='time-of-flight',
    radiation_probe='neutron',
    scattering_type='bragg',
)
verify.set_reference_as_measured(experiment, x, calc_fullprof)

experiment.linked_phases.create(id='ncaf', scale=FULLPROF_SCALE)

experiment.instrument.setup_twotheta_bank = FULLPROF_TWOTHETA_BANK
experiment.instrument.calib_d_to_tof_offset = FULLPROF_ZERO
experiment.instrument.calib_d_to_tof_linear = FULLPROF_DTT1
experiment.instrument.calib_d_to_tof_quad = FULLPROF_DTT2

experiment.peak.type = 'jorgensen-von-dreele'
experiment.peak.broad_gauss_sigma_0 = FULLPROF_SIGMA_0
experiment.peak.broad_gauss_sigma_1 = FULLPROF_SIGMA_1
experiment.peak.broad_gauss_sigma_2 = FULLPROF_SIGMA_2
experiment.peak.broad_lorentz_gamma_0 = FULLPROF_GAMMA_0
experiment.peak.broad_lorentz_gamma_1 = FULLPROF_GAMMA_1
experiment.peak.broad_lorentz_gamma_2 = FULLPROF_GAMMA_2
experiment.peak.exp_rise_alpha_0 = FULLPROF_ALPHA_0
experiment.peak.exp_rise_alpha_1 = FULLPROF_ALPHA_1
experiment.peak.exp_decay_beta_0 = FULLPROF_BETA_0
experiment.peak.exp_decay_beta_1 = FULLPROF_BETA_1

experiment.excluded_regions.create(id='1', start=0, end=30000)
experiment.excluded_regions.create(id='2', start=50000, end=200000)

project.experiments.add(experiment)

# %% [markdown]
# ## ed-cryspy VS FullProf

# %%
experiment.calculator.type = 'cryspy'

experiment.linked_phases['ncaf'].scale = FULLPROF_SCALE

project.analysis.calculate()
calc_ed_cryspy = experiment.data.intensity_calc

project.display.pattern_comparison(
    'ncaf',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy,
    reference_label=FULLPROF_LABEL,
    candidate_label='ed-cryspy',
)

# %% [markdown]
# ## Fit ed-cryspy to FullProf

# %%
# experiment.linked_phases['ncaf'].scale = 1.0927822317965166
experiment.linked_phases['ncaf'].scale.free = True

project.analysis.fit()
project.display.fit.results()

project.analysis.calculate()
calc_ed_cryspy_refined = experiment.data.intensity_calc

project.display.pattern_comparison(
    'ncaf',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy_refined,
    reference_label=FULLPROF_LABEL,
    candidate_label='ed-cryspy (refined)',
)

# %%
experiment.linked_phases['ncaf'].scale

# %% [markdown]
# ## ed-crysfml VS FullProf

# %%
experiment.calculator.type = 'crysfml'

experiment.linked_phases['ncaf'].scale = FULLPROF_SCALE

project.analysis.calculate()
calc_ed_crysfml = experiment.data.intensity_calc

project.display.pattern_comparison(
    'ncaf',
    reference=calc_fullprof,
    candidate=calc_ed_crysfml,
    reference_label=FULLPROF_LABEL,
    candidate_label='ed-crysfml',
)

# %% [markdown]
# ## Fit ed-crysfml to FullProf

# %%
# experiment.linked_phases['ncaf'].scale = 307.9429
experiment.linked_phases['ncaf'].scale.free = True

project.analysis.fit()
project.display.fit.results()

project.analysis.calculate()
calc_ed_crysfml_refined = experiment.data.intensity_calc

project.display.pattern_comparison(
    'ncaf',
    reference=calc_fullprof,
    candidate=calc_ed_crysfml_refined,
    reference_label=FULLPROF_LABEL,
    candidate_label='ed-crysfml (refined)',
)

# %%
experiment.linked_phases['ncaf'].scale

# %% [markdown]
# ## Agreement check

# %%
verify.assert_patterns_agree(
    [
        (
            'cryspy vs FullProf',
            verify.restrict_to_included(experiment, calc_fullprof),
            calc_ed_cryspy_refined,
        ),
        (
            'crysfml vs FullProf',
            verify.restrict_to_included(experiment, calc_fullprof),
            calc_ed_crysfml_refined,
        ),
    ],
    raise_on_failure=False,
)
