# %% [markdown]
# # Bayesian Analysis (MCMC) – LBCO and Si
#
# This notebook continues the powder diffraction refinement tutorial. In
# that tutorial, you built a two-phase model containing
# La₀.₅Ba₀.₅CoO₃ (LBCO) and a small Si impurity, refined the model against
# simulated time-of-flight neutron data, and saved the project.
#
# A conventional least-squares refinement gives a best-fit point and
# uncertainty estimates based on the local shape of the objective
# function. Bayesian analysis instead uses Markov chain Monte Carlo
# (MCMC) sampling to explore the joint posterior distribution of the
# free parameters. This allows us to investigate questions such as:
#
# - Which parameter values are supported by the data?
# - How broad are their credible intervals?
# - Which parameters are correlated?
# - How does parameter uncertainty propagate into the calculated
#   diffraction pattern?
#
# This notebook follows the same teaching structure as the refinement
# tutorial:
#
# - **Introduction:** a complete, guided MCMC analysis of the refined
#   LBCO+Si model.
# - **Exercise:** repeat the analysis after fixing one member of a
#   strongly correlated peak-profile pair, then compare the results.
#
# We will use the DREAM sampler provided by the `bumps (dream)`
# minimizer. The short chains used here keep the tutorial practical. A
# scientific analysis requires longer chains and careful convergence
# checks.

# %% [markdown]
# ## 🛠️ Import Libraries

# %%
import easydiffraction as edi

# %% [markdown]
# ## 📘 Introduction: MCMC Analysis of LBCO+Si
#
# We will first work through the complete Bayesian workflow without
# exercises. This reference analysis samples the same seven scientific
# parameters that remained free at the end of the refinement tutorial:
#
# - the LBCO lattice parameter,
# - the LBCO and Si scale factors, and
# - four peak-profile parameters.
#
# The resulting project will be called `project_1`, following the
# convention used for the introductory Si fit in the previous tutorial.

# %% [markdown]
# ### 📂 Load the Refined Project
#
# Rather than rebuilding the experiment and structures, download the
# project saved at the end of the refinement tutorial. This restores the
# measured data, both structures, the refined values, and the
# free-parameter settings.
#
# The following cell downloads our pre-generated refined project from
# the EasyDiffraction repository. This lets you continue even if you did
# not complete the refinement tutorial or your saved project is missing.
# The `download_data` function will not overwrite an existing project
# unless you set `overwrite=True`, so it is safe to run even if the
# project is already present.

# %% [markdown] tags=["doc-link"]
# 📖 See
# [documentation](https://docs.easydiffraction.org/lib/latest/user-guide/analysis-workflow/project/#loading-a-saved-project)
# for more details about loading a saved project.

# %%
refinement_project_dir = edi.download_data(
    'proj-fitting-exercise-si-lbco-main',
    destination='projects',
)
project_1 = edi.Project.load(refinement_project_dir)

# %% [markdown]
# Save a copy under a new name before changing the analysis. This keeps
# the deterministic refinement unchanged and gives the sampler its own
# location for posterior summaries and chain data.

# %%
project_1.metadata.title = 'Reference Bayesian Analysis of LBCO with Si Impurity'
project_1.metadata.description = (
    'Reference MCMC analysis of a two-phase LBCO and Si powder diffraction model.'
)
project_1.save_as(dir_path='projects/exercise-bayesian-si-lbco-reference')

# %% [markdown]
# Confirm that the restored project contains the LBCO and Si structures
# and the `sim_lbco` experiment.

# %%
project_1.structures.show_names()
project_1.experiments.show_names()

# %%
project_1.display.structure(struct_name='lbco')
project_1.display.structure(struct_name='si')

# %%
project_1.display.pattern(expt_name='sim_lbco')

# %% [markdown]
# ### 🎯 Choose the Sampled Parameters
#
# MCMC varies every free parameter simultaneously. Before sampling, it
# is worth asking which parameters are needed to answer the scientific
# question.
#
# First, display all free parameters in the refined project.

# %%
project_1.display.parameters.free()

# %% [markdown]
# The seven line-segment background intensities were refined in the
# previous tutorial. If we left them free, this analysis would sample 14
# parameters instead of 7. The larger space would require more model
# evaluations, take longer to explore, and generally need a longer chain
# to mix well. Background parameters can also correlate with phase
# scales and broad peaks, making the posterior harder to interpret.
#
# We therefore fix the background at its refined values. This is a
# practical simplification for a short teaching example, not a universal
# rule. Fixing the background means that its uncertainty is **not**
# propagated into the final credible intervals. In a complete scientific
# analysis, you should sample relevant background parameters or otherwise
# account for their uncertainty when it can affect the result.

