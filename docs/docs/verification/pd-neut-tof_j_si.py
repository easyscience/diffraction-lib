# %% [markdown]
# # Si — neutron powder, time-of-flight, Jorgensen
#
# Cross-engine and external-reference verification for silicon in
# time-of-flight geometry with the plain **Jorgensen** peak profile
# (back-to-back exponentials ⊗ Gaussian, **no Lorentzian term**). The
# **same** pattern is calculated with each EasyDiffraction engine
# (`cryspy`, `crysfml`) and compared against a **FullProf** reference, on
# identical input parameters and **without any fitting**.
#
# This is the companion of the Jorgensen–Von Dreele Si page. Both engines
# diverge from the FullProf plain-Jorgensen profile (they agree more
# closely with each other than with FullProf) and also sit at a different
# absolute time-of-flight intensity scale, so the profile terms and the
# scale are investigated together by refinement below.

# %%
import easydiffraction as ed
from easydiffraction import ExperimentFactory
from easydiffraction import StructureFactory
from easydiffraction.analysis import verification as verify

# %% [markdown]
# ## Load the FullProf reference

# %%
reference_dir = verify.bundled_reference_dir() / 'pd-neut-tof_j_si'
x, calc_fullprof = verify.load_fullprof_profile(str(reference_dir / 'arg_si1.sub'))

# %% [markdown]
# ## Build the project and define the structure in code

# %%
project = ed.Project()

structure = StructureFactory.from_scratch(name='si')

structure.space_group.name_h_m = 'F d -3 m'  # FullProf Space group symbol
structure.space_group.it_coordinate_system_code = '2'

structure.cell.length_a = 5.432381  # FullProf a

structure.atom_sites.create(
    label='Si',  # FullProf Atom
    type_symbol='Si',  # FullProf Typ
    fract_x=0.125,  # FullProf X
    fract_y=0.125,  # FullProf Y
    fract_z=0.125,  # FullProf Z
    adp_type='Biso',  # FullProf Biso
    adp_iso=0.54095,  # FullProf Biso
)

project.structures.add(structure)

# %% [markdown]
# ## Create the experiment on the reference grid

# %%
experiment = ExperimentFactory.from_scratch(
    name='si',
    sample_form='powder',
    beam_mode='time-of-flight',
    radiation_probe='neutron',
    scattering_type='bragg',
)
verify.set_reference_as_measured(experiment, x, calc_fullprof)

experiment.linked_phases.create(id='si', scale=0.6562111)  # FullProf Scale

experiment.instrument.setup_twotheta_bank = 144.845  # FullProf 2ThetaBank
experiment.instrument.calib_d_to_tof_linear = 7476.91016  # FullProf Dtt1
experiment.instrument.calib_d_to_tof_quad = -1.54  # FullProf Dtt2

experiment.peak.type = 'jorgensen'
experiment.peak.broad_gauss_sigma_0 = 5.0790  # FullProf Sigma-0
experiment.peak.broad_gauss_sigma_1 = 29.6492  # FullProf Sigma-1
experiment.peak.broad_gauss_sigma_2 = 0.0 # FullProf Sigma-2
experiment.peak.exp_rise_alpha_0 = 0.0  # FullProf alph0
experiment.peak.exp_rise_alpha_1 = 0.235422  # FullProf alph1
experiment.peak.exp_decay_beta_0 = 0.038020  # FullProf beta0
experiment.peak.exp_decay_beta_1 = 0.010902  # FullProf beta1

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
    'si',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy,
    reference_label='FullProf',
    candidate_label='EasyDiffraction (cryspy)',
)

# %%
project.display.pattern_comparison(
    'si',
    reference=calc_fullprof,
    candidate=calc_ed_crysfml,
    reference_label='FullProf',
    candidate_label='EasyDiffraction (crysfml)',
)

# %% [markdown]
# ## Compare the two engines with each other

# %%
project.display.pattern_comparison(
    'si',
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
# ## Investigate the discrepancy by refinement
#
# The divergence is in the scale, not the structure. So, it is freed ...

# %%
# Adjust the initial guess to be closer to the reference, to speed up the fit
experiment.linked_phases['ncaf'].scale = 15.0

# %%
experiment.calculator.type = 'cryspy'
project.analysis.minimizer.type = 'lmfit'

experiment.linked_phases['si'].scale.free = True

# %%
project.analysis.fit()

# %% [markdown]
# ## Goodness of fit and refined parameters

# %%
project.display.fit.results()

# %% [markdown]
# ## Refined cryspy vs FullProf

# %%
calc_ed_cryspy_refined = verify.calculate_pattern(project, experiment, 'cryspy')

project.display.pattern_comparison(
    'si',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy_refined,
    reference_label='FullProf',
    candidate_label='EasyDiffraction (cryspy, refined)',
)

# %%
verify.report_refinement_closeness(calc_fullprof, calc_ed_cryspy, calc_ed_cryspy_refined)
