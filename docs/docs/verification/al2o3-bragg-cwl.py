# %% [markdown]
# # Al₂O₃ — neutron powder, constant wavelength (Bragg)
#
# Cross-engine and external-reference verification for corundum (α-Al₂O₃):
# the **same** pattern is calculated with each EasyDiffraction engine
# (`cryspy`, `crysfml`) and compared against a **FullProf** reference, on
# identical input parameters and **without any fitting**. It also runs as
# a regression check under `pixi run script-tests`.

# %%
import easydiffraction as ed
from easydiffraction import ExperimentFactory
from easydiffraction import StructureFactory
from easydiffraction.analysis import verification as verify

# %% [markdown]
# ## Load the FullProf reference
#
# The reference profile provides the x-grid the engines calculate on and
# the reference curve `calc_fullprof`.

# %%
reference_dir = verify.bundled_reference_dir()
x, calc_fullprof = verify.load_fullprof_profile(str(reference_dir / 'al2o3_uvwx_no-assym.sim'))

# %% [markdown]
# ## Build the project and define the structure in code

# %%
project = ed.Project()

structure = StructureFactory.from_scratch(name='al2o3')
structure.space_group.name_h_m = 'R -3 c'
structure.cell.length_a = 4.754000
structure.cell.length_b = 4.754000
structure.cell.length_c = 12.990000
structure.cell.angle_gamma = 120.0
structure.atom_sites.create(
    label='Al', type_symbol='Al', fract_x=0.0, fract_y=0.0, fract_z=0.35228, adp_iso=0.40
)
structure.atom_sites.create(
    label='O', type_symbol='O', fract_x=0.30640, fract_y=0.0, fract_z=0.25, adp_iso=0.60
)

project.structures.add(structure)

# %% [markdown]
# ## Create the experiment on the reference grid

# %%
experiment = ExperimentFactory.from_scratch(
    name='al2o3',
    sample_form='powder',
    beam_mode='constant wavelength',
    radiation_probe='neutron',
    scattering_type='bragg',
)
verify.set_reference_as_measured(experiment, x, calc_fullprof)

experiment.instrument.setup_wavelength = 1.540560
experiment.peak.broad_gauss_u = 0.004133
experiment.peak.broad_gauss_v = -0.007618
experiment.peak.broad_gauss_w = 0.006255
experiment.peak.broad_lorentz_x = 0.018961
experiment.peak.broad_lorentz_y = 0.0
experiment.linked_phases.create(id='al2o3', scale=1.0)

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
    'al2o3',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy,
    reference_label='FullProf',
    candidate_label='EasyDiffraction (cryspy)',
)

# %%
project.display.pattern_comparison(
    'al2o3',
    reference=calc_fullprof,
    candidate=calc_ed_crysfml,
    reference_label='FullProf',
    candidate_label='EasyDiffraction (crysfml)',
)

# %% [markdown]
# ## Compare the two engines with each other

# %%
project.display.pattern_comparison(
    'al2o3',
    reference=calc_ed_crysfml,
    candidate=calc_ed_cryspy,
    reference_label='EasyDiffraction (crysfml)',
    candidate_label='EasyDiffraction (cryspy)',
)

# %% [markdown]
# ## Agreement check

# %%
verify.assert_patterns_agree([
    ('cryspy vs FullProf', calc_fullprof, calc_ed_cryspy),
    ('crysfml vs FullProf', calc_fullprof, calc_ed_crysfml),
    ('cryspy vs crysfml', calc_ed_cryspy, calc_ed_crysfml),
])

# %%
