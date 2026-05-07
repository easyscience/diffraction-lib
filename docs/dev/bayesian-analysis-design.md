# Bayesian Analysis Design

**Status:** Draft
**Date:** 2026-05-07

## Goal

Add Bayesian analysis to the existing fitting workflow with the smallest
user-facing API change possible, reusing the current `Analysis`,
`Fit`, `Fitter`, minimizer factory, result reporting, and plotting
surfaces.

The primary first target is BUMPS DREAM sampling for diffraction
refinement with parameter bounds taken from each parameter's
`fit_min` and `fit_max` attributes.

## User-Facing API

The intended workflow stays aligned with the current fitting API:

```python
project.analysis.fit.minimizer_type = 'bumps (lm)'
project.analysis.fit()

project.analysis.fit.minimizer_type = 'bumps (dream)'
project.analysis.fit()

project.analysis.display.fit_results()
project.display.plotter.plot_meas_vs_calc(expt_name='hrpt')
project.display.plotter.plot_param_correlations()
```

Additional Bayesian-only plotting methods should be added rather than
overloading every existing method with different semantics:

```python
project.display.plotter.plot_posterior_pairs()
project.display.plotter.plot_param_distribution(param)
```

For the first implementation, these Bayesian plotting methods may use
ArviZ with the Plotly backend internally.

### Explicit Two-Step Workflow

`'bumps (dream)'` should **not** implicitly run a deterministic
Levenberg-Marquardt pre-fit. Users should call `'bumps (lm)'` first when
they want a better starting point.

Reasons:

- It keeps `fit()` behavior explicit and predictable.
- It avoids hidden extra runtime.
- It keeps deterministic fit failures separate from sampling failures.
- It matches the current minimizer-selection model.

## Core Architectural Decision

### Keep Full Results in `analysis.fit_results`

Bayesian results should be stored in a new runtime result object,
**not** in a new heavy `Analysis` category.

Recommended model:

- `FitResults` remains the base deterministic result container.
- `BayesianFitResults` extends `FitResults` for posterior-specific data.
- `analysis.fit_results` stores either `FitResults` or
  `BayesianFitResults`.

This keeps the existing public access pattern unchanged:

```python
project.analysis.fit_results
```

### Why Not a New Results Category Under `Analysis`

Current `Analysis` categories are lightweight, structured,
project-owned configuration or control objects:

- `fit`
- `aliases`
- `constraints`
- `joint_fit_experiments`

These are serialized with the project. Full Bayesian results are a poor
fit for this category model because they are:

- runtime products rather than project configuration
- potentially large arrays
- not natural CIF content
- often disposable or recomputable

Posterior chains, posterior predictive draws, and pair-plot input data
should therefore remain runtime-only objects attached to
`BayesianFitResults`.

## Optional Future Category

A **small** `Analysis` category may still be useful later, but only for
Bayesian configuration, not for heavy result storage.

Possible future category name:

- `analysis.sampling`
- or `analysis.bayesian`

Possible responsibilities:

- sampler type
- point estimate policy
- default HDI levels
- exposed DREAM hyperparameters if they become public later

This category should stay lightweight and serializable. It should not
store raw chains.

## Proposed New Runtime Types

### `BumpsDreamMinimizer`

Add a new minimizer implementation registered through
`MinimizerFactory` with tag:

```python
'bumps (dream)'
```

Responsibilities:

- build bounded BUMPS parameters from EasyDiffraction parameters
- require finite `fit_min` and `fit_max` for every sampled parameter
- run DREAM with internal default settings
- collect posterior samples and sampler state
- compute posterior summaries
- set project parameters to the chosen point estimate after sampling

### `BayesianFitResults`

Subclass `FitResults` and add Bayesian-specific fields.

Recommended fields:

- `sampler_name`
- `point_estimate_name`
- `posterior_samples`
- `posterior_parameter_summaries`
- `posterior_predictive`
- `credible_interval_levels`
- `engine_result`

### Supporting Value Objects

Recommended helper containers:

- `PosteriorSamples`
- `PosteriorParameterSummary`
- `PosteriorPredictiveSummary`

These keep `BayesianFitResults` structured and reduce pressure to hide
plotting-specific arrays inside experiment data categories.

## Point Estimate Policy

After a DREAM run, project parameters should be updated to the **MAP**
or best posterior sample, not to independent marginal medians.

Reason:

- per-parameter medians can produce a parameter vector that was never
  sampled jointly
- MAP corresponds to a coherent sampled state
- the calculated profile shown after Bayesian fitting should correspond
  to one actual parameter set

Posterior tables can still report median, standard deviation, and HDIs.

## Parameter Bounds

DREAM should require finite bounds for every sampled free parameter.

Behavior:

- use `fit_min` and `fit_max`
- if any sampled parameter is unbounded, stop with a clear error
- the error should list the offending parameter names

