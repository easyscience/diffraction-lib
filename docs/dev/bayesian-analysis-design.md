# Bayesian Analysis Design

**Status:** Design proposal **Date:** 2026-05-07

## Goal

Add Bayesian analysis to the existing fitting workflow with the smallest
user-facing API change possible. The first implementation target is the
BUMPS DREAM sampler for diffraction refinement, with sampled parameters
bounded by each parameter's `fit_min` and `fit_max` attributes.

The word `DREAM` in this document means the BUMPS Markov-chain Monte
Carlo sampler. It does not refer to the ESS DREAM instrument.

## Design Principles

- Keep `project.analysis.fit()` as the single execution entry point.
- Add `'bumps (dream)'` as a normal minimizer tag.
- Store large posterior outputs in runtime result objects, not in CIF
  categories.
- Commit one coherent sampled parameter vector back to the project after
  sampling.
- Keep deterministic fitting and Bayesian sampling behavior explicit.
- Add Bayesian display and plotting behavior without changing existing
  deterministic semantics.

## Current Code Anchors

The design should extend the existing seams instead of adding a parallel
analysis stack:

- `src/easydiffraction/analysis/categories/fit/default.py` owns
  `fit.minimizer_type` and `fit.mode`.
- `src/easydiffraction/analysis/fitting.py` collects free parameters,
  builds the residual objective, and calls `MinimizerBase.fit()`.
- `src/easydiffraction/analysis/minimizers/base.py` defines the
  minimizer lifecycle and returns a `FitResults` instance.
- `src/easydiffraction/analysis/minimizers/bumps.py` already adapts an
  EasyDiffraction residual function into BUMPS through
  `_EasyDiffractionFitness`.
- `src/easydiffraction/analysis/fit_helpers/reporting.py` owns
  `FitResults` display behavior.
- `src/easydiffraction/display/plotting.py` currently builds parameter
  correlations from `analysis.fit_results.engine_result`.
- `pyproject.toml` already declares `arviz`, so Bayesian plotting does
  not need a new dependency decision.

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

Additional Bayesian-specific plotting methods should be added rather
than forcing every existing plotting method to accept Bayesian-specific
options:

```python
project.display.plotter.plot_posterior_pairs()
project.display.plotter.plot_param_distribution(param)
project.display.plotter.plot_posterior_predictive(expt_name='hrpt')
```

### Explicit Two-Step Workflow

`'bumps (dream)'` must not implicitly run a deterministic
Levenberg-Marquardt pre-fit. Users should call `'bumps (lm)'` first when
they want a better starting point.

Reasons:

- `fit()` stays explicit and predictable.
- Hidden pre-fitting can add significant runtime.
- Deterministic failures stay separate from sampling failures.
- The behavior matches the existing minimizer-selection model.

## Scope

### In Scope For The First Implementation

- Register `MinimizerTypeEnum.BUMPS_DREAM` with tag `'bumps (dream)'`.
- Add `BumpsDreamMinimizer`.
- Add `BayesianFitResults` and small posterior value objects.
- Require finite bounds for every sampled free parameter.
- Use bounded uniform priors implied by `fit_min` and `fit_max`.
- Use the existing residual objective and BUMPS likelihood convention.
- Store posterior chains runtime-only in `analysis.fit_results`.
- Display posterior summaries from `analysis.display.fit_results()`.
- Add posterior correlation support to `plot_param_correlations()`.
- Add posterior marginal and posterior pair plots.
- Add posterior predictive plotting with capped draw evaluation.

### Out Of Scope Initially

- Automatic deterministic pre-fitting.
- Persistent Bayesian configuration categories.
- CIF serialization of posterior chains.
- Export of posterior chains.
- Model comparison across multiple Bayesian fits.
- User-facing DREAM hyperparameter controls.
- Unbounded posterior predictive storage for every draw and every
  experiment.
- Sequential Bayesian fitting.

## Resolved Design Decisions

- `plot_posterior_predictive(...)` is required for the first useful
  Bayesian implementation.
- Posterior chains remain runtime-only and do not need an export API in
  phase 1.
