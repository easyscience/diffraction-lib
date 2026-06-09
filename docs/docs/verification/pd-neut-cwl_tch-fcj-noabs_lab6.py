# %% [markdown]
# # LaB₆ — neutron powder, constant wavelength, FCJ asymmetry

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
    label='La',  # FullProf Atom
    type_symbol='La',  # FullProf Typ
    fract_x=0.0,  # FullProf X
    fract_y=0.0,  # FullProf Y
    fract_z=0.0,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=0.32249,  # FullProf Biso
)
structure.atom_sites.create(
    label='B',  # FullProf Atom
    type_symbol='11B',  # FullProf "B11"
    fract_x=0.19978,  # FullProf X
    fract_y=0.5,  # FullProf Y
    fract_z=0.5,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=0.16910,  # FullProf Biso
)

project.structures.add(structure)

# %% [markdown]
# ## Load the FullProf reference

# %%
FULLPROF_PROJECT_DIR = 'pd-neut-cwl_tch-fcj_lab6'
FULLPROF_PRF_FILE = 'ECH0030684_LaB6_1p622A_noAbs.prf'
FULLPROF_BAC_FILE = 'ECH0030684_LaB6_1p622A_noAbs.bac'
FULLPROF_ZERO = -0.21148  # FullProf Zero
FULLPROF_SCALE = 44.51785  # FullProf Scale
FULLPROF_WAVELENGTH = 1.622528  # FullProf Lambda
FULLPROF_U = 0.089670  # FullProf U
FULLPROF_V = -0.375862  # FullProf V
FULLPROF_W = 0.476309  # FullProf W
FULLPROF_X = 0.0  # FullProf X
FULLPROF_Y = 0.052528  # FullProf Y
FULLPROF_SYCOS = 0.05290  # FullProf SyCos
FULLPROF_SYSIN = 0.09073  # FullProf SySin
FULLPROF_S_L = 0.08000  # FullProf S_L
FULLPROF_D_L = 0.08000  # FullProf D_L

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

experiment.linked_phases.create(id='lab6', scale=FULLPROF_SCALE)

experiment.instrument.setup_wavelength = FULLPROF_WAVELENGTH
experiment.instrument.calib_twotheta_offset = FULLPROF_ZERO

experiment.peak.broad_gauss_u = FULLPROF_U
experiment.peak.broad_gauss_v = FULLPROF_V
experiment.peak.broad_gauss_w = FULLPROF_W
experiment.peak.broad_lorentz_x = FULLPROF_X
experiment.peak.broad_lorentz_y = FULLPROF_Y
# Engine-specific corrections are applied in each engine's section below:
# SyCos/SySin (cryspy only) and the FCJ S_L/D_L asymmetry (crysfml only).

project.experiments.add(experiment)

# %% [markdown]
# ## ed-cryspy VS FullProf

# %%
experiment.instrument.calib_sample_displacement = FULLPROF_SYCOS
experiment.instrument.calib_sample_transparency = FULLPROF_SYSIN

experiment.calculator.type = 'cryspy'
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
# ## Fit ed-cryspy to FullProf

# %%
experiment.linked_phases['lab6'].scale.free = True
experiment.instrument.calib_twotheta_offset.free = True
experiment.instrument.calib_sample_displacement.free = True
experiment.instrument.calib_sample_transparency.free = True

project.analysis.minimizer.type = 'lmfit'
project.analysis.fit()

experiment.calculator.type = 'cryspy'
project.analysis.calculate()
calc_ed_cryspy_refined = experiment.data.intensity_calc

project.display.pattern_comparison(
    'lab6',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy_refined,
    reference_label='FullProf',
    candidate_label='ed-cryspy (refined)',
)

# %% [markdown]
# ## ed-crysfml VS FullProf

# %%
experiment.calculator.type = 'crysfml'
experiment.peak.type = 'thompson-cox-hastings'
experiment.linked_phases['lab6'].scale = FULLPROF_SCALE
experiment.linked_phases['lab6'].scale.free = False
experiment.instrument.calib_twotheta_offset = FULLPROF_ZERO
experiment.instrument.calib_twotheta_offset.free = False
experiment.instrument.calib_sample_displacement.free = False
experiment.instrument.calib_sample_transparency.free = False
experiment.peak.broad_gauss_u = FULLPROF_U
experiment.peak.broad_gauss_v = FULLPROF_V
experiment.peak.broad_gauss_w = FULLPROF_W
experiment.peak.broad_lorentz_x = FULLPROF_X
experiment.peak.broad_lorentz_y = FULLPROF_Y
experiment.peak.asym_fcj_1 = FULLPROF_S_L
experiment.peak.asym_fcj_2 = FULLPROF_D_L

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
# ## Fit ed-crysfml to FullProf

# %%
experiment.linked_phases['lab6'].scale.free = True
experiment.instrument.calib_twotheta_offset.free = True

project.analysis.fit()

experiment.calculator.type = 'crysfml'
project.analysis.calculate()
calc_ed_crysfml_refined = experiment.data.intensity_calc

project.display.pattern_comparison(
    'lab6',
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
        ('cryspy vs FullProf', calc_fullprof, calc_ed_cryspy),
        ('crysfml vs FullProf', calc_fullprof, calc_ed_crysfml),
    ],
    raise_on_failure=False,
)