This is stricter than some deterministic minimizers, but appropriate for
bounded posterior sampling.

## Hidden DREAM Defaults

For the first implementation, sampling parameters should stay internal
and use library defaults.

Examples:

- `n_steps`
- `n_burn`
- `thin`
- `pop`
- `alpha`

These can become user-configurable later through a small sampling
configuration category or explicit keyword API.

## Display Behavior

### `project.analysis.display.fit_results()`

Keep the existing entry point and dispatch by result type.

Deterministic fit:

- keep the current summary
- keep the current fitted-parameter table

Bayesian fit:

- show a sampling summary section
- show posterior parameter summaries instead of only fitted values and
  covariance-derived uncertainties

Recommended Bayesian table columns:

- datablock
- category
- entry
- parameter
- start
- MAP
- median
- posterior std
- 68% interval
- 95% interval
- units

## Plotting Behavior

### `plot_meas_vs_calc(expt_name=...)`

Keep the existing method name.

Deterministic fit:

- current measured vs calculated behavior unchanged

Bayesian fit:

- measured pattern
- MAP calculated line
- shaded credible band around prediction

Recommended default:

- one shaded 95% credible interval band

This is the clearest default for diffraction patterns. A full posterior
predictive distribution at every x value is useful but visually denser,
so it should not be the default first view.

### `plot_param_correlations()`

Keep the current method name and purpose.

Deterministic fit:

- covariance- or engine-derived correlation matrix

Bayesian fit:

- posterior-sample correlation matrix

This preserves the meaning of the method.

### New `plot_posterior_pairs()`

Add a new Bayesian-specific method for pairwise posterior exploration.

Intended behavior:

- ArviZ-backed implementation first
- Plotly backend
- pairwise scatter or density panels
- marginal distributions on the diagonal
- optional parameter subset support later

This method should serve the role of an interactive corner or pair plot.

### New `plot_param_distribution(param)`

Add a one-dimensional marginal posterior plot for a selected parameter.

Intended behavior:

- ArviZ-backed implementation first
- posterior histogram or density
- MAP marker
- median marker
- HDI overlay

This is more natural than starting with a model-comparison distribution
plot because the current library stores one active fit result, not a set
of compared Bayesian models.

### Possible Later Addition: `plot_posterior_predictive(...)`

A dedicated method can be added later for richer predictive views.

Possible API:

```python
project.display.plotter.plot_posterior_predictive(
    expt_name='hrpt',
    style='band',
)
```

Possible styles:

- `band`
- `dist`

For the first implementation, these views may also be delegated to
ArviZ where practical.

## Data Ownership

Experiment `data` categories should remain responsible for:

- measured pattern
- current calculated pattern
- current background pattern

Posterior-specific data should remain analysis-owned through
`BayesianFitResults`, because it is:

- fit-result scoped
- potentially joint across experiments
- used mainly for reporting and plotting

## Persistence and Serialization

For the first implementation:

- do not serialize full posterior chains to CIF
- do not force posterior arrays into project save files

Possible future export surfaces:

- explicit posterior export methods
- CSV summaries
- NumPy or NetCDF export if needed later

## Dependency Direction

For the first implementation, add ArviZ as a runtime dependency and use
it for Bayesian plotting and summary-oriented data transformations where
that reduces implementation cost.

Recommended direction:

- keep Plotly as the interactive rendering backend
- use ArviZ-backed plotting internally for Bayesian views where it fits
- keep the public EasyDiffraction plotting API independent of ArviZ

Future note:

- once Bayesian functionality stabilizes, EasyDiffraction may replace
  some or all ArviZ-backed plots with project-native implementations to
  improve control over styling, interactivity, and domain-specific
  diffraction presentation

## Recommended First Implementation Scope

### Phase 1

- add `MinimizerTypeEnum.BUMPS_DREAM`
- add `BumpsDreamMinimizer`
- add `BayesianFitResults`
- keep `analysis.fit_results` as the single public result slot
- make `analysis.display.fit_results()` dispatch by result type

### Phase 2

- extend `plot_meas_vs_calc()` with Bayesian credible bands
- extend `plot_param_correlations()` to use posterior samples when
  available
- add `plot_posterior_pairs()`
- add `plot_param_distribution(param)`

### Phase 3

- consider adding a lightweight `analysis.sampling` category for saved
  Bayesian configuration
- consider explicit posterior export APIs
- consider richer predictive plotting modes

## Summary

The recommended design is:

- add `'bumps (dream)'` as a normal minimizer type
- keep Bayesian analysis inside the existing `fit()` workflow
- store heavy posterior results in `BayesianFitResults`
- keep `analysis.fit_results` as the main public result entry point
- avoid a new heavy `Analysis` category for results
- only add a small new `Analysis` category later if Bayesian settings
  need to become persistent and user-configurable
