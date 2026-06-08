# %% [markdown]
# # LBCO — neutron powder, constant wavelength, pseudo-Voigt
#
# This page calculates the **same** La₀.₅Ba₀.₅CoO₃ diffraction pattern
# with each EasyDiffraction engine (`cryspy`, `crysfml`) and compares
# both against a **FullProf** reference profile — all on identical input
# parameters and **without any fitting**. It doubles as a regression
# check run by `pixi run script-tests`.
#
# The structure is defined directly in code; the experiment grid and the
# FullProf reference come from the project's reference profile.

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
reference_dir = verify.bundled_reference_dir() / 'pd-neut-cwl_pv_lbco'
x, calc_fullprof = verify.load_columned_profile(
    str(reference_dir / 'lbco1.sub'),
    skip_rows=1,
    columns=(0, 1),
)

# %% [markdown]
# ## Build the project

# %%
project = ed.Project()

# %% [markdown]
# ## Define the structure
#
# La₀.₅Ba₀.₅CoO₃ is a cubic perovskite (`P m -3 m`). La and Ba share the
# A site at the origin (½ each); the oxygen site is refined slightly
# oxygen-deficient. Atomic displacements are isotropic (B).

# %%
structure = StructureFactory.from_scratch(name='lbco')

structure.space_group.name_h_m = 'P m -3 m'  # FullProf Space group symbol

structure.cell.length_a = 3.890790  # FullProf a

structure.atom_sites.create(
    label='La',  # FullProf Atom
    type_symbol='La',  # FullProf Typ
    fract_x=0.0,  # FullProf X
    fract_y=0.0,  # FullProf Y
    fract_z=0.0,  # FullProf Z
    occupancy=0.5,  # FullProf Occ
    adp_type='Biso',  # FullProf Biso
    adp_iso=0.57499,  # FullProf Biso
)
structure.atom_sites.create(
    label='Ba',  # FullProf Atom
    type_symbol='Ba',  # FullProf Typ
    fract_x=0.0,  # FullProf X
    fract_y=0.0,  # FullProf Y
    fract_z=0.0,  # FullProf Z
    occupancy=0.5,  # FullProf Occ
    adp_type='Biso',  # FullProf Biso
    adp_iso=0.57499,  # FullProf Biso
)
structure.atom_sites.create(
    label='Co',  # FullProf Atom
    type_symbol='Co',  # FullProf Typ
    fract_x=0.5,  # FullProf X
    fract_y=0.5,  # FullProf Y
    fract_z=0.5,  # FullProf Z
    occupancy=1.0,  # FullProf Occ
    adp_type='Biso',  # FullProf Biso
    adp_iso=0.26014,  # FullProf Biso
)
structure.atom_sites.create(
    label='O',  # FullProf Atom
    type_symbol='O',  # FullProf Typ
    fract_x=0.0,  # FullProf X
    fract_y=0.5,  # FullProf Y
    fract_z=0.5,  # FullProf Z
    occupancy=0.97856,  # FullProf Occ
    adp_type='Biso',  # FullProf Biso
    adp_iso=1.36658,  # FullProf Biso
)

project.structures.add(structure)

# %% [markdown]
# ## Create the experiment

# %%
experiment = ExperimentFactory.from_scratch(
    name='lbco',
    sample_form='powder',
    beam_mode='constant wavelength',
    radiation_probe='neutron',
    scattering_type='bragg',
)
verify.set_reference_as_measured(experiment, x, calc_fullprof)

experiment.linked_phases.create(id='lbco', scale=9.405646)  # FullProf Scale

experiment.instrument.setup_wavelength = 1.494000  # FullProf Lambda

experiment.peak.type = 'pseudo-voigt'
experiment.peak.broad_gauss_u = 0.081547  # FullProf U
experiment.peak.broad_gauss_v = -0.115345  # FullProf V
experiment.peak.broad_gauss_w = 0.121119  # FullProf W
experiment.peak.broad_lorentz_x = 0.0  # FullProf X
experiment.peak.broad_lorentz_y = 0.083044  # FullProf Y

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
    'lbco',
    reference=calc_fullprof,
    candidate=calc_ed_cryspy,
    reference_label='FullProf',
    candidate_label='EasyDiffraction (cryspy)',
)

# %%
project.display.pattern_comparison(
    'lbco',
    reference=calc_fullprof,
    candidate=calc_ed_crysfml,
    reference_label='FullProf',
    candidate_label='EasyDiffraction (crysfml)',
)

# %% [markdown]
# ## Compare the two engines with each other

# %%
project.display.pattern_comparison(
    'lbco',
    reference=calc_ed_crysfml,
    candidate=calc_ed_cryspy,
    reference_label='EasyDiffraction (crysfml)',
    candidate_label='EasyDiffraction (cryspy)',
)

# %% [markdown]
# ## Agreement check
#
# A single table scores every pair against documented tolerances, with a
# check/cross per metric; an out-of-tolerance value is shown in red and
# raises, so the page fails as a regression check.

# %%
verify.assert_patterns_agree([
    ('cryspy vs FullProf', calc_fullprof, calc_ed_cryspy),
    ('crysfml vs FullProf', calc_fullprof, calc_ed_crysfml),
    ('cryspy vs crysfml', calc_ed_cryspy, calc_ed_crysfml),
])