- `project.analysis.fit(random_seed=...)` should be supported for
  `'bumps (dream)'` because stochastic scientific workflows need
  reproducibility. If omitted, the minimizer should generate a seed and
  record it in `BayesianFitResults.sampler_settings`.
- Deterministic minimizers should reject a non-`None` `random_seed` with
  a clear error rather than silently ignoring it.
- `BayesianFitResults.success` should mean that DREAM completed and
  produced usable posterior samples. Convergence quality should be
  stored separately in diagnostics, displayed prominently, and warned on
  when poor. It should set `success=False` only when there are no usable
  samples or the sampler itself fails.
- Posterior predictive plots should evaluate a capped subset of
  posterior draws. Start with an internal default cap of 200 draws,
  record the effective draw count in the result, and expose the cap only
  later if users need control.

## Statistical Semantics

The existing residual objective returns the residual vector consumed by
deterministic minimizers. The first Bayesian implementation should treat
the BUMPS negative log likelihood as:

```python
nllf = 0.5 * sum(residuals**2)
```

This assumes residuals are already scaled consistently with the
experimental uncertainty model. If an experiment does not provide valid
uncertainties, the posterior is only as meaningful as the residual
weighting currently used by deterministic fitting.

Initial priors are uniform inside finite `fit_min` and `fit_max` bounds
and zero outside those bounds. No Gaussian, log-normal, or
domain-specific priors are part of the first implementation.

## Core Architectural Decision

### Keep Full Results In `analysis.fit_results`

Bayesian results should be stored in a new runtime result object, not in
a new heavy `Analysis` category.

Recommended model:

- `FitResults` remains the base deterministic result container.
- `BayesianFitResults` extends `FitResults` for posterior-specific data.
- `analysis.fit_results` stores either `FitResults` or
  `BayesianFitResults`.

This keeps the existing public access pattern unchanged:

```python
project.analysis.fit_results
```

### Why Not A New Results Category Under `Analysis`

Current `Analysis` categories are lightweight, structured, project-owned
configuration or control objects:

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

Posterior chains, posterior predictive draws, and pair-plot inputs
should therefore remain runtime-only objects attached to
`BayesianFitResults`.

## Optional Future Category

A small `Analysis` category may still be useful later, but only for
Bayesian configuration, not for heavy result storage.

Possible future category name:

- `analysis.sampling`
- `analysis.bayesian`

Possible responsibilities:

- sampler type
- point estimate policy
- default highest-density interval levels
- default posterior predictive draw cap
- public DREAM hyperparameters
- persistent default random seed policy, if users need saved sampling
  preferences later

This category should stay lightweight and serializable. It must not
store raw chains.

## Runtime Type Contracts

### `BumpsDreamMinimizer`

Add a new minimizer implementation registered through `MinimizerFactory`
with tag:

```python
'bumps (dream)'
```

Responsibilities:

- Reuse `_EasyDiffractionFitness` or a small subclass of it.
- Build bounded BUMPS parameters from EasyDiffraction parameters.
- Preserve parameter order from `Fitter.fit()` through all arrays.
- Validate finite bounds before starting the sampler.
- Run DREAM with internal defaults.
- Collect posterior samples, log likelihood values, and sampler
  diagnostics where BUMPS exposes them.
- Choose and commit the MAP or best posterior sample after sampling.
- Build `BayesianFitResults`.

The existing `BumpsMinimizer` handles BUMPS parameter ordering carefully
because `FitProblem` can sort parameters internally. DREAM must preserve
the same guarantee: result arrays and summaries must be mapped back to
the original EasyDiffraction parameter order.

### `BayesianFitResults`

Subclass `FitResults` and add Bayesian-specific fields. Inherited fields
should keep deterministic-compatible meanings:

- `success`: sampler completed and produced usable posterior samples
- `parameters`: EasyDiffraction parameters updated to the committed MAP
  vector
- `starting_parameters`: an immutable snapshot of starting values, not
  the same mutable parameter objects after fitting
- `reduced_chi_square`: reduced chi-square at the committed MAP vector,
  when available
- `engine_result`: raw or lightly wrapped BUMPS DREAM result
- `fitting_time`: elapsed sampling time

Recommended Bayesian fields:

