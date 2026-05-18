# %% [markdown]
# # Structure Refinement: Co2SiO4, D20 (T-scan, resumed)
#
# This example loads a previously saved Co2SiO4 project after a
# sequential refinement was stopped before all scan files were
# processed. If `analysis/results.csv` already contains completed rows,
# running `project.analysis.fit()` again resumes from the remaining
# datasets and appends the missing results.

# %% [markdown]
# ## Import Library

# %%
import easydiffraction as ed

# %% [markdown]
# ## Download Saved Project
#
# The returned path points directly to the saved project directory with
# a partially completed sequential fit, including
# `analysis/results.csv`.

# %%
project_dir = ed.download_data(id=34, destination='projects')

# %% [markdown]
# ## Load Saved Project

# %%
project = ed.Project.load(project_dir)

# %% [markdown]
# ## Resume Sequential Analysis
#
# This project already stores the template experiment, sequential-fit
# settings, and the partial `analysis/results.csv` from the previous
# run. Running the fit again skips datasets already present in the CSV
# and continues from the remaining files.

# %%
project.analysis.fit()

# %% [markdown]
# ## Replay Fitted Datasets
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
# ## Plot Parameter Evolution
#
# Use the same persisted diffrn path stored in `analysis/results.csv`
# for the x-axis. Omitting `param` plots every fitted parameter one
# after another.

# %%
temperature = 'diffrn.ambient_temperature'

# %%
project.display.fit.series(versus=temperature)
