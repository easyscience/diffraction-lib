# %% [markdown]
# # PbSO₄ — neutron powder, constant wavelength, pseudo-Voigt with empirical asymmetry
#
# This page calculates the **same** PbSO₄ diffraction pattern with each
# EasyDiffraction engine (`cryspy`, `crysfml`) and compares both against a
# **FullProf** reference profile — all on identical input parameters and
# **without any fitting**.
#
# The peak shape here is a **pseudo-Voigt with empirical (FullProf-style)
# axial-divergence asymmetry**; a companion page repeats the comparison
# with a plain pseudo-Voigt. Both engines agree with each other but
# differ from FullProf on the empirical asymmetry, so that difference is
# investigated by refinement below.

# %%
import easydiffraction as ed
from easydiffraction import ExperimentFactory
from easydiffraction import StructureFactory
from easydiffraction.analysis import verification as verify

# %% [markdown]
# ## Load the FullProf reference
#
# The reference profile provides both the x-grid the engines calculate on
# and the reference curve `calc_fullprof`.

# %%
reference_dir = verify.bundled_reference_dir() / 'pd-neut-cwl_pv-asym_empir_pbso4'
x, calc_fullprof = verify.load_fullprof_profile(str(reference_dir / 'pbso41.sub'))

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
structure.cell.length_b = 5.397254  # FullProf b
structure.cell.length_c = 6.958971  # FullProf c

structure.atom_sites.create(
    label='Pb',  # FullProf Atom
    type_symbol='Pb',  # FullProf Typ
    fract_x=0.18752,  # FullProf X
    fract_y=0.25,  # FullProf Y
    fract_z=0.16705,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=1.38991,  # FullProf Biso
)
structure.atom_sites.create(
    label='S',  # FullProf Atom
    type_symbol='S',  # FullProf Typ
    fract_x=0.06549,  # FullProf X
    fract_y=0.25,  # FullProf Y
    fract_z=0.68374,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=0.39275,  # FullProf Biso
)
structure.atom_sites.create(
    label='O1',  # FullProf Atom
    type_symbol='O',  # FullProf Typ
    fract_x=0.90816,  # FullProf X
    fract_y=0.25,  # FullProf Y
    fract_z=0.59544,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=1.99239,  # FullProf Biso
)
structure.atom_sites.create(
    label='O2',  # FullProf Atom
    type_symbol='O',  # FullProf Typ
    fract_x=0.19355,  # FullProf X
    fract_y=0.25,  # FullProf Y
    fract_z=0.54330,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=1.47741,  # FullProf Biso
)
structure.atom_sites.create(
    label='O3',  # FullProf Atom
    type_symbol='O',  # FullProf Typ
    fract_x=0.08109,  # FullProf X
    fract_y=0.02727,  # FullProf Y
    fract_z=0.80869,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=1.30069,  # FullProf Biso
)

project.structures.add(structure)

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

experiment.linked_phases.create(id='pbso4', scale=1.463902)  # FullProf Scale

experiment.instrument.setup_wavelength = 1.912  # FullProf Lambda

experiment.peak.type = 'pseudo-voigt + empirical asymmetry'
experiment.peak.broad_gauss_u = 0.153291  # FullProf U
experiment.peak.broad_gauss_v = -0.453033  # FullProf V
experiment.peak.broad_gauss_w = 0.419309  # FullProf W
experiment.peak.broad_lorentz_x = 0.0  # FullProf X
experiment.peak.broad_lorentz_y = 0.086844  # FullProf Y
experiment.peak.asym_empir_1 = 0.29584  # FullProf Asy1
experiment.peak.asym_empir_2 = 0.02295  # FullProf Asy2
experiment.peak.asym_empir_3 = -0.11217  # FullProf Asy3
experiment.peak.asym_empir_4 = 0.04856  # FullProf Asy4

project.experiments.add(experiment)