# %%
experiment_1 = project_1.experiments['sim_lbco']

for line_segment in experiment_1.background:
    line_segment.intensity.free = False

# %% [markdown]
# Display the remaining free parameters to verify the sampling problem.

# %%
project_1.display.parameters.free()

# %% [markdown]
# ### 🚀 Run a Local Refinement
#
# Fixing the background changes the optimization problem slightly. We
# first run a fast local least-squares refinement to update the best-fit
# values and their uncertainty estimates. These values will provide the
# starting point and finite bounds for MCMC.
#
# We use the BUMPS Levenberg-Marquardt minimizer, `bumps (lm)`, so the
# local and Bayesian stages use the same minimizer library.

# %% [markdown] tags=["doc-link"]
# 📖 See
# [documentation](https://docs.easydiffraction.org/lib/latest/user-guide/analysis-workflow/analysis/#minimization-optimization)
# for more details about the available minimizers.

# %%
project_1.analysis.minimizer.show_supported()

# %%
project_1.analysis.minimizer.type = 'bumps (lm)'

# %%
project_1.analysis.fit()
project_1.display.fit.results()

# %% [markdown]
# ### 🔗 Understand the Local Correlation Chart
#
# The correlation chart summarizes how pairs of refined parameters can
# change together near the least-squares optimum. Each off-diagonal
# value is a correlation coefficient between -1 and +1:
#
# - a value near **+1** means that the two parameters tend to increase
#   together;
# - a value near **-1** means that one tends to decrease when the other
#   increases; and
# - a value near **0** means that there is little linear relationship.
#
# Correlation does not mean that one parameter physically causes the
# other. It means that the measured pattern cannot distinguish their
# effects independently within this model.

# %%
project_1.display.fit.correlations()

# %% [markdown]
# The matrix shows only one triangular half because the other half would
# contain the same values in reverse order. EasyDiffraction
# automatically filters the chart to keep the strongest relationships
# readable. In an interactive Jupyter display, hover over a colored cell
# to see the two full parameter names and the numerical correlation
# coefficient.
#
# The strongest relationship is typically the negative correlation
# between `broad_gauss_sigma_1` and `broad_gauss_sigma_2`, close to
# -0.94. Both parameters contribute to the d-spacing dependence of the
# Gaussian TOF peak width. An increase in one can be partly compensated
# by a decrease in the other while producing a similar calculated peak
# shape.
#
# This chart comes from the local covariance estimate, so it describes
# only the neighborhood around the best-fit point. MCMC will show whether
# the relationship remains linear and approximately elliptical across a
# wider region of parameter space.

# %% [markdown]
# ### 🎲 Define the Sampling Region
#
# DREAM requires finite lower and upper bounds for every sampled
# parameter. Here, we derive them from the uncertainty estimated by the
# local fit. `set_fit_bounds_from_uncertainty()` places each bound four
# estimated standard uncertainties from the current value by default,
# while respecting any physical parameter limits.
#
# These bounds act as bounded prior support in this example. They must be
# inspected rather than accepted blindly: narrow bounds can truncate the
# posterior, while unnecessarily wide bounds can make sampling less
# efficient.

# %% [markdown] tags=["doc-link"]
# 📖 See
# [documentation](https://docs.easydiffraction.org/lib/latest/user-guide/parameters/)
# for more details about parameter values, uncertainties, and fit bounds.

# %%
for param in project_1.free_parameters:
    param.set_fit_bounds_from_uncertainty()

# %%
project_1.display.parameters.free()

# %% [markdown]
# ### 🎲 Run DREAM Sampling
#
# In Bayesian analysis, the posterior combines the likelihood of the
# measured data with prior assumptions. MCMC constructs chains of
# correlated samples whose long-run distribution approximates that
# posterior.
#
# DREAM uses multiple chains and differential-evolution proposals to
# explore correlated parameter spaces. This makes it useful for the
# strong peak-profile correlation observed above.

# %% [markdown] tags=["doc-link"]
# 📖 See
# [documentation](https://docs.easydiffraction.org/lib/latest/user-guide/analysis-workflow/analysis/#bayesian-analysis)
# for more details about Bayesian minimizers and posterior displays.

