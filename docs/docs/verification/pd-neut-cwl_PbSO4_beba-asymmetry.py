# %% [markdown]
# # PbSO₄ — powder neutron CW — Bérar-Baldinozzi asymmetry
#
# Verifies the empirical Bérar-Baldinozzi asymmetry workflow for
# anglesite. The page fits cryspy asymmetry parameters because FullProf
# and cryspy use different coefficient conventions.

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

structure.cell.length_a = 8.479506  # FullProf a
structure.cell.length_b = 5.397256  # FullProf b
structure.cell.length_c = 6.958973  # FullProf c

structure.atom_sites.create(
    id='Pb',  # FullProf Atom
    type_symbol='Pb',  # FullProf Typ
    fract_x=0.18752,  # FullProf X
    fract_y=0.25,  # FullProf Y
    fract_z=0.16705,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=1.39017,  # FullProf Biso
)
structure.atom_sites.create(
    id='S',  # FullProf Atom
    type_symbol='S',  # FullProf Typ
    fract_x=0.06549,  # FullProf X
    fract_y=0.25,  # FullProf Y
    fract_z=0.68373,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=0.39270,  # FullProf Biso
)
structure.atom_sites.create(
    id='O1',  # FullProf Atom
    type_symbol='O',  # FullProf Typ
    fract_x=0.90816,  # FullProf X
    fract_y=0.25,  # FullProf Y
    fract_z=0.59544,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=1.99307,  # FullProf Biso
)
structure.atom_sites.create(
    id='O2',  # FullProf Atom
    type_symbol='O',  # FullProf Typ
    fract_x=0.19355,  # FullProf X
    fract_y=0.25,  # FullProf Y
    fract_z=0.54331,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=1.47771,  # FullProf Biso
)
structure.atom_sites.create(
    id='O3',  # FullProf Atom
    type_symbol='O',  # FullProf Typ
    fract_x=0.08109,  # FullProf X
    fract_y=0.02727,  # FullProf Y
    fract_z=0.80869,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=1.30007,  # FullProf Biso
)

project.structures.add(structure)

# %% [markdown]
# ## Load the FullProf reference

# %%
FULLPROF_PROJECT_DIR = 'pd-neut-cwl_pbso4_beba-asymmetry'
FULLPROF_PRF_FILE = 'pbso4.prf'
FULLPROF_SUM_FILE = 'pbso4.sum'
FULLPROF_BAC_FILE = 'pbso4.bac'
FULLPROF_LABEL = verify.fullprof_label(FULLPROF_PROJECT_DIR, FULLPROF_SUM_FILE)

FULLPROF_ZERO = -0.08424  # FullProf Zero
FULLPROF_SCALE = 1.463815  # FullProf Scale
FULLPROF_WAVELENGTH = 1.912000  # FullProf Lambda
FULLPROF_U = 0.153402  # FullProf U
FULLPROF_V = -0.453103  # FullProf V
FULLPROF_W = 0.419409  # FullProf W
FULLPROF_X = 0.0  # FullProf X
FULLPROF_Y = 0.086818  # FullProf Y
FULLPROF_ASY_1 = 0.29465  # FullProf Asy1
FULLPROF_ASY_2 = 0.02261  # FullProf Asy2
FULLPROF_ASY_3 = -0.10961  # FullProf Asy3
FULLPROF_ASY_4 = 0.04941  # FullProf Asy4

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
experiment.peak.type = 'pseudo-voigt + berar-baldinozzi asymmetry'
experiment.peak.broad_gauss_u = FULLPROF_U
experiment.peak.broad_gauss_v = FULLPROF_V
experiment.peak.broad_gauss_w = FULLPROF_W
experiment.peak.broad_lorentz_x = FULLPROF_X
experiment.peak.broad_lorentz_y = FULLPROF_Y
experiment.peak.asym_beba_a0 = FULLPROF_ASY_1
experiment.peak.asym_beba_b0 = FULLPROF_ASY_2
experiment.peak.asym_beba_a1 = FULLPROF_ASY_3
experiment.peak.asym_beba_b1 = FULLPROF_ASY_4

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
# ## Fit edi-cryspy to FullProf

# %%
# cryspy and FullProf implement the Berar-Baldinozzi asymmetry with
# different conventions, so the FullProf coefficients do not transfer
# 1-to-1. Freeing cryspy's own coefficients recovers the FullProf
# profile, confirming the structure and the symmetric profile are
# correct.
experiment.calculator.type = 'cryspy'

experiment.peak.asym_beba_a0.free = True
experiment.peak.asym_beba_b0.free = True
experiment.peak.asym_beba_a1.free = True
experiment.peak.asym_beba_b1.free = True

project.analysis.fit()
project.display.fit.results()

project.analysis.calculate()
calc_ed_cryspy_refined = experiment.data.intensity_calc
LABEL_ED_CRYSPY_REFINED = verify.engine_label('cryspy', note='refined')

project.display.pattern_comparison(
    'pbso4',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy_refined,
    reference_label=FULLPROF_LABEL,
    candidate_label=LABEL_ED_CRYSPY_REFINED,
)

# %% [markdown]
# ## Agreement check

# %%
verify.assert_patterns_agree([
    (f'{LABEL_ED_CRYSPY_REFINED} vs {FULLPROF_LABEL}', calc_fullprof, calc_ed_cryspy_refined),
])
