# %% [markdown]
# # PbSO₄ — powder X-ray CW — round robin
#
# Verifies the anglesite X-ray round-robin case with the Cu Kα doublet
# and FullProf empirical asymmetry.
#
# **Refinement:** atomic ADPs, the overall scale, and Bérar-Baldinozzi
# coefficients (round-robin case); see the known difference below.

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

structure.cell.length_a = 8.485900  # FullProf a
structure.cell.length_b = 5.402259  # FullProf b
structure.cell.length_c = 6.964587  # FullProf c

structure.atom_sites.create(
    id='Pb',  # FullProf Atom
    type_symbol='Pb',  # FullProf Typ
    fract_x=0.18822,  # FullProf X
    fract_y=0.25,  # FullProf Y
    fract_z=0.16711,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=1.86290,  # FullProf Biso
)
structure.atom_sites.create(
    id='S',  # FullProf Atom
    type_symbol='S',  # FullProf Typ
    fract_x=0.06306,  # FullProf X
    fract_y=0.25,  # FullProf Y
    fract_z=0.68485,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=1.34971,  # FullProf Biso
)
structure.atom_sites.create(
    id='O1',  # FullProf Atom
    type_symbol='O',  # FullProf Typ
    fract_x=0.90281,  # FullProf X
    fract_y=0.25,  # FullProf Y
    fract_z=0.59724,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=1.19713,  # FullProf Biso
)
structure.atom_sites.create(
    id='O2',  # FullProf Atom
    type_symbol='O',  # FullProf Typ
    fract_x=0.18443,  # FullProf X
    fract_y=0.25,  # FullProf Y
    fract_z=0.54586,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=2.56174,  # FullProf Biso
)
structure.atom_sites.create(
    id='O3',  # FullProf Atom
    type_symbol='O',  # FullProf Typ
    fract_x=0.08094,  # FullProf X
    fract_y=0.02239,  # FullProf Y
    fract_z=0.81289,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=1.37463,  # FullProf Biso
)

project.structures.add(structure)

# %% [markdown]
# ## Load the FullProf reference

# %%
FULLPROF_PROJECT_DIR = 'pd-xray-cwl_pbso4_round-robin'
FULLPROF_PRF_FILE = 'pbsox.prf'
FULLPROF_SUM_FILE = 'pbsox.sum'
FULLPROF_BAC_FILE = 'pbsox.bac'
FULLPROF_LABEL = verify.fullprof_label(FULLPROF_PROJECT_DIR, FULLPROF_SUM_FILE)

FULLPROF_ZERO = 0.00363  # FullProf Zero
FULLPROF_SCALE = 0.0004703142  # FullProf Scale
FULLPROF_WAVELENGTH_1 = 1.540560  # FullProf Lambda1
FULLPROF_WAVELENGTH_2 = 1.544400  # FullProf Lambda2
FULLPROF_WAVELENGTH_2_TO_1_RATIO = 0.50000  # FullProf Ratio
FULLPROF_U = 0.048457  # FullProf U
FULLPROF_V = -0.083053  # FullProf V
FULLPROF_W = 0.035188  # FullProf W
FULLPROF_X = 0.0  # FullProf X
FULLPROF_Y = 0.058360  # FullProf Y
FULLPROF_WDT = 48.0  # FullProf Wdt
FULLPROF_ASY_1 = -0.41356  # FullProf Asy1
FULLPROF_ASY_2 = 0.0  # FullProf Asy2
FULLPROF_ASY_3 = 1.26777  # FullProf Asy3
FULLPROF_ASY_4 = 0.0  # FullProf Asy4

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
    radiation_probe='xray',
    scattering_type='bragg',
)
verify.set_reference_as_measured(experiment, x, calc_fullprof)

experiment.linked_structures.create(structure_id='pbso4', scale=FULLPROF_SCALE)

experiment.instrument.setup_wavelength = FULLPROF_WAVELENGTH_1
experiment.instrument.setup_wavelength_2 = FULLPROF_WAVELENGTH_2
experiment.instrument.setup_wavelength_2_to_1_ratio = FULLPROF_WAVELENGTH_2_TO_1_RATIO
experiment.instrument.calib_twotheta_offset = FULLPROF_ZERO

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

# FullProf excludes 0-10 deg and 154-180 deg in the PCR.
experiment.excluded_regions.create(id='1', start=0.0, end=10.0)
experiment.excluded_regions.create(id='2', start=154.0, end=180.0)

experiment.peak.cutoff_fwhm = FULLPROF_WDT

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
    reference=verify.restrict_to_included(experiment, calc_fullprof),
    candidate=calc_ed_cryspy,
    reference_label=FULLPROF_LABEL,
    candidate_label=LABEL_ED_CRYSPY,
)

# %% [markdown]
# ## Fit edi-cryspy to FullProf

# %%
# The anomalous-dispersion table discrepancy is partially compensated by
# scale and isotropic ADPs. The asymmetry terms are refined separately
# because cryspy and FullProf use different Berar-Baldinozzi conventions.
for atom_id in ('Pb', 'S', 'O1', 'O2', 'O3'):
    atom = structure.atom_sites[atom_id]
    atom.adp_iso.free = True

experiment.linked_structures['pbso4'].scale.free = True
experiment.peak.asym_beba_a0.free = True
experiment.peak.asym_beba_a1.free = True

project.analysis.fit()
project.display.fit.results()

project.analysis.calculate()
calc_ed_cryspy_refined = experiment.data.intensity_calc
LABEL_ED_CRYSPY_REFINED = verify.engine_label('cryspy', note='refined')

project.display.pattern_comparison(
    'pbso4',
    reference=verify.restrict_to_included(experiment, calc_fullprof),
    candidate=calc_ed_cryspy_refined,
    reference_label=FULLPROF_LABEL,
    candidate_label=LABEL_ED_CRYSPY_REFINED,
)

# %%
experiment.linked_structures['pbso4'].scale

# %% [markdown]
# ## Agreement check

# %%
verify.assert_patterns_agree(
    [
        (
            f'{LABEL_ED_CRYSPY} vs {FULLPROF_LABEL}',
            verify.restrict_to_included(experiment, calc_fullprof),
            calc_ed_cryspy,
        ),
        (
            f'{LABEL_ED_CRYSPY_REFINED} vs {FULLPROF_LABEL}',
            verify.restrict_to_included(experiment, calc_fullprof),
            calc_ed_cryspy_refined,
        ),
    ],
    known_discrepancy=True,
    reason=(
        'Laboratory X-ray PbSO4: the remaining strict-tolerance '
        'difference is partially compensated by refining scale and '
        'isotropic ADPs, consistent with a Cu Kalpha '
        'anomalous-dispersion table mismatch in f-prime/f-double-prime, '
        'especially for Pb. The Berar-Baldinozzi asymmetry terms are '
        'refined separately because cryspy and FullProf use different '
        'conventions.'
    ),
)