# %%
project_1.analysis.minimizer.type = 'bumps (dream)'
project_1.analysis.minimizer.sampling_steps = 300  # lower than the default 3000
project_1.analysis.minimizer.burn_in_steps = 60  # lower than the default 600
project_1.analysis.minimizer.random_seed = 42

# %% [markdown]
# Burn-in samples allow the chains to move away from their initial
# positions before the retained posterior is summarized. The fixed seed
# makes the tutorial output reproducible.

# %%
project_1.analysis.fit()

# %% [markdown]
# ### 📋 Understand the Bayesian Fit Summary
#
# The result table now reports posterior medians and 95% credible
# intervals in addition to fit-quality metrics. A 95% credible interval
# is the interval containing 95% of the retained marginal posterior
# samples under this model and bounded sampling setup.
#
# The table also reports convergence diagnostics:
#
# - **r-hat** compares variation within and between chains. Values close
#   to 1 are desirable; EasyDiffraction uses `r-hat <= 1.01` as its
#   displayed convergence criterion.
# - **ess bulk** is the effective sample size after accounting for
#   autocorrelation. A larger value means that the chain contains more
#   independent information; the display recommends at least 400.

# %%
project_1.display.fit.results()

# %% [markdown]
# A short teaching run may fail these convergence criteria even when it
# finishes normally. That means the numerical posterior summaries are
# provisional. Increase the number of sampling steps and inspect the
# diagnostics again before drawing scientific conclusions.

# %% [markdown]
# ### 🔗 Understand Posterior Correlations
#
# Calling the same method after MCMC now builds the matrix from posterior
# samples rather than from the local least-squares covariance estimate.
# It answers: *across the sampled posterior, which parameter pairs vary
# together, and how strongly?*

# %%
project_1.display.fit.correlations()

# %% [markdown]
# Compare this chart with the local chart above. Similar coefficients
# suggest that the local approximation captured the main linear
# relationship. A substantial difference can indicate curvature,
# asymmetry, bounds, or another feature that a local covariance matrix
# cannot represent.

# %% [markdown]
# ### 🗺️ Understand the Posterior Pair Plot
#
# The pair plot shows more information than a matrix of single
# coefficients:
#
# - **Diagonal panels** show each parameter's one-dimensional marginal
#   posterior density. A narrow peak indicates greater precision; a wide,
#   skewed, truncated, or multimodal shape indicates more uncertainty or
#   a more complicated posterior.
# - **Lower-triangle panels** show joint posterior samples for pairs of
#   parameters. The contours summarize where the sampled density is
#   concentrated.
# - A compact, nearly round cloud suggests weak correlation. An elongated
#   upward cloud suggests positive correlation, and an elongated downward
#   cloud suggests negative correlation. Curved or split contours cannot
#   be summarized well by one correlation coefficient.
# - The upper triangle is intentionally blank because it would duplicate
#   the lower triangle.

# %%
project_1.display.posterior.pairs()

# %% [markdown]
# In Jupyter, the default plotting engine resolves to interactive Plotly.
# Hover over a diagonal density curve to see the full parameter name,
# parameter value, and probability density. Hover over a visible sample
# point in a lower-triangle panel to see the exact values of both
# parameters for that posterior draw. The shaded contour itself has no
# hover tooltip; it is a smoothed two-dimensional density guide. Use the
# Plotly toolbar to zoom, pan, and reset the view, and click legend items
# to hide or show samples, contours, or marginal densities.
#
# The `broad_gauss_sigma_1`–`broad_gauss_sigma_2` panel should form a
# long downward band. This reveals the range of compensating parameter
# combinations, whereas the correlation chart reduces the relationship
# to one number.

# %% [markdown]
# ### 📈 Understand Marginal Posterior Distributions
#
# A separate distribution plot gives a more detailed view of each
# diagonal panel. It includes a histogram, a smoothed marginal density,
# the median, the best posterior sample, and the 95% credible interval.
# Hover over the traces and interval markers to read their values.

# %%
project_1.display.posterior.distribution()

# %% [markdown]
# A density pressed against a fit bound warns that the allowed region may
# be too narrow or that the parameter is poorly identified. A best
# sample far from the median can occur for a skewed or irregular
# posterior and is another reason not to summarize MCMC with only one
# point estimate.

# %% [markdown]
# ### 📊 Understand the Posterior-Predictive Plot
#
# Posterior prediction propagates every retained parameter combination
# through the diffraction calculation. The best-posterior-sample curve
# shows one calculated pattern, while the 95% band shows parameter
# uncertainty propagated into the pattern.

