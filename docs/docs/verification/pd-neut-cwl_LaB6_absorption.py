# %% [markdown]
# # LaB6 - powder neutron CW - absorption
#
# Verifies the LaB6 baseline with only Debye-Scherrer cylindrical
# absorption enabled.
#
# **Refinement:** none — every parameter is taken from the FullProf
# reference; only the calculated patterns are compared.

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
    type_symbol='B',  # FullProf Typ
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
FULLPROF_PROJECT_DIR = 'pd-neut-cwl_lab6'
FULLPROF_PRF_FILE = 'ECH0030684_LaB6_1p622A_absorption.prf'
FULLPROF_SUM_FILE = 'ECH0030684_LaB6_1p622A_absorption.sum'
FULLPROF_BAC_FILE = 'ECH0030684_LaB6_1p622A_absorption.bac'
FULLPROF_LABEL = verify.fullprof_label(FULLPROF_PROJECT_DIR, FULLPROF_SUM_FILE)

FULLPROF_ZERO = -0.45778  # FullProf Zero
FULLPROF_SCALE = 42.98374  # FullProf Scale
FULLPROF_WAVELENGTH = 1.623899  # FullProf Lambda
FULLPROF_U = 0.143431  # FullProf U
FULLPROF_V = -0.523140  # FullProf V
FULLPROF_W = 0.590412  # FullProf W
FULLPROF_X = 0.0  # FullProf X
FULLPROF_Y = 0.054515  # FullProf Y
FULLPROF_MU_R = 0.7  # FullProf muR

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

experiment.absorption.type = 'cylinder-hewat'
experiment.absorption.mu_r = FULLPROF_MU_R

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
    'lab6',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy,
    reference_label=FULLPROF_LABEL,
    candidate_label=LABEL_ED_CRYSPY,
)

# %% [markdown]
# ## Agreement check

# %%
verify.assert_patterns_agree([
    (f'{LABEL_ED_CRYSPY} vs {FULLPROF_LABEL}', calc_fullprof, calc_ed_cryspy),
])
