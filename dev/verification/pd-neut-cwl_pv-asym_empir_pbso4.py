# %% [markdown]
# # PbSO₄ — neutron powder, constant wavelength, empirical asymmetry

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
structure = StructureFactory.from_scratch(name='pbso4')

structure.space_group.name_h_m = 'P n m a'  # FullProf Space group symbol

structure.cell.length_a = 8.479506  # FullProf a
structure.cell.length_b = 5.397256  # FullProf b
structure.cell.length_c = 6.958973  # FullProf c

structure.atom_sites.create(
    label='Pb',  # FullProf Atom
    type_symbol='Pb',  # FullProf Typ
    fract_x=0.18752,  # FullProf X
    fract_y=0.25,  # FullProf Y
    fract_z=0.16705,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=1.39017,  # FullProf Biso
)
structure.atom_sites.create(
    label='S',  # FullProf Atom
    type_symbol='S',  # FullProf Typ
    fract_x=0.06549,  # FullProf X
    fract_y=0.25,  # FullProf Y
    fract_z=0.68373,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=0.39270,  # FullProf Biso
)
structure.atom_sites.create(
    label='O1',  # FullProf Atom
    type_symbol='O',  # FullProf Typ
    fract_x=0.90816,  # FullProf X
    fract_y=0.25,  # FullProf Y
    fract_z=0.59544,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=1.99307,  # FullProf Biso
)
structure.atom_sites.create(
    label='O2',  # FullProf Atom
    type_symbol='O',  # FullProf Typ
    fract_x=0.19355,  # FullProf X
    fract_y=0.25,  # FullProf Y
    fract_z=0.54331,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=1.47771,  # FullProf Biso
)
structure.atom_sites.create(
    label='O3',  # FullProf Atom
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
FULLPROF_PROJECT_DIR = 'pd-neut-cwl_pv-asym_empir_pbso4'
FULLPROF_PRF_FILE = 'pbso4.prf'
FULLPROF_BAC_FILE = 'pbso4.bac'
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

experiment.linked_phases.create(id='pbso4', scale=FULLPROF_SCALE)

experiment.instrument.setup_wavelength = FULLPROF_WAVELENGTH
experiment.instrument.calib_twotheta_offset = FULLPROF_ZERO

experiment.peak.type = 'pseudo-voigt'
experiment.peak.broad_gauss_u = FULLPROF_U
experiment.peak.broad_gauss_v = FULLPROF_V
experiment.peak.broad_gauss_w = FULLPROF_W
experiment.peak.broad_lorentz_x = FULLPROF_X
experiment.peak.broad_lorentz_y = FULLPROF_Y
# The empirical-asymmetry coefficients (cryspy only) are set in the
# cryspy section below; crysfml has no empirical-asymmetry model.

project.experiments.add(experiment)

# %% [markdown]
# ## ed-cryspy VS FullProf

# %%
experiment.peak.type = 'pseudo-voigt + empirical asymmetry'
experiment.peak.broad_gauss_u = FULLPROF_U
experiment.peak.broad_gauss_v = FULLPROF_V
experiment.peak.broad_gauss_w = FULLPROF_W
experiment.peak.broad_lorentz_x = FULLPROF_X
experiment.peak.broad_lorentz_y = FULLPROF_Y
experiment.peak.asym_empir_1 = FULLPROF_ASY_1
experiment.peak.asym_empir_2 = FULLPROF_ASY_2
experiment.peak.asym_empir_3 = FULLPROF_ASY_3
experiment.peak.asym_empir_4 = FULLPROF_ASY_4

experiment.calculator.type = 'cryspy'

project.analysis.calculate()
calc_ed_cryspy = experiment.data.intensity_calc

project.display.pattern_comparison(
    'pbso4',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy,
    reference_label='FullProf',
    candidate_label='ed-cryspy',
)

# %% [markdown]
# ## Fit ed-cryspy to FullProf

# %%
# cryspy and FullProf parameterise the empirical asymmetry differently, so
# the FullProf coefficients do not transfer 1-to-1. Freeing cryspy's own
# coefficients recovers the FullProf profile, confirming the structure and
# the symmetric profile are correct.
experiment.calculator.type = 'cryspy'

experiment.linked_phases['pbso4'].scale.free = True
experiment.peak.asym_empir_1.free = True
experiment.peak.asym_empir_2.free = True
experiment.peak.asym_empir_3.free = True
experiment.peak.asym_empir_4.free = True

project.analysis.fit()
project.display.fit.results()

project.analysis.calculate()
calc_ed_cryspy_refined = experiment.data.intensity_calc

project.display.pattern_comparison(
    'pbso4',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy_refined,
    reference_label='FullProf',
    candidate_label='ed-cryspy (refined)',
)

# %% [markdown]
# ## ed-crysfml VS FullProf

# %%
experiment.calculator.type = 'crysfml'

experiment.linked_phases['pbso4'].scale = FULLPROF_SCALE

experiment.peak.type = 'pseudo-voigt'
experiment.peak.broad_gauss_u = FULLPROF_U
experiment.peak.broad_gauss_v = FULLPROF_V
experiment.peak.broad_gauss_w = FULLPROF_W
experiment.peak.broad_lorentz_x = FULLPROF_X
experiment.peak.broad_lorentz_y = FULLPROF_Y

project.analysis.calculate()
calc_ed_crysfml = experiment.data.intensity_calc

project.display.pattern_comparison(
    'pbso4',
    reference=calc_fullprof,
    candidate=calc_ed_crysfml,
    reference_label='FullProf',
    candidate_label='ed-crysfml',
)

# %% [markdown]
# ## Fit ed-crysfml to FullProf

# %%
experiment.linked_phases['pbso4'].scale.free = True
experiment.instrument.calib_twotheta_offset.free = True

project.analysis.fit()
project.display.fit.results()

project.analysis.calculate()
calc_ed_crysfml_refined = experiment.data.intensity_calc

project.display.pattern_comparison(
    'pbso4',
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