# %%
project_1.display.posterior.predictive(expt_name='sim_lbco')

# %%
project_1.display.posterior.predictive(
    expt_name='sim_lbco',
    x_min=80000,
    x_max=81500,
)

# %% [markdown]
# Compare the width of the band with the experimental uncertainty and
# remaining residuals. A narrow band does not prove that the model is
# correct: systematic deviations can indicate model inadequacy,
# underestimated experimental uncertainty, or effects not included in
# the refinement. In the interactive view, hover over the measured and
# best-sample curves to inspect individual x and intensity values. The
# shaded 95% band is read from its upper and lower boundaries and does
# not itself show a hover tooltip.

# %% [markdown]
# Save the completed reference Bayesian project. Its MCMC chain and
# posterior data are stored with the project and remain available for
# comparison with the exercise below.

# %%
project_1.save()

# %% [markdown]
# ## 💪 Exercise: Fix One Correlated Parameter
#
# The reference analysis showed that `broad_gauss_sigma_1` and
# `broad_gauss_sigma_2` are strongly negatively correlated. In this
# exercise, you will fix `broad_gauss_sigma_2` at its refined value and
# repeat the Bayesian workflow.
#
# Removing one member of the pair reduces the sampling dimension and
# removes that pair from the correlation and pair plots. This can improve
# sampling efficiency, but it changes the scientific question: the new
# posterior is conditional on the chosen fixed value of
# `broad_gauss_sigma_2`. Its uncertainty is no longer propagated. The
# exercise demonstrates the computational and visual effect of fixing a
# parameter; it does not establish that fixing it is always the correct
# scientific choice.

# %% [markdown]
# ### 📂 Exercise 1: Create a Fresh Project
#
# Load the original deterministic refinement again as `project_2` and
# save it under a new name. Starting from the deterministic project
# ensures that the second MCMC run does not reuse the first posterior
# state or its uncertainty estimates.

# %% [markdown]
# **Hint:**

# %% [markdown] tags=["dmsc-school-hint"]
# Use `edi.Project.load()` with `refinement_project_dir`, which was
# downloaded in the introduction.

# %% [markdown]
# **Solution:**

# %% tags=["solution", "hide-input"]
project_2 = edi.Project.load(refinement_project_dir)
project_2.metadata.title = 'Bayesian Analysis with Fixed broad_gauss_sigma_2'
project_2.metadata.description = (
    'MCMC analysis of LBCO and Si with one peak-profile parameter fixed.'
)
project_2.save_as(dir_path='projects/exercise-bayesian-si-lbco-main')

# %% [markdown]
# ### 🎯 Exercise 2: Reduce the Free-Parameter Set
#
# #### Exercise 2.1: Fix the Background
#
# Fix every background intensity for the same computational reason as in
# the reference analysis.

# %% [markdown]
# **Hint:**

# %% [markdown] tags=["dmsc-school-hint"]
# Iterate over `project_2.experiments['sim_lbco'].background` and set
# each point's `intensity.free` attribute to `False`.

# %% [markdown]
# **Solution:**

# %% tags=["solution", "hide-input"]
experiment_2 = project_2.experiments['sim_lbco']

for line_segment in experiment_2.background:
    line_segment.intensity.free = False

# %% [markdown]
# #### Exercise 2.2: Fix `broad_gauss_sigma_2`
#
# Remove `broad_gauss_sigma_2` from the refined and sampled parameter
# set, then display the remaining free parameters. How many remain?

# %% [markdown]
# **Hint:**

# %% [markdown] tags=["dmsc-school-hint"]
# Set the parameter's `free` attribute to `False`, then call
# `project_2.display.parameters.free()`.

# %% [markdown]
# **Solution:**

# %% tags=["solution", "hide-input"]
experiment_2.peak.broad_gauss_sigma_2.free = False

# %% tags=["solution", "hide-input"]
project_2.display.parameters.free()

# %% [markdown] tags=["dmsc-school-hint"]
# Six parameters remain. The background intensities and
# `broad_gauss_sigma_2` will stay at their refined values throughout the
# following local fit and MCMC run.

# %% [markdown]
# ### 🚀 Exercise 3: Repeat the Local Refinement
#
# Select `bumps (lm)`, run the fit, display the result table, and inspect
# the local correlation chart. Is the original strongly correlated pair
# still present?

