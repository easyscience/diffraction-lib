# %% [markdown]
# # Si — neutron powder, time-of-flight, Jorgensen

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
structure = StructureFactory.from_scratch(name='si')

structure.space_group.name_h_m = 'F d -3 m'  # FullProf Space group symbol
structure.space_group.it_coordinate_system_code = '2'

structure.cell.length_a = 5.432382  # FullProf a

structure.atom_sites.create(
    label='Si',  # FullProf Atom
    type_symbol='Si',  # FullProf Typ
    fract_x=0.125,  # FullProf X
    fract_y=0.125,  # FullProf Y
    fract_z=0.125,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=0.54095,  # FullProf Biso
)

project.structures.add(structure)

# %% [markdown]
# ## Load the FullProf reference

# %%
FULLPROF_PROJECT_DIR = 'pd-neut-tof_j_si'
FULLPROF_SUB_FILE = 'arg_si1.sub'
FULLPROF_SCALE = 0.6620058  # FullProf Scale
FULLPROF_TWOTHETA_BANK = 144.845  # FullProf 2ThetaBank
FULLPROF_DTT1 = 7476.91016  # FullProf Dtt1
FULLPROF_DTT2 = -1.54  # FullProf Dtt2
FULLPROF_SIGMA_0 = 5.0790  # FullProf Sigma-0
FULLPROF_SIGMA_1 = 29.6492  # FullProf Sigma-1
FULLPROF_SIGMA_2 = 0.0  # FullProf Sigma-2
FULLPROF_ALPHA_0 = 0.0  # FullProf alph0
FULLPROF_ALPHA_1 = 0.235422  # FullProf alph1
FULLPROF_BETA_0 = 0.038020  # FullProf beta0
FULLPROF_BETA_1 = 0.010902  # FullProf beta1

x, calc_fullprof = verify.load_fullprof_profile(FULLPROF_PROJECT_DIR, FULLPROF_SUB_FILE)

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

experiment.linked_phases.create(id='si', scale=FULLPROF_SCALE)

experiment.instrument.setup_twotheta_bank = FULLPROF_TWOTHETA_BANK
experiment.instrument.calib_d_to_tof_linear = FULLPROF_DTT1
experiment.instrument.calib_d_to_tof_quad = FULLPROF_DTT2

experiment.peak.type = 'jorgensen'
experiment.peak.broad_gauss_sigma_0 = FULLPROF_SIGMA_0
experiment.peak.broad_gauss_sigma_1 = FULLPROF_SIGMA_1
experiment.peak.broad_gauss_sigma_2 = FULLPROF_SIGMA_2
experiment.peak.exp_rise_alpha_0 = FULLPROF_ALPHA_0
experiment.peak.exp_rise_alpha_1 = FULLPROF_ALPHA_1
experiment.peak.exp_decay_beta_0 = FULLPROF_BETA_0
experiment.peak.exp_decay_beta_1 = FULLPROF_BETA_1

project.experiments.add(experiment)

# %% [markdown]
# ## ed-cryspy VS FullProf

# %%
experiment.calculator.type = 'cryspy'
project.analysis.calculate()
calc_ed_cryspy = experiment.data.intensity_calc

project.display.pattern_comparison(
    'si',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy,
    reference_label='FullProf',
    candidate_label='ed-cryspy',
)

# %% [markdown]
# ## Fit ed-cryspy to FullProf

# %%
experiment.calculator.type = 'cryspy'
experiment.linked_phases['si'].scale = 15.1026
experiment.linked_phases['si'].scale.free = True

project.analysis.fit()
project.display.fit.results()

project.analysis.calculate()
calc_ed_cryspy_refined = experiment.data.intensity_calc

project.display.pattern_comparison(
    'si',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy_refined,
    reference_label='FullProf',
    candidate_label='ed-cryspy (refined)',
)

# %% [markdown]
# ## ed-crysfml VS FullProf

# %%
experiment.calculator.type = 'crysfml'
experiment.linked_phases['si'].scale = FULLPROF_SCALE
experiment.linked_phases['si'].scale.free = False

project.analysis.calculate()
calc_ed_crysfml = experiment.data.intensity_calc

project.display.pattern_comparison(
    'si',
    reference=calc_fullprof,
    candidate=calc_ed_crysfml,
    reference_label='FullProf',
    candidate_label='ed-crysfml',
)

# %% [markdown]
# ## Fit ed-crysfml to FullProf

# %%
experiment.linked_phases['si'].scale = 15.1026
experiment.linked_phases['si'].scale.free = True

project.analysis.fit()
project.display.fit.results()

project.analysis.calculate()
calc_ed_crysfml_refined = experiment.data.intensity_calc

project.display.pattern_comparison(
    'si',
    reference=calc_fullprof,
    candidate=calc_ed_crysfml_refined,
    reference_label='FullProf',
    candidate_label='ed-crysfml (refined)',
)

# %% [markdown]
# ## Agreement check

# %%
verify.assert_patterns_agree(
    [
        ('cryspy vs FullProf', calc_fullprof, calc_ed_cryspy_refined),
        ('crysfml vs FullProf', calc_fullprof, calc_ed_crysfml_refined),
    ],
    raise_on_failure=False,
)
