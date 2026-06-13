# %% [markdown]
# # Structure Refinement: Co2SiO4, D20 (T-scan, resumed)
#
# This example loads a previously saved Co2SiO4 project after a
# sequential refinement was stopped before all scan files were
# processed. If `analysis/results.csv` already contains completed rows,
# running `project.analysis.fit()` again resumes from the remaining
# datasets and appends the missing results.

# %% [markdown]
# ## 🛠️ Import Library

# %%
import os
import pathlib
import shutil

import easydiffraction as ed

# %% [markdown]
# ## 📂 Load Project

# %% [markdown]
# ### Locate Project
#
# Temporary: load a new-format Co2SiO4 scan project bundled with the
# documentation (with `analysis/results.csv`). This will switch back to
# `ed.download_data(id=37, ...)` once the updated project archives are
# published to the EasyDiffraction data repository.

# %%
bundled_project = 'docs/docs/tutorials/projects/ed-23'
artifact_root = pathlib.Path(os.environ.get('EASYDIFFRACTION_ARTIFACT_ROOT', '.'))
project_dir = artifact_root / 'projects' / 'ed_23_cosio_d20_scan_input'
shutil.rmtree(project_dir, ignore_errors=True)
shutil.copytree(bundled_project, project_dir)

# %% [markdown]
# ### Load Project
#
# The bundled project is copied to a writable working directory first so
# resuming the sequential fit (which appends to `analysis/results.csv`)
# writes there, leaving the bundled read-only copy untouched.

# %%
project = ed.Project.load(str(project_dir))

# %% [markdown]
# ## 🚀 Perform Analysis

# %% [markdown]
# ### Display Structure
#
# Render the Co2SiO4 structure restored from the saved project.

# %%
project.display.structure(struct_name='cosio')

# %% [markdown]
# ### Resume Sequential Analysis
#
# This project already stores the template experiment, sequential-fit
# settings, and the partial `analysis/results.csv` from the previous
# run. Running the fit again skips datasets already present in the CSV
# and continues from the remaining files.

# %%
project.analysis.fit()

# %% [markdown]
# ### Replay Fitted Datasets
#
# Apply fitted parameters from the first CSV row and plot the result.

# %%
project.apply_params_from_csv(row_index=0)
project.display.pattern(expt_name='d20')

# %% [markdown]
#
# Apply fitted parameters from the last CSV row and plot the result.

# %%
project.apply_params_from_csv(row_index=-1)
project.display.pattern(expt_name='d20')

# %% [markdown]
# ### Display Parameter Evolution
#
# Use the same persisted diffrn path stored in `analysis/results.csv`
# for the x-axis.

# %%
temperature = 'diffrn.ambient_temperature'

# %% [markdown]
# Plot fit quality metrics vs. temperature.

# %%
project.display.fit.series(
    project.analysis.fit_result.success,
    versus=temperature,
)
project.display.fit.series(
    project.analysis.fit_result.reduced_chi_square,
    versus=temperature,
)
project.display.fit.series(
    project.analysis.fit_result.iterations,
    versus=temperature,
)

# %% [markdown]
# Omitting `param` plots every fitted parameter one after another.

# %%
project.display.fit.series(versus=temperature)

# %% [markdown]
# ## 💾 Save Project

# %%
project.save_as(dir_path='projects/ed_23_cosio_d20_scan')