# %% [markdown]
# **Hint:**

# %% [markdown] tags=["dmsc-school-hint"]
# Repeat the local-refinement sequence from the introduction with
# `project_2`.

# %% [markdown]
# **Solution:**

# %% tags=["solution", "hide-input"]
project_2.analysis.minimizer.type = 'bumps (lm)'
project_2.analysis.fit()
project_2.display.fit.results()

# %% tags=["solution", "hide-input"]
project_2.display.fit.correlations()

# %% [markdown] tags=["dmsc-school-hint"]
# The `broad_gauss_sigma_1`–`broad_gauss_sigma_2` pair is absent because
# `broad_gauss_sigma_2` was not varied. This does not show that the
# physical ambiguity disappeared; it shows that the fixed parameter is
# no longer part of the estimated covariance or posterior.

# %% [markdown]
# ### 🎲 Exercise 4: Set New Sampling Bounds
#
# Derive finite bounds from the new local-fit uncertainties and verify
# them. Why must the bounds be recalculated instead of copied from
# `project_1`?

# %% [markdown]
# **Hint:**

# %% [markdown] tags=["dmsc-school-hint"]
# Iterate over `project_2.free_parameters` and call
# `set_fit_bounds_from_uncertainty()`.

# %% [markdown]
# **Solution:**

# %% tags=["solution", "hide-input"]
for param in project_2.free_parameters:
    param.set_fit_bounds_from_uncertainty()

# %% tags=["solution", "hide-input"]
project_2.display.parameters.free()

# %% [markdown] tags=["dmsc-school-hint"]
# Fixing one correlated parameter changes the local covariance matrix and
# therefore the uncertainty estimates of the remaining parameters. The
# new bounds should be based on this new local problem.

# %% [markdown]
# ### 🎲 Exercise 5: Repeat DREAM Sampling
#
# Configure DREAM with the same short-chain settings used for
# `project_1`, then sample the six-parameter posterior.

# %% [markdown]
# **Hint:**

# %% [markdown] tags=["dmsc-school-hint"]
# Use 300 sampling steps, 60 burn-in steps, and random seed 42 so the two
# runs use comparable settings.

# %% [markdown]
# **Solution:**

# %% tags=["solution", "hide-input"]
project_2.analysis.minimizer.type = 'bumps (dream)'
project_2.analysis.minimizer.sampling_steps = 300
project_2.analysis.minimizer.burn_in_steps = 60
project_2.analysis.minimizer.random_seed = 42

# %% tags=["solution", "hide-input"]
project_2.analysis.fit()

# %% [markdown]
# ### 📊 Exercise 6: Compare the Posterior Results
#
# #### Exercise 6.1: Check Convergence and Credible Intervals
#
# Display the Bayesian result table. Compare r-hat, effective sample
# size, and the credible intervals with the reference run. Did fixing one
# parameter automatically guarantee convergence?

# %% [markdown]
# **Hint:**

# %% [markdown] tags=["dmsc-school-hint"]
# Use `project_2.display.fit.results()`, then compare the diagnostics
# with those displayed for `project_1` in the introduction.

# %% [markdown]
# **Solution:**

# %% tags=["solution", "hide-input"]
project_2.display.fit.results()

# %% [markdown] tags=["dmsc-school-hint"]
# Reducing the dimension can make sampling easier, but a 300-step chain
# is still short. Convergence must be judged from the diagnostics, not
# assumed from the number of free parameters.

# %% [markdown]
# #### Exercise 6.2: Inspect Correlations and Pair Relationships
#
# Display the posterior correlation matrix and pair plot. Confirm that
# `broad_gauss_sigma_2` is absent, then inspect whether
# `broad_gauss_sigma_1` is correlated with any remaining parameter.

# %% [markdown]
# **Hint:**

# %% [markdown] tags=["dmsc-school-hint"]
# Use the same `display.fit.correlations()` and
# `display.posterior.pairs()` calls as in the introduction. Hover over
# cells and sample points to identify the parameter pairs and values.

# %% [markdown]
# **Solution:**

# %% tags=["solution", "hide-input"]
project_2.display.fit.correlations()

# %% tags=["solution", "hide-input"]
project_2.display.posterior.pairs()

# %% [markdown] tags=["dmsc-school-hint"]
# The original pair is gone because only sampled parameters appear in
# posterior charts. Look for any remaining elongated contours rather
# than concluding that all correlations have disappeared. Fixing one
# parameter can expose or strengthen relationships among the parameters
# that remain free.

