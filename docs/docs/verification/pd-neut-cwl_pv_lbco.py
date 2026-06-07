# %% [markdown]
# # LBCO — neutron powder, constant wavelength, pseudo-Voigt
#
# This page calculates the **same** La₀.₅Ba₀.₅CoO₃ diffraction pattern
# (HRPT) with each supported EasyDiffraction engine and compares them,
# **without any fitting**. There is no external reference here, so the
# two engines are compared against each other. It also runs as a
# regression check under `pixi run script-tests`.

# %%
import easydiffraction as ed
from easydiffraction.analysis import verification as verify

# %% [markdown]
# ## Build the project (La₀.₅Ba₀.₅CoO₃, HRPT)

# %%
project = ed.Project()
project.structures.add_from_cif_path(ed.download_data(id=1, destination='data'))
project.experiments.add_from_cif_path(ed.download_data(id=2, destination='data'))

experiment = project.experiments['hrpt']

# %% [markdown]
# ## Calculate the pattern with each engine

# %%
calc_ed_cryspy = verify.calculate_pattern(project, experiment, 'cryspy')
calc_ed_crysfml = verify.calculate_pattern(project, experiment, 'crysfml')

# %% [markdown]
# ## Compare the engines
#
# `crysfml` is drawn as a solid blue line and `cryspy` as red markers,
# with the residual below and closeness metrics in the top-left corner.

# %%
project.display.pattern_comparison(
    'hrpt',
    reference=calc_ed_crysfml,
    candidate=calc_ed_cryspy,
    reference_label='EasyDiffraction (crysfml)',
    candidate_label='EasyDiffraction (cryspy)',
)

# %% [markdown]
# ## Agreement check

# %%
verify.assert_patterns_agree([
    ('cryspy vs crysfml', calc_ed_crysfml, calc_ed_cryspy),
])

# %%
