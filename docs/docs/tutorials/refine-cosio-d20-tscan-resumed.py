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
import easydiffraction as ed

# %% [markdown]
# ## 📂 Load Project

# %% [markdown]
# ### Locate Project
#
# Download and extract the saved Co2SiO4 scan project from the
# EasyDiffraction data repository.

# %%
project_dir = ed.download_data('proj-cosio-d20-scan', destination='projects', overwrite=True)

# %% [markdown]
# ### Load Project
#
# The project is downloaded into a fresh writable working directory so
# resuming the sequential fit appends to its `analysis/results.csv`.

# %%
project = ed.Project.load(project_dir)

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
