# %% [markdown]
# # LiF — powder X-ray CW — polarization
#
# Verifies the X-ray polarization correction on the same single-wavelength
# LiF reference.

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
structure = StructureFactory.from_scratch(name='lif')

structure.space_group.name_h_m = 'F m -3 m'  # FullProf Space group symbol
structure.cell.length_a = 4.026700  # FullProf a

structure.atom_sites.create(
    id='Li1',  # FullProf Atom
    type_symbol='Li',  # FullProf Typ
    fract_x=0.0,  # FullProf X
    fract_y=0.0,  # FullProf Y
    fract_z=0.0,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=1.20000,  # FullProf Biso
)
structure.atom_sites.create(
    id='F1',  # FullProf Atom
    type_symbol='F',  # FullProf Typ
    fract_x=0.5,  # FullProf X
    fract_y=0.5,  # FullProf Y
    fract_z=0.5,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=0.80000,  # FullProf Biso
)

project.structures.add(structure)

# %% [markdown]
# ## Load the FullProf reference

# %%
FULLPROF_PROJECT_DIR = 'pd-xray-cwl_lif'
FULLPROF_PRF_FILE = 'lif_single_polarized.prf'
FULLPROF_SUM_FILE = 'lif_single_polarized.sum'
FULLPROF_BAC_FILE = 'lif_single_polarized.bac'
FULLPROF_LABEL = verify.fullprof_label(FULLPROF_PROJECT_DIR, FULLPROF_SUM_FILE)

FULLPROF_ZERO = 0.0  # FullProf Zero
FULLPROF_SCALE = 0.01  # FullProf Scale
FULLPROF_WAVELENGTH = 1.540560  # FullProf Lambda1
FULLPROF_U = 0.048457  # FullProf U
FULLPROF_V = -0.083053  # FullProf V
FULLPROF_W = 0.040000  # FullProf W
FULLPROF_X = 0.0  # FullProf X
FULLPROF_Y = 0.049268  # FullProf Y
FULLPROF_POLARIZATION_COEFFICIENT = 0.5  # FullProf Rpolarz
FULLPROF_CTHM = 0.8 # FullProf Cthm
FULLPROF_MONOCHROMATOR_TWOTHETA = 26.5650511771 # acos(sqrt(Cthm)) in degrees

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
    name='lif',
    sample_form='powder',
    beam_mode='constant wavelength',
    radiation_probe='xray',
    scattering_type='bragg',
)
verify.set_reference_as_measured(experiment, x, calc_fullprof)

experiment.linked_structures.create(structure_id='lif', scale=FULLPROF_SCALE)

experiment.instrument.setup_wavelength = FULLPROF_WAVELENGTH
experiment.instrument.calib_twotheta_offset = FULLPROF_ZERO
experiment.instrument.setup_polarization_coefficient = (
    FULLPROF_POLARIZATION_COEFFICIENT
)
experiment.instrument.setup_monochromator_twotheta = (
    FULLPROF_MONOCHROMATOR_TWOTHETA
)

experiment.peak.type = 'pseudo-voigt'
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

project.analysis.calculate()
calc_ed_cryspy = experiment.data.intensity_calc
LABEL_ED_CRYSPY = verify.engine_label('cryspy')

project.display.pattern_comparison(
    'lif',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy,
    reference_label=FULLPROF_LABEL,
    candidate_label=LABEL_ED_CRYSPY,
)

# %% [markdown]
# ## Fit edi-cryspy to FullProf

# %%
experiment.linked_structures['lif'].scale.free = True

project.analysis.fit()
project.display.fit.results()

project.analysis.calculate()
calc_ed_cryspy_refined = experiment.data.intensity_calc
LABEL_ED_CRYSPY_REFINED = verify.engine_label('cryspy', note='refined')

project.display.pattern_comparison(
    'lif',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy_refined,
    reference_label=FULLPROF_LABEL,
    candidate_label=LABEL_ED_CRYSPY_REFINED,
)

# %% [markdown]
# ## edi-crysfml VS FullProf

# %%
experiment.calculator.type = 'crysfml'

experiment.linked_structures['lif'].scale = FULLPROF_SCALE

project.analysis.calculate()
calc_ed_crysfml = experiment.data.intensity_calc
LABEL_ED_CRYSFML = verify.engine_label('crysfml')

project.display.pattern_comparison(
    'lif',
    reference=calc_fullprof,
    candidate=calc_ed_crysfml,
    reference_label=FULLPROF_LABEL,
    candidate_label=LABEL_ED_CRYSFML,
)

# %% [markdown]
# ## Fit edi-crysfml to FullProf

# %%
experiment.linked_structures['lif'].scale.free = True

project.analysis.fit()
project.display.fit.results()

project.analysis.calculate()
calc_ed_crysfml_refined = experiment.data.intensity_calc
LABEL_ED_CRYSFML_REFINED = verify.engine_label('crysfml', note='refined')

project.display.pattern_comparison(
    'lif',
    reference=calc_fullprof,
    candidate=calc_ed_crysfml_refined,
    reference_label=FULLPROF_LABEL,
    candidate_label=LABEL_ED_CRYSFML_REFINED,
)

# %% [markdown]
# ## Agreement check

# %%
verify.assert_patterns_agree(
    [
        (
            f'{LABEL_ED_CRYSPY_REFINED} vs {FULLPROF_LABEL}',
            calc_fullprof,
            calc_ed_cryspy_refined,
        ),
        (
            f'{LABEL_ED_CRYSFML_REFINED} vs {FULLPROF_LABEL}',
            calc_fullprof,
            calc_ed_crysfml_refined,
        ),
    ]
)
