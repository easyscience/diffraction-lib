# %% [markdown]
# # PbSO₄ — X-ray powder, single wavelength, polarized, Wdt 48
#
# **Note — diagnostic single-wavelength reference.**
#
# This is the X-ray Rietveld Round Robin anglesite (PbSO₄) measured with
# a laboratory Cu source, but with a single-wavelength FullProf reference
# generated from `pbsox_single_polarized.pcr`. The PCR keeps
# `Lambda1 = Lambda2`, sets `Ratio = 0`, uses `Wdt = 48`, and enables
# the FullProf X-ray polarization correction with `Rpolarz = 0.5` and
# `Cthm = 0.8`. The page isolates whether EasyDiffraction backends can
# reproduce a FullProf X-ray Lorentz-polarization correction when peak
# tail truncation is widened.

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

structure.cell.length_a = 8.479832  # FullProf a
structure.cell.length_b = 5.397758  # FullProf b
structure.cell.length_c = 6.959325  # FullProf c

structure.atom_sites.create(
    id='Pb',  # FullProf Atom
    type_symbol='Pb',  # FullProf Typ
    fract_x=0.18788,  # FullProf X
    fract_y=0.25,  # FullProf Y
    fract_z=0.16749,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=1.78522,  # FullProf Biso
)
structure.atom_sites.create(
    id='S',  # FullProf Atom
    type_symbol='S',  # FullProf Typ
    fract_x=0.06302,  # FullProf X
    fract_y=0.25,  # FullProf Y
    fract_z=0.68446,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=0.85413,  # FullProf Biso
)
structure.atom_sites.create(
    id='O1',  # FullProf Atom
    type_symbol='O',  # FullProf Typ
    fract_x=0.91235,  # FullProf X
    fract_y=0.25,  # FullProf Y
    fract_z=0.59346,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=1.33362,  # FullProf Biso
)
structure.atom_sites.create(
    id='O2',  # FullProf Atom
    type_symbol='O',  # FullProf Typ
    fract_x=0.18443,  # FullProf X
    fract_y=0.25,  # FullProf Y
    fract_z=0.53434,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=1.57511,  # FullProf Biso
)
structure.atom_sites.create(
    id='O3',  # FullProf Atom
    type_symbol='O',  # FullProf Typ
    fract_x=0.07573,  # FullProf X
    fract_y=0.01951,  # FullProf Y
    fract_z=0.81594,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=1.32792,  # FullProf Biso
)

project.structures.add(structure)

# %% [markdown]
# ## Load the FullProf reference

# %%
FULLPROF_PROJECT_DIR = 'pd-xray-pbso4'
FULLPROF_PRF_FILE = 'pbsox_single_polarized.prf'
FULLPROF_SUM_FILE = 'pbsox_single_polarized.sum'
FULLPROF_LABEL = verify.fullprof_label(FULLPROF_PROJECT_DIR, FULLPROF_SUM_FILE)
FULLPROF_BAC_FILE = 'pbsox_single_polarized.bac'
FULLPROF_ZERO = -0.04816  # FullProf Zero
FULLPROF_SCALE = 0.0004693346  # FullProf Scale
FULLPROF_WAVELENGTH = 1.540560  # FullProf Lambda1
FULLPROF_U = 0.048457  # FullProf U
FULLPROF_V = -0.083053  # FullProf V
FULLPROF_W = 0.035188  # FullProf W
FULLPROF_X = 0.0  # FullProf X
FULLPROF_Y = 0.049268  # FullProf Y
FULLPROF_WDT = 48.0  # FullProf Wdt
FULLPROF_POLARIZATION_COEFFICIENT = 0.5  # FullProf Rpolarz
FULLPROF_CTHM = 0.8  # FullProf Cthm

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

experiment.instrument.setup_wavelength = FULLPROF_WAVELENGTH
experiment.instrument.calib_twotheta_offset = FULLPROF_ZERO

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
    'pbso4',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy,
    reference_label=FULLPROF_LABEL,
    candidate_label=LABEL_ED_CRYSPY,
)

# %% [markdown]
# ## Fit edi-cryspy to FullProf

# %%
experiment.linked_structures['pbso4'].scale.free = True
experiment.peak.broad_gauss_u.free = True
experiment.peak.broad_gauss_v.free = True
experiment.peak.broad_gauss_w.free = True
experiment.peak.broad_lorentz_y.free = True

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

# %%
experiment.linked_structures['pbso4'].scale

# %% [markdown]
# ## edi-crysfml VS FullProf

# %%
experiment.calculator.type = 'crysfml'

experiment.linked_structures['pbso4'].scale = FULLPROF_SCALE
experiment.peak.broad_gauss_u = FULLPROF_U
experiment.peak.broad_gauss_v = FULLPROF_V
experiment.peak.broad_gauss_w = FULLPROF_W
experiment.peak.broad_lorentz_x = FULLPROF_X
experiment.peak.broad_lorentz_y = FULLPROF_Y

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
# ## Fit edi-crysfml to FullProf

# %%
experiment.linked_structures['pbso4'].scale.free = True
experiment.peak.broad_gauss_u.free = True
experiment.peak.broad_gauss_v.free = True
experiment.peak.broad_gauss_w.free = True
experiment.peak.broad_lorentz_y.free = True

project.analysis.fit()
project.display.fit.results()

project.analysis.calculate()
calc_ed_crysfml_refined = experiment.data.intensity_calc
LABEL_ED_CRYSFML_REFINED = verify.engine_label('crysfml', note='refined')

project.display.pattern_comparison(
    'pbso4',
    reference=calc_fullprof,
    candidate=calc_ed_crysfml_refined,
    reference_label=FULLPROF_LABEL,
    candidate_label=LABEL_ED_CRYSFML_REFINED,
)

# %%
experiment.linked_structures['pbso4'].scale

# %% [markdown]
# ## Agreement check

# %%
verify.assert_patterns_agree(
    [
        (f'{LABEL_ED_CRYSPY} vs {FULLPROF_LABEL}', calc_fullprof, calc_ed_cryspy),
        (
            f'{LABEL_ED_CRYSPY_REFINED} vs {FULLPROF_LABEL}',
            calc_fullprof,
            calc_ed_cryspy_refined,
        ),
        (f'{LABEL_ED_CRYSFML} vs {FULLPROF_LABEL}', calc_fullprof, calc_ed_crysfml),
        (
            f'{LABEL_ED_CRYSFML_REFINED} vs {FULLPROF_LABEL}',
            calc_fullprof,
            calc_ed_crysfml_refined,
        ),
    ],
    known_discrepancy=True,
    reason=(
        'Laboratory X-ray PbSO4 single-wavelength diagnostic with '
        'Wdt=48, Rpolarz=0.5, and Cthm=0.8: EasyDiffraction does not '
        'yet expose these X-ray optics fields or bind them to cryspy/'
        'crysfml, and the remaining strict-tolerance difference is '
        'also affected by FullProf/Cryspy Cu Kalpha anomalous-'
        'dispersion table differences, especially Pb f-prime.'
    ),
)

# %%