- `sampler_name`
- `point_estimate_name`
- `posterior_samples`
- `posterior_parameter_summaries`
- `posterior_predictive`
- `credible_interval_levels`
- `diagnostics`
- `sampler_settings`

`sampler_settings` should record the internal defaults actually used.
That keeps a runtime audit trail even before the settings are public
configuration.

For DREAM, `sampler_settings` must include `random_seed`, whether the
seed was user-provided or generated, and the posterior predictive draw
cap used for summaries.

### `PosteriorSamples`

Recommended fields:

- `parameter_names`: minimizer-safe names, matching sampled array order
- `parameter_labels`: user-facing labels for tables and plots
- `values`: NumPy array shaped `(chain, draw, parameter)`
- `flat_values`: optional cached array shaped `(sample, parameter)`
- `log_likelihood`: optional NumPy array shaped `(chain, draw)`
- `log_posterior`: optional NumPy array shaped `(chain, draw)`
- `bounds`: mapping from parameter name to `(fit_min, fit_max)`
- `start_values`: starting values in parameter order
- `map_values`: committed MAP values in parameter order
- `map_chain`: chain index of the MAP sample, if known
- `map_draw`: draw index of the MAP sample, if known

The object should provide one conversion helper:

```python
posterior_samples.to_arviz()
```

This keeps public EasyDiffraction methods independent of ArviZ while
letting plotting and summaries use ArviZ internally.

### `PosteriorParameterSummary`

Recommended fields:

- `parameter_name`
- `parameter_label`
- `datablock`
- `category`
- `entry`
- `parameter`
- `start`
- `map`
- `mean`
- `median`
- `std`
- `hdi`
- `fit_min`
- `fit_max`
- `units`

`hdi` should be a mapping keyed by interval probability, for example:

```python
{
    0.68: (lower_68, upper_68),
    0.95: (lower_95, upper_95),
}
```

### `PosteriorPredictiveSummary`

Posterior predictive data can be expensive for diffraction patterns, so
the first implementation should store summaries rather than every draw.

Recommended fields:

- `experiment_name`
- `x`
- `y_observed`
- `y_map`
- `intervals`
- `draw_count`

`intervals` should be keyed by interval probability:

```python
{
    0.95: (lower_y, upper_y),
}
```

Posterior predictive summaries are required for
`plot_posterior_predictive(...)`, but they should be based on a capped
subset of posterior draws. The default cap is an internal implementation
constant, initially 200 draws.

## Point Estimate Policy

After a DREAM run, project parameters should be updated to the MAP or
best posterior sample, not to independent marginal medians.

Reasons:

- Per-parameter medians can produce a parameter vector that was never
  sampled jointly.
- MAP corresponds to one coherent sampled state.
- The calculated profile shown after Bayesian fitting should correspond
  to one actual parameter set.

Posterior tables should still report mean, median, standard deviation,
and HDIs.

If the sampler fails before producing usable samples, the minimizer
should restore starting parameter values instead of leaving the project
at an arbitrary last sampled state.

## Parameter Bounds

DREAM should require finite bounds for every sampled free parameter.

Validation rules:

- Use `fit_min` and `fit_max`.
- Bounds must be finite.
- `fit_min` must be strictly less than `fit_max`.
- The starting value must be inside the bounds.
- Validate only sampled parameters: free, unconstrained parameters
  collected by `Fitter.fit()`.

Failure behavior:

- Stop before running BUMPS.
- Raise a clear `ValueError`.
- List every offending parameter and the specific problem.

This is stricter than some deterministic minimizers, but appropriate for
bounded posterior sampling.

### Interaction With Physical Limits

`Analysis.fit(use_physical_limits=True)` currently allows deterministic
minimizers to fill unbounded `fit_min` and `fit_max` from parameter
value spec physical limits. DREAM should use the same pre-processing
path.

If `use_physical_limits=True` still leaves any sampled parameter
unbounded, DREAM must fail with the same finite-bound error.

## DREAM Defaults And Reproducibility

For the first implementation, sampling parameters should stay internal
and use library defaults or small wrapper constants in `bumps_dream.py`.

Examples:

