# %% [markdown]
# # Y2O3 - powder neutron CW - beta ADPs
#
# Verifies dimensionless beta-tensor anisotropic ADPs on a pseudo-Voigt
# neutron powder pattern with other correction models disabled.
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
#
# Occupancies are the crystallographic site fractions (all fully
# occupied). FullProf's `.pcr` lists the multiplicity-weighted values
# (0.5, 0.16667, 1.0 for the 24d, 8b and 48e sites); cryspy derives the
# site multiplicity from the symmetry, so the fractions are 1.0 here.

# %%
structure = StructureFactory.from_scratch(name='y2o3')

structure.space_group.name_h_m = 'I a -3'  # FullProf Space group symbol

structure.cell.length_a = 10.605744  # FullProf a

structure.atom_sites.create(
    id='Y1',  # FullProf Atom
    type_symbol='Y',  # FullProf Typ
    fract_x=-0.03236,  # FullProf X
    fract_y=0.0,  # FullProf Y
    fract_z=0.25,  # FullProf Z
    occupancy=1.0,  # FullProf Occ 0.50000 (24d site)
    adp_type='beta',  # FullProf N_t = 2 (anisotropic β)
)
structure.atom_sites.create(
    id='Y2',  # FullProf Atom
    type_symbol='Y',  # FullProf Typ
    fract_x=0.25,  # FullProf X
    fract_y=0.25,  # FullProf Y
    fract_z=0.25,  # FullProf Z
    occupancy=1.0,  # FullProf Occ 0.16667 (8b site)
    adp_type='beta',  # FullProf N_t = 2 (anisotropic β)
)
structure.atom_sites.create(
    id='O1',  # FullProf Atom
    type_symbol='O',  # FullProf Typ
    fract_x=0.39072,  # FullProf X
    fract_y=0.15204,  # FullProf Y
    fract_z=0.38030,  # FullProf Z
    occupancy=1.0,  # FullProf Occ 1.00000 (48e site)
    adp_type='beta',  # FullProf N_t = 2 (anisotropic β)
)

# β tensor components (FullProf Betas), dimensionless.
structure.atom_site_aniso['Y1'].adp_11 = 0.00303  # FullProf beta11
structure.atom_site_aniso['Y1'].adp_22 = 0.00272  # FullProf beta22
structure.atom_site_aniso['Y1'].adp_33 = 0.00295  # FullProf beta33
structure.atom_site_aniso['Y1'].adp_23 = -0.00025  # FullProf beta23

structure.atom_site_aniso['Y2'].adp_11 = 0.00304  # FullProf beta11
structure.atom_site_aniso['Y2'].adp_12 = -0.00013  # FullProf beta12

structure.atom_site_aniso['O1'].adp_11 = 0.00299  # FullProf beta11
structure.atom_site_aniso['O1'].adp_22 = 0.00310  # FullProf beta22
structure.atom_site_aniso['O1'].adp_33 = 0.00273  # FullProf beta33
structure.atom_site_aniso['O1'].adp_12 = -0.00007  # FullProf beta12
structure.atom_site_aniso['O1'].adp_13 = -0.00020  # FullProf beta13
structure.atom_site_aniso['O1'].adp_23 = -0.00001  # FullProf beta23

project.structures.add(structure)

# %% [markdown]
# ## Load the FullProf reference

# %%
FULLPROF_PROJECT_DIR = 'pd-neut-cwl_y2o3_beta-adp'
FULLPROF_PRF_FILE = 'y2o3.prf'
FULLPROF_SUM_FILE = 'y2o3.sum'
FULLPROF_BAC_FILE = 'y2o3.bac'
FULLPROF_LABEL = verify.fullprof_label(FULLPROF_PROJECT_DIR, FULLPROF_SUM_FILE)

FULLPROF_ZERO = -0.01625  # FullProf Zero
FULLPROF_SCALE = 1.0602  # FullProf Scale
FULLPROF_WAVELENGTH = 1.54822  # FullProf Lambda
FULLPROF_U = 0.036631  # FullProf U
FULLPROF_V = -0.068345  # FullProf V
FULLPROF_W = 0.131426  # FullProf W

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
    name='y2o3',
    sample_form='powder',
    beam_mode='constant wavelength',
    radiation_probe='neutron',
    scattering_type='bragg',
)
verify.set_reference_as_measured(experiment, x, calc_fullprof)

experiment.linked_structures.create(structure_id='y2o3', scale=FULLPROF_SCALE)

experiment.instrument.setup_wavelength = FULLPROF_WAVELENGTH
experiment.instrument.calib_twotheta_offset = FULLPROF_ZERO

experiment.peak.type = 'pseudo-voigt'
experiment.peak.broad_gauss_u = FULLPROF_U
experiment.peak.broad_gauss_v = FULLPROF_V
experiment.peak.broad_gauss_w = FULLPROF_W

# FullProf excluded the 0–12° and 137.5–180° regions (.pcr).
experiment.excluded_regions.create(id='1', start=0.0, end=12.0)
experiment.excluded_regions.create(id='2', start=137.5, end=180.0)

# Match cryspy's peak-range cutoff to the FullProf Wdt used for
# this reference (20.0 FWHM) so both engines truncate identically.
experiment.peak.cutoff_fwhm = 20.0

project.experiments.add(experiment)

# %% [markdown]
# ## edi-cryspy VS FullProf

# %%
experiment.calculator.type = 'cryspy'

project.analysis.calculate()
calc_ed_cryspy = experiment.data.intensity_calc
LABEL_ED_CRYSPY = verify.engine_label('cryspy')

project.display.pattern_comparison(
    'y2o3',
    reference=verify.restrict_to_included(experiment, calc_fullprof),
    candidate=calc_ed_cryspy,
    reference_label=FULLPROF_LABEL,
    candidate_label=LABEL_ED_CRYSPY,
)

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
    ],
)
