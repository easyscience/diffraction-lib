# %% [markdown]
# # PbSO₄ — powder neutron CW — basic pseudo-Voigt
#
# Verifies the baseline constant-wavelength neutron powder pattern for
# anglesite with a pseudo-Voigt peak shape and no asymmetry correction.
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
structure = StructureFactory.from_scratch(name='pbso4')

structure.space_group.name_h_m = 'P n m a'  # FullProf Space group symbol

structure.cell.length_a = 8.477992  # FullProf a
structure.cell.length_b = 5.396482  # FullProf b
structure.cell.length_c = 6.957715  # FullProf c

structure.atom_sites.create(
    id='Pb',  # FullProf Atom
    type_symbol='Pb',  # FullProf Typ
    fract_x=0.18754,  # FullProf X
    fract_y=0.25,  # FullProf Y
    fract_z=0.16709,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=1.38058,  # FullProf Biso
)
structure.atom_sites.create(
    id='S',  # FullProf Atom
    type_symbol='S',  # FullProf Typ
    fract_x=0.06532,  # FullProf X
    fract_y=0.25,  # FullProf Y
    fract_z=0.68401,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=0.36192,  # FullProf Biso
)
structure.atom_sites.create(
    id='O1',  # FullProf Atom
    type_symbol='O',  # FullProf Typ
    fract_x=0.90822,  # FullProf X
    fract_y=0.25,  # FullProf Y
    fract_z=0.59542,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=2.03661,  # FullProf Biso
)
structure.atom_sites.create(
    id='O2',  # FullProf Atom
    type_symbol='O',  # FullProf Typ
    fract_x=0.19390,  # FullProf X
    fract_y=0.25,  # FullProf Y
    fract_z=0.54359,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=1.50417,  # FullProf Biso
)
structure.atom_sites.create(
    id='O3',  # FullProf Atom
    type_symbol='O',  # FullProf Typ
    fract_x=0.08114,  # FullProf X
    fract_y=0.02713,  # FullProf Y
    fract_z=0.80863,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=1.34347,  # FullProf Biso
)

project.structures.add(structure)

# %% [markdown]
# ## Load the FullProf reference

# %%
FULLPROF_PROJECT_DIR = 'pd-neut-cwl_pbso4_basic'
FULLPROF_PRF_FILE = 'pbso4.prf'
FULLPROF_SUM_FILE = 'pbso4.sum'
FULLPROF_BAC_FILE = 'pbso4.bac'
FULLPROF_LABEL = verify.fullprof_label(FULLPROF_PROJECT_DIR, FULLPROF_SUM_FILE)

FULLPROF_ZERO = -0.14357  # FullProf Zero
FULLPROF_SCALE = 1.467900  # FullProf Scale
FULLPROF_WAVELENGTH = 1.912000  # FullProf Lambda
FULLPROF_U = 0.139488  # FullProf U
FULLPROF_V = -0.414074  # FullProf V
FULLPROF_W = 0.388200  # FullProf W
FULLPROF_X = 0.0  # FullProf X
FULLPROF_Y = 0.086383  # FullProf Y

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
    name='pbso4',
    sample_form='powder',
    beam_mode='constant wavelength',
    radiation_probe='neutron',
    scattering_type='bragg',
)
verify.set_reference_as_measured(experiment, x, calc_fullprof)

experiment.linked_structures.create(structure_id='pbso4', scale=FULLPROF_SCALE)

experiment.instrument.setup_wavelength = FULLPROF_WAVELENGTH
experiment.instrument.calib_twotheta_offset = FULLPROF_ZERO

experiment.peak.type = 'pseudo-voigt'
experiment.peak.broad_gauss_u = FULLPROF_U
experiment.peak.broad_gauss_v = FULLPROF_V
experiment.peak.broad_gauss_w = FULLPROF_W
experiment.peak.broad_lorentz_x = FULLPROF_X
experiment.peak.broad_lorentz_y = FULLPROF_Y

# Match cryspy's peak-range cutoff to the FullProf Wdt used for
# this reference (30.0 FWHM) so both engines truncate identically.
experiment.peak.cutoff_fwhm = 30.0

project.experiments.add(experiment)

# %% [markdown]
# ## edi-cryspy VS FullProf

# %%
experiment.calculator.type = 'cryspy'

project.analysis.calculate()
calc_ed_cryspy = experiment.data.intensity_calc
LABEL_ED_CRYSPY = verify.engine_label('cryspy')

project.display.pattern_comparison(
    'pbso4',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy,
    reference_label=FULLPROF_LABEL,
    candidate_label=LABEL_ED_CRYSPY,
)

# %% [markdown]
# ## edi-crysfml VS FullProf

# %%
experiment.calculator.type = 'crysfml'

project.analysis.calculate()
calc_ed_crysfml = experiment.data.intensity_calc
LABEL_ED_CRYSFML = verify.engine_label('crysfml')

project.display.pattern_comparison(
    'pbso4',
    reference=calc_fullprof,
    candidate=calc_ed_crysfml,
    reference_label=FULLPROF_LABEL,
    candidate_label=LABEL_ED_CRYSFML,
)

# %% [markdown]
# ## Agreement check

# %%
verify.assert_patterns_agree(
    [
        (f'{LABEL_ED_CRYSPY} vs {FULLPROF_LABEL}', calc_fullprof, calc_ed_cryspy),
        (f'{LABEL_ED_CRYSFML} vs {FULLPROF_LABEL}', calc_fullprof, calc_ed_crysfml),
    ],
)