- `n_steps`
- `n_burn`
- `thin`
- `pop`
- `alpha`

These should not be user-facing API initially. They should be recorded
in `BayesianFitResults.sampler_settings` so users can inspect how a
runtime result was produced.

The exception is `random_seed`, which should be accepted as an optional
keyword by `project.analysis.fit(...)` when the active minimizer is
`'bumps (dream)'`. This keeps stochastic results reproducible without
creating a persistent sampling category in phase 1.

Tests may monkeypatch the internal defaults to keep unit and integration
tests fast. That test hook should not become public API.

## Display Behavior

### `project.analysis.display.fit_results()`

Keep the existing entry point and dispatch by result type.

Deterministic fit:

- keep the current summary
- keep the current fitted-parameter table

Bayesian fit:

- show a sampling summary section
- show sampler settings that materially affect the result
- show diagnostics when available
- show posterior parameter summaries instead of only fitted values and
  covariance-derived uncertainties

Recommended Bayesian table columns:

- datablock
- category
- entry
- parameter
- start
- MAP
- mean
- median
- posterior std
- 68% HDI
- 95% HDI
- units

Display code should not require ArviZ at render time if summaries were
already computed by the minimizer.

## Plotting Behavior

### `plot_meas_vs_calc(expt_name=...)`

Keep the existing method name.

Deterministic fit:

- current measured vs calculated behavior unchanged

Bayesian fit:

- measured pattern
- MAP calculated line
- one shaded 95% credible interval band when `posterior_predictive` is
  available

If predictive intervals are unavailable, the method should plot the MAP
calculated line and warn that posterior predictive intervals were not
computed.

This is the clearest default for diffraction patterns. A full posterior
predictive distribution at every x value is useful but visually denser,
so it should not be the default first view.

### `plot_param_correlations()`

Keep the current method name and purpose.

Deterministic fit:

- covariance- or engine-derived correlation matrix

Bayesian fit:

- posterior-sample correlation matrix computed from flattened posterior
  samples

Implementation detail:

- Check for `BayesianFitResults.posterior_samples` first.
- Fall back to the existing covariance path for deterministic results.
- Keep the current thresholding and lower-triangle display behavior.

This preserves the meaning of the method while making it work for
posterior samples.

### New `plot_posterior_pairs()`

Add a Bayesian-specific method for pairwise posterior exploration.

Intended behavior:

- ArviZ-backed implementation first
- Plotly backend where practical
- pairwise scatter or density panels
- marginal distributions on the diagonal
- optional parameter subset support

This method should serve the role of an interactive corner or pair plot.
When the active result is deterministic, it should log a clear warning
instead of trying to infer a posterior from covariance.

### New `plot_param_distribution(param)`

Add a one-dimensional marginal posterior plot for a selected parameter.

Intended behavior:

- ArviZ-backed implementation first
- posterior histogram or density
- MAP marker
- median marker
- HDI overlay

Parameter selection should accept the same identifiers users see in
fit-result tables where possible:

- parameter object
- unique parameter name
- user-facing label

Ambiguous string matches should fail with a clear error listing matching
parameters.

### New `plot_posterior_predictive(...)`

Add a dedicated method for posterior predictive views. This is required
for phase 1 because `plot_meas_vs_calc(...)` should stay a concise
measured-versus-current-calculation view.

Initial API:

```python
project.display.plotter.plot_posterior_predictive(
    expt_name='hrpt',
    style='band',
)
```

Possible styles:

- `band`
- `draws`
- `distribution`

Initial behavior:

- default to `style='band'`
- show measured pattern
- show MAP calculated line
- show a 95% posterior predictive band by default
- support capped individual posterior predictive draws with
  `style='draws'`

For the first implementation, richer views may be delegated to ArviZ
where practical, but diffraction-specific x/y plotting should remain
clear and domain-oriented.

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

When the MAP vector is committed, normal category update behavior should
make the current calculated pattern correspond to the MAP values.
Posterior predictive summaries should not mutate experiment data
categories for every posterior draw.

## Persistence And Serialization

For the first implementation:

