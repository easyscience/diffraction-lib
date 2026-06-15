# %% [markdown]
# # LaB₆ — neutron powder, constant wavelength, SyCos/SySin

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
    adp_iso=0.25812,  # FullProf Biso
)
structure.atom_sites.create(
    id='B',  # FullProf Atom
    type_symbol='11B',  # FullProf "B11     0.66500    0.00000   0"
    fract_x=0.19972,  # FullProf X
    fract_y=0.5,  # FullProf Y
    fract_z=0.5,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=0.11925,  # FullProf Biso
)

project.structures.add(structure)

# %% [markdown]
# ## Load the FullProf reference

# %%
FULLPROF_PROJECT_DIR = 'pd-neut-cwl_tch-fcj_lab6'
FULLPROF_PRF_FILE = 'ECH0030684_LaB6_1p622A_noAbs_noSLDL.prf'
FULLPROF_BAC_FILE = 'ECH0030684_LaB6_1p622A_noAbs_noSLDL.bac'
FULLPROF_ZERO = -0.45778  # FullProf Zero
FULLPROF_SCALE = 42.98374  # FullProf Scale
FULLPROF_WAVELENGTH = 1.623899  # FullProf Lambda
FULLPROF_U = 0.143431  # FullProf U
FULLPROF_V = -0.523140  # FullProf V
FULLPROF_W = 0.590412  # FullProf W
FULLPROF_X = 0.0  # FullProf X
FULLPROF_Y = 0.054515  # FullProf Y
FULLPROF_SYCOS = 0.01153  # FullProf SyCos
FULLPROF_SYSIN = 0.24334  # FullProf SySin

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
# SyCos/SySin (cryspy-only) are set in the cryspy section below.

experiment.peak.broad_gauss_u = FULLPROF_U
experiment.peak.broad_gauss_v = FULLPROF_V
experiment.peak.broad_gauss_w = FULLPROF_W
experiment.peak.broad_lorentz_x = FULLPROF_X
experiment.peak.broad_lorentz_y = FULLPROF_Y

project.experiments.add(experiment)

# %% [markdown]
# ## edi-cryspy VS FullProf

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
    candidate_label='edi-cryspy',
)

# %% [markdown]
# ## edi-crysfml VS FullProf

# %%
experiment.calculator.type = 'crysfml'

project.analysis.calculate()
calc_ed_crysfml = experiment.data.intensity_calc

project.display.pattern_comparison(
    'lab6',
    reference=calc_fullprof,
    candidate=calc_ed_crysfml,
    reference_label='FullProf',
    candidate_label='edi-crysfml',
)

# %% [markdown]
# ## Fit edi-crysfml to FullProf

# %%
experiment.linked_structures['lab6'].scale.free = True
experiment.instrument.calib_twotheta_offset.free = True

project.analysis.fit()
project.display.fit.results()

project.analysis.calculate()
calc_ed_crysfml_refined = experiment.data.intensity_calc

project.display.pattern_comparison(
    'lab6',
    reference=calc_fullprof,
    candidate=calc_ed_crysfml_refined,
    reference_label='FullProf',
    candidate_label='edi-crysfml (refined)',
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
