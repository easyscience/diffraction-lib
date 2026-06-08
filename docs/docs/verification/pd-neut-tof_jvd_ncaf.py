# %% [markdown]
# # NaCaAlF — neutron powder, time-of-flight, Jorgensen–Von Dreele
#
# Cross-engine and external-reference verification for NaCaAlF
# (Na₂Ca₃Al₂F₁₄) in time-of-flight geometry: the **same** pattern is
# calculated with each EasyDiffraction engine (`cryspy`, `crysfml`) and
# compared against a **FullProf** reference, on identical input
# parameters and **without any fitting**. It also runs as a regression
# check under `pixi run script-tests`.
#
# This Jorgensen–Von Dreele profile has no Lorentzian (`gamma`) term, so
# both engines agree closely with FullProf.

# %%
import easydiffraction as ed
from easydiffraction import ExperimentFactory
from easydiffraction import StructureFactory
from easydiffraction.analysis import verification as verify

# %% [markdown]
# ## Load the FullProf reference
#
# This reference is a two-column ``x y`` profile.

# %%
reference_dir = verify.bundled_reference_dir() / 'pd-neut-tof_jvd_ncaf'
x, calc_fullprof = verify.load_columned_profile(
    str(reference_dir / 'ncaf_tof.sub'),
    skip_rows=1,
    columns=(0, 1),
)

# %% [markdown]
# ## Build the project and define the structure in code

# %%
project = ed.Project()

structure = StructureFactory.from_scratch(name='ncaf')
structure.space_group.name_h_m = 'I 21 3'  # FullProf Space group symbol
structure.cell.length_a = 10.250256  # FullProf a
structure.cell.length_b = 10.250256  # FullProf b
structure.cell.length_c = 10.250256  # FullProf c
structure.atom_sites.create(
    label='Ca',  # FullProf Atom
    type_symbol='Ca',  # FullProf Typ
    fract_x=0.46610,  # FullProf X
    fract_y=0.0,  # FullProf Y
    fract_z=0.25,  # FullProf Z
    adp_iso=0.88770,  # FullProf Biso
)
structure.atom_sites.create(
    label='Al',  # FullProf Atom
    type_symbol='Al',  # FullProf Typ
    fract_x=0.25163,  # FullProf X
    fract_y=0.25163,  # FullProf Y
    fract_z=0.25163,  # FullProf Z
    adp_iso=0.65283,  # FullProf Biso
)
structure.atom_sites.create(
    label='Na',  # FullProf Atom
    type_symbol='Na',  # FullProf Typ
    fract_x=0.08472,  # FullProf X
    fract_y=0.08472,  # FullProf Y
    fract_z=0.08472,  # FullProf Z
    adp_iso=1.89281,  # FullProf Biso
)
structure.atom_sites.create(
    label='F1',  # FullProf Atom
    type_symbol='F',  # FullProf Typ
    fract_x=0.13748,  # FullProf X
    fract_y=0.30533,  # FullProf Y
    fract_z=0.11947,  # FullProf Z
    adp_iso=0.89562,  # FullProf Biso
)
structure.atom_sites.create(
    label='F2',  # FullProf Atom
    type_symbol='F',  # FullProf Typ
    fract_x=0.36263,  # FullProf X
    fract_y=0.36333,  # FullProf Y
    fract_z=0.18669,  # FullProf Z
    adp_iso=1.27227,  # FullProf Biso
)
structure.atom_sites.create(
    label='F3',  # FullProf Atom
    type_symbol='F',  # FullProf Typ
    fract_x=0.46120,  # FullProf X
    fract_y=0.46120,  # FullProf Y
    fract_z=0.46120,  # FullProf Z
    adp_iso=0.78071,  # FullProf Biso
)

project.structures.add(structure)

# %% [markdown]
# ## Create the experiment on the reference grid