# %% [markdown]
# #### Exercise 6.3: Compare `broad_gauss_sigma_1`
#
# Plot the marginal posterior for `broad_gauss_sigma_1` from both runs.
# Compare the medians, shapes, and 95% credible intervals. Why might the
# second interval be narrower?

# %% [markdown]
# **Hint:**

# %% [markdown] tags=["dmsc-school-hint"]
# Call `display.posterior.distribution()` for each project and pass the
# corresponding `broad_gauss_sigma_1` parameter using `param`.

# %% [markdown]
# **Solution:**

# %% tags=["solution", "hide-input"]
project_1.display.posterior.distribution(
    param=experiment_1.peak.broad_gauss_sigma_1,
)

# %% tags=["solution", "hide-input"]
project_2.display.posterior.distribution(
    param=experiment_2.peak.broad_gauss_sigma_1,
)

# %% [markdown] tags=["dmsc-school-hint"]
# The conditional posterior can be narrower because
# `broad_gauss_sigma_1` no longer shares uncertainty with
# `broad_gauss_sigma_2`. That apparent precision comes from assuming the
# fixed value is exact. It may underestimate the true uncertainty if
# `broad_gauss_sigma_2` is not independently known.

# %% [markdown]
# #### Exercise 6.4: Compare Posterior Predictions
#
# Plot the same zoomed posterior-predictive region for both analyses.
# Does fixing `broad_gauss_sigma_2` noticeably change the best curve or
# uncertainty band?

# %% [markdown]
# **Hint:**

# %% [markdown] tags=["dmsc-school-hint"]
# Call `display.posterior.predictive()` for both projects with the same
# experiment name and the same `x_min` and `x_max` values.

# %% [markdown]
# **Solution:**

# %% tags=["solution", "hide-input"]
project_1.display.posterior.predictive(
    expt_name='sim_lbco',
    x_min=80000,
    x_max=81500,
)

# %% tags=["solution", "hide-input"]
project_2.display.posterior.predictive(
    expt_name='sim_lbco',
    x_min=80000,
    x_max=81500,
)

# %% [markdown]
# Two parameterizations can produce similarly good calculated patterns
# while assigning different uncertainties to individual parameters.
# This is why parameter correlations, marginal posteriors, and posterior
# predictions should be interpreted together.

# %% [markdown]
# ### 💾 Exercise 7: Save the Project
#
# Save the second posterior and its MCMC chain.

# %% [markdown]
# **Hint:**

# %% [markdown] tags=["dmsc-school-hint"]
# The project directory was set in Exercise 1, so use `project_2.save()`
# to update the existing saved project.

# %% [markdown]
# **Solution:**

# %% tags=["solution", "hide-input"]
project_2.save()

# %% [markdown]
# #### Final Remarks
#
# In this part of the notebook, you learned how to:
#
# - prepare a refined EasyDiffraction project for MCMC;
# - reduce runtime by fixing nuisance parameters while recognizing the
#   uncertainty tradeoff;
# - use a local fit to obtain starting values and finite bounds;
# - sample a correlated posterior with DREAM;
# - distinguish a local covariance correlation from a posterior-sample
#   correlation;
# - read correlation matrices, pair plots, marginal distributions, and
#   posterior-predictive plots; and
# - understand how fixing one member of a correlated pair changes the
#   statistical question and the reported uncertainty.
#
# For scientific analysis, run longer chains, verify convergence,
# examine sensitivity to bounds and fixed values, and reconsider the
# diffraction model when systematic residuals remain.

# %% [markdown]
# ## 🎁 Bonus
#
# Congratulations — you've now completed the diffraction data analysis
# part of the DMSC Summer School!
#
# If you'd like to keep exploring, the EasyDiffraction library offers
# many additional tutorials and examples on the official documentation
# site: 👉 https://docs.easydiffraction.org/lib/latest/tutorials
#
# Besides the Python package, EasyDiffraction also comes with a
# graphical user interface (GUI) for deterministic diffraction
# refinement workflows. Bayesian analysis is not yet available in the
# GUI, so MCMC workflows currently require the Python library.
#
# If you prefer a point-and-click interface over coding, the GUI
# provides a user-friendly way to perform deterministic refinements. You
# can download it as a standalone application here: 👉
# https://easydiffraction.org
#
# We'd love to hear your feedback on EasyDiffraction — both the library
# and the GUI! 💬