- Do not serialize full posterior chains to CIF.
- Do not force posterior arrays into project save files.
- Let project auto-save persist the current MAP parameter values and
  `fit.minimizer_type`, as it already does for deterministic fitting.
- Treat `analysis.fit_results` as runtime-only.

Possible future export surfaces:

- explicit posterior export methods
- CSV summaries
- ArviZ NetCDF export
- NumPy archive export

## Failure And Warning Policy

Hard failures should stop before expensive sampling when possible:

- missing finite bounds
- invalid bound order
- start value outside bounds
- no sampled parameters
- BUMPS DREAM backend unavailable

Soft warnings should allow a result to be returned:

- convergence diagnostics unavailable
- convergence diagnostics outside recommended thresholds
- posterior predictive intervals not computed
- MAP value close to a fit bound

`success` should mean that the sampler completed and usable posterior
samples were produced. Convergence diagnostics should be shown and
stored separately. Poor convergence should set a diagnostic flag and log
a warning, but it should not turn the result into a hard failure unless
there are no usable samples.

## Testing Requirements

Unit tests should cover:

- `MinimizerTypeEnum.BUMPS_DREAM` and factory registration.
- Finite-bound validation with all offending parameters reported.
- Start-value-inside-bounds validation.
- `random_seed` threading and recording for DREAM.
- Non-`None` `random_seed` rejection for deterministic minimizers.
- Preservation of parameter order between EasyDiffraction parameters,
  BUMPS parameters, posterior arrays, and summaries.
- MAP commit behavior.
- Restore-start-values behavior on sampler failure.
- `BayesianFitResults.display_results()` table content.
- Posterior correlation calculation from flattened posterior samples.
- Posterior predictive summary generation with capped draw evaluation.
- Deterministic correlation behavior remaining unchanged.
- Project serialization not including posterior arrays.

Integration tests should cover:

- A small bounded synthetic refinement with `'bumps (dream)'`.
- Optional deterministic pre-fit followed by DREAM as two explicit
  `fit()` calls.
- `analysis.display.fit_results()` after DREAM.
- `plot_posterior_predictive(...)` after DREAM.
- Bayesian plotting smoke tests using a small posterior fixture.

## Implementation Plan

The detailed implementation plan is
`docs/dev/plan_bayesian-analysis.md`. It follows
`.github/copilot-instructions.md`: phase 1 is implementation only, phase
2 is verification, and every completed phase 1 implementation step must
be staged with explicit paths and committed locally before the next step
starts.

High-level implementation order:

- register the DREAM minimizer
- add Bayesian result models
- thread optional `random_seed` through fitting
- implement DREAM sampling and MAP commit behavior
- add Bayesian result display
- add posterior correlations
- add posterior distribution plots
- add posterior predictive summaries and plots

## Acceptance Criteria

The first useful implementation is complete when:

- `project.analysis.fit.show_minimizer_types()` lists `'bumps (dream)'`.
- `project.analysis.fit.minimizer_type = 'bumps (dream)'` runs through
  the same `project.analysis.fit()` path as other minimizers.
- Missing finite bounds fail before sampling with a clear parameter
  list.
- Successful sampling stores `BayesianFitResults` in
  `project.analysis.fit_results`.
- Project parameters are left at the MAP sample after a successful run.
- `project.analysis.display.fit_results()` renders posterior summaries.
- `plot_param_correlations()` works from posterior samples.
- `plot_posterior_predictive(expt_name=...)` shows measured data, MAP
  calculation, and a posterior predictive band.
- Saving a project does not serialize posterior chains.

## Implementation Discovery

During implementation, inspect which BUMPS DREAM result object fields
are stable enough to store directly in `engine_result`. Normalize
posterior samples, log-likelihood values, diagnostics, and summaries
into EasyDiffraction-owned value objects first; keep `engine_result` as
an opaque backend escape hatch.

## Summary

The recommended design is to add `'bumps (dream)'` as a normal minimizer
type, keep Bayesian analysis inside the existing `fit()` workflow, store
heavy posterior data in `BayesianFitResults`, and keep
`analysis.fit_results` as the main public result entry point. A
lightweight serialized `Analysis` category can be added later if
Bayesian settings need to become persistent and user-configurable.