# %% [markdown]
# ## Calculate the pattern with each engine

# %%
calc_ed_cryspy = verify.calculate_pattern(project, experiment, 'cryspy')
calc_ed_crysfml = verify.calculate_pattern(project, experiment, 'crysfml')

# %% [markdown]
# ## Compare each engine against FullProf
#
# The FullProf reference is drawn as a solid blue line and the engine as
# a red dashed line, with the residual below and closeness metrics in the
# top-left corner.

# %%
project.display.pattern_comparison(
    'pbso4',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy,
    reference_label='FullProf',
    candidate_label='EasyDiffraction (cryspy)',
)

# %%
project.display.pattern_comparison(
    'pbso4',
    reference=calc_fullprof,
    candidate=calc_ed_crysfml,
    reference_label='FullProf',
    candidate_label='EasyDiffraction (crysfml)',
)

# %% [markdown]
# ## Compare the two engines with each other

# %%
project.display.pattern_comparison(
    'pbso4',
    reference=calc_ed_crysfml,
    candidate=calc_ed_cryspy,
    reference_label='EasyDiffraction (crysfml)',
    candidate_label='EasyDiffraction (cryspy)',
)

# %% [markdown]
# ## Agreement check
#
# A single table scores every pair against documented tolerances, with a
# check/cross per metric; an out-of-tolerance value is shown in red. The
# two engines agree closely with each other but both differ from FullProf
# on the empirical asymmetry, so the check only reports here
# (`raise_on_failure=False`) and the difference is investigated below.

# %%
verify.assert_patterns_agree(
    [
        ('cryspy vs FullProf', calc_fullprof, calc_ed_cryspy),
        ('crysfml vs FullProf', calc_fullprof, calc_ed_crysfml),
        ('cryspy vs crysfml', calc_ed_cryspy, calc_ed_crysfml),
    ],
    raise_on_failure=False,
)

# %% [markdown]
# ## Investigate the discrepancy by refinement
#
# The two engines agree with each other but differ from FullProf only on
# the **empirical axial-divergence asymmetry** — a peak-*profile*
# parameter whose definition differs between codes, not a structural one.
# Because the FullProf profile is already loaded as the measured data, we
# can test that reading directly: refine **only** the four `asym_empir_*`
# terms with the `cryspy` engine, keeping the structure and every other
# parameter fixed, and check whether `cryspy` can reproduce the FullProf
# curve — and how far the asymmetry terms have to move to do it.

# %%
experiment.calculator.type = 'cryspy'
project.analysis.minimizer.type = 'lmfit'

# Free only the disputed asymmetry terms; the structure stays fixed, so a
# good fit confirms the difference is a profile-parameter convention, not
# a structural disagreement.
experiment.peak.asym_empir_1.free = True
experiment.peak.asym_empir_2.free = True
experiment.peak.asym_empir_3.free = True
experiment.peak.asym_empir_4.free = True

# %%
project.analysis.fit()

# %% [markdown]
# ## Goodness of fit and refined parameters
#
# The reference is a calculation-only profile with unit uncertainties, so
# the absolute reduced χ² and R-factors are not normalised goodness-of-fit
# values; the **scale-independent before/after closeness table** below is
# the meaningful measure of the improvement. What matters here is the
# refined asymmetry values and that the structure was never touched.

# %%
project.display.fit.results()

# %% [markdown]
# ## Refined cryspy vs FullProf
#
# The refined `cryspy` pattern overlaid on the FullProf reference, then a
# before/after table of the closeness metrics.

# %%
calc_ed_cryspy_refined = verify.calculate_pattern(project, experiment, 'cryspy')

project.display.pattern_comparison(
    'pbso4',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy_refined,
    reference_label='FullProf',
    candidate_label='EasyDiffraction (cryspy, refined)',
)

# %%
verify.report_refinement_closeness(calc_fullprof, calc_ed_cryspy, calc_ed_cryspy_refined)