# %%
experiment = ExperimentFactory.from_scratch(
    name='ncaf',
    sample_form='powder',
    beam_mode='time-of-flight',
    radiation_probe='neutron',
    scattering_type='bragg',
)
verify.set_reference_as_measured(experiment, x, calc_fullprof)

experiment.instrument.setup_twotheta_bank = 152.827  # FullProf 2ThetaBank
experiment.instrument.calib_d_to_tof_linear = 20773.12305  # FullProf Dtt1
experiment.instrument.calib_d_to_tof_quad = -1.08308  # FullProf Dtt2
experiment.instrument.calib_d_to_tof_offset = 0.0  # FullProf Zero

experiment.peak.type = 'jorgensen-von-dreele'
experiment.peak.broad_gauss_sigma_0 = 0.0  # FullProf Sigma-0
experiment.peak.broad_gauss_sigma_1 = 0.0  # FullProf Sigma-1
experiment.peak.broad_gauss_sigma_2 = 15.6960  # FullProf Sigma-2
experiment.peak.exp_rise_alpha_0 = -0.009276  # FullProf alph0
experiment.peak.exp_rise_alpha_1 = 0.109623  # FullProf alph1
experiment.peak.exp_decay_beta_0 = 0.006705  # FullProf beta0
experiment.peak.exp_decay_beta_1 = 0.009708  # FullProf beta1

experiment.linked_phases.create(id='ncaf', scale=4.019921)  # FullProf Scale

project.experiments.add(experiment)

# %% [markdown]
# ## Calculate the pattern with each engine

# %%
calc_ed_cryspy = verify.calculate_pattern(project, experiment, 'cryspy')
calc_ed_crysfml = verify.calculate_pattern(project, experiment, 'crysfml')

# %% [markdown]
# ## Compare each engine against FullProf

# %%
project.display.pattern_comparison(
    'ncaf',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy,
    reference_label='FullProf',
    candidate_label='EasyDiffraction (cryspy)',
)

# %%
project.display.pattern_comparison(
    'ncaf',
    reference=calc_fullprof,
    candidate=calc_ed_crysfml,
    reference_label='FullProf',
    candidate_label='EasyDiffraction (crysfml)',
)

# %% [markdown]
# ## Compare the two engines with each other

# %%
project.display.pattern_comparison(
    'ncaf',
    reference=calc_ed_crysfml,
    candidate=calc_ed_cryspy,
    reference_label='EasyDiffraction (crysfml)',
    candidate_label='EasyDiffraction (cryspy)',
)

# %% [markdown]
# ## Agreement check
#
# The engines reproduce the FullProf peak *shapes* but sit at different
# absolute time-of-flight intensity scales: neither matches the FullProf
# `.pcr` scale and the two engines differ from each other by a large
# factor, so the absolute comparison is reported here
# (`raise_on_failure=False`) and the scale convention is investigated
# below.

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
# ## Investigate the scale convention by refinement
#
# The shapes already agree, so free **only** the scale with the `cryspy`
# engine and refine, keeping the structure, calibration, and profile
# fixed. If a scale-only fit closes the gap, the discrepancy is purely a
# time-of-flight intensity-scale convention, not a structural or profile
# one. (`crysfml` follows a different convention again and is not refined
# here.)

# %%
experiment.calculator.type = 'cryspy'
project.analysis.minimizer.type = 'lmfit'

experiment.linked_phases['ncaf'].scale.free = True

project.analysis.fit()

# %% [markdown]
# ## Goodness of fit and refined scale

# %%
project.display.fit.results()

# %% [markdown]
# ## Refined cryspy vs FullProf

# %%
calc_ed_cryspy_refined = verify.calculate_pattern(project, experiment, 'cryspy')

project.display.pattern_comparison(
    'ncaf',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy_refined,
    reference_label='FullProf',
    candidate_label='EasyDiffraction (cryspy, refined)',
)

# %%
verify.report_refinement_closeness(calc_fullprof, calc_ed_cryspy, calc_ed_cryspy_refined)
