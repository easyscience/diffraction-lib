# ADR: Analysis CIF Fit State

**Status:** Proposed **Date:** 2026-05-13 **Updated:** 2026-05-18

## Context

`analysis/analysis.cif` currently persists analysis configuration such
as `_fitting.minimizer_type`, `_fitting.mode_type`, aliases,
constraints, and active mode-specific settings. It does not yet persist
the analysis-owned fit state needed to reopen a saved project and
continue the same command-line or plotting workflow.

Parameter CIF serialization already carries the committed parameter
`value`, the current `free` state, and the current `uncertainty` via CIF
bracket notation. That data belongs to structure or experiment CIF
files. Analysis-owned fit state should not be duplicated there.

The missing analysis-owned state includes:

- fit controls that apply to parameters during fitting but are not model
  values
- fit bounds and bound provenance needed by deterministic and Bayesian
  minimizers
- pre-fit scalar snapshots needed by fit recovery and undo workflows
- compact status metadata for the latest persisted fit projection
- Bayesian summary metadata and manifests for bulk array sidecars
- plot-ready Bayesian caches that make restored posterior displays
  instant rather than recomputing after load

The accepted `runtime-fit-results.md` ADR keeps full backend runtime
objects runtime-only unless a later ADR narrows the persisted
projection. This ADR defines that narrower persisted projection. It
persists stable metadata, summaries, and canonical/cached numerical
arrays, not backend driver objects.

This ADR is the canonical storage contract for fit-state persistence.
The parameter-level posterior ADR defines only the `parameter.posterior`
API projection and depends on the saved state described here.

## Decision

### 1. Every new persisted concept gets an explicit CIF category

New analysis fit-state data must be represented by named CIF categories.
Do not add loose ad-hoc tags, JSON blobs, or overload existing model
parameter tags for analysis-owned fit state.

Existing categories remain responsible for existing configuration:

- `_fitting` stores common fitting configuration.
- `_alias` and `_constraint` store symbolic analysis configuration.
- `_joint_fit`, `_sequential_fit`, and `_sequential_fit_extract` store
  active fit-mode settings.

New common fit-state categories are:

- `_fit_state`
- `_fit_parameter`
- `_fit_result`
- `_fit_parameter_correlation`

Deterministic-specific categories are:

- `_deterministic_result`
- `_deterministic_parameter_result`

Bayesian-specific categories are:

- `_bayesian_result`
- `_bayesian_sampler`
- `_bayesian_convergence`
- `_bayesian_parameter_posterior`
- `_bayesian_distribution_cache`
- `_bayesian_pair_cache`
- `_bayesian_predictive_dataset`

Bulk arrays referenced by Bayesian categories live in
`analysis/results.h5`.

### 2. Add `_fit_state` for schema versioning

`_fit_state` is a single-item category for the persisted fit-state
schema:

```cif
_fit_state.schema_version 1
```

This version applies to the fit-state CIF categories and any HDF5
sidecar manifests they reference. It is not the EasyDiffraction package
version. Individual result categories should not repeat `schema_version`
unless they later need independent evolution.

### 3. Add `_fit_parameter` for per-parameter fit controls

`_fit_parameter` is an analysis-owned loop keyed by live parameter
unique name:

```cif
loop_
_fit_parameter.param_unique_name
_fit_parameter.fit_min
_fit_parameter.fit_max
_fit_parameter.fit_bounds_uncertainty_multiplier
_fit_parameter.start_value
_fit_parameter.start_uncertainty
lbco.cell.length_a 3.8895 3.8920 4.0 3.8909 0.0003
hrpt.peak.broad_gauss_u 0.05 0.11 4.0 0.08 0.007
```

Fields:

- `param_unique_name`
- `fit_min`
- `fit_max`
- `fit_bounds_uncertainty_multiplier`
- `start_value`
- `start_uncertainty`

`fit_min` and `fit_max` are required so saved DREAM projects can be
rerun from the CLI without recreating bounds in Python. The
`fit_bounds_uncertainty_multiplier` field preserves how
uncertainty-derived bounds were created. `start_value` and
`start_uncertainty` capture the most recent pre-fit scalar state for
fit-result displays and undo workflows.

The committed parameter value after a fit remains in structure or
experiment CIF. `_fit_parameter` does not duplicate active values.

### 4. Add `_fit_result` for common fit status

`_fit_result` is a single-item category for fields shared across fit
types:

```cif
_fit_result.result_kind bayesian
_fit_result.success true
_fit_result.message "Sampler completed"
_fit_result.iterations 3000
_fit_result.fitting_time 82.4
_fit_result.reduced_chi_square 1.031
```

Fields:

- `result_kind`
- `success`
- `message`
- `iterations`
- `fitting_time`
- `reduced_chi_square`

`result_kind` identifies the latest persisted projection, for example
`deterministic` or `bayesian`. Backend runtime objects, optimizer
instances, driver state, and arbitrary engine payloads are not stored in
this category.

### 5. Add `_fit_parameter_correlation` for reusable correlations

`_fit_parameter_correlation` stores compact pairwise correlation
summaries keyed by a persisted `id`:

```cif
loop_
_fit_parameter_correlation.id
_fit_parameter_correlation.source_kind
_fit_parameter_correlation.param_unique_name_i
_fit_parameter_correlation.param_unique_name_j
_fit_parameter_correlation.correlation
"posterior:lbco.cell.length_a:hrpt.peak.broad_gauss_u" posterior lbco.cell.length_a hrpt.peak.broad_gauss_u 0.87
```

Fields:

- `id`
- `source_kind`
- `param_unique_name_i`
- `param_unique_name_j`
- `correlation`

Rows are keyed by the persisted `id` field so each correlation pair has
stable collection identity in both Python and CIF. When a caller does
not provide an explicit `id`, implementations should derive one from
the normalized `source_kind`, `param_unique_name_i`, and
`param_unique_name_j` values.

Only the upper triangle excluding the diagonal is stored. Correlation
heatmaps can be restored from this loop alone. Posterior pair plots
still use the Bayesian pair cache or posterior samples.

### 6. Store deterministic metadata in dedicated categories

Deterministic fits use the common `_fit_parameter`, `_fit_result`, and
`_fit_parameter_correlation` categories, plus deterministic-specific
categories for optimizer details and parameter-result display state.

`_deterministic_result` stores one saved deterministic result header:

- `optimizer_name`
- `method_name`
- `objective_name`
- `objective_value`
- `n_data_points`
- `n_parameters`
- `n_free_parameters`
- `degrees_of_freedom`
- `covariance_available`
- `correlation_available`

`_deterministic_parameter_result` stores one row per parameter varied in
the latest deterministic fit:

- `order_index`
- `param_unique_name`
- `final_value`
- `final_uncertainty`
- `at_lower_bound`
- `at_upper_bound`

`final_value` and `final_uncertainty` are a result projection for
display and consistency checks. The calculation source of truth remains
the live parameter value and uncertainty restored from structure and
experiment CIF. If the deterministic result projection disagrees with
the live parameter state on load, loaders should warn and prefer the
live parameter state for calculations.

Pre-fit values and uncertainties are not duplicated in
`_deterministic_parameter_result`; they come from `_fit_parameter`.
Parameter correlations, when available from covariance, are stored in
`_fit_parameter_correlation` with `source_kind deterministic`.

### 7. Store Bayesian metadata in dedicated categories

Bayesian persistence extends the common categories with explicit
Bayesian categories in `analysis/analysis.cif`.

`_bayesian_result` stores one saved Bayesian result header:

- `sampler_name`
- `point_estimate_name`
- `success`
- `sampler_completed`
- `best_log_posterior`
- `credible_interval_inner`
- `credible_interval_outer`
- `has_posterior_samples`
- `has_distribution_cache`
- `has_pair_cache`
- `has_posterior_predictive`
- `sidecar_file`

`_bayesian_sampler` stores resolved sampler settings actually used:

- `steps`
- `burn`
- `thin`
- `pop`
- `parallel`
- `init`
- `random_seed`

`_bayesian_convergence` stores top-level diagnostics and shapes:

- `converged`
- `max_r_hat`
- `min_ess_bulk`
- `n_draws`
- `n_chains`
- `n_parameters`

`_bayesian_parameter_posterior` stores one posterior summary row per
sampled parameter:

- `order_index`
- `unique_name`
- `display_name`
- `best_sample_value`
- `median`
- `uncertainty`
- `interval_68_lower`
- `interval_68_upper`
- `interval_95_lower`
- `interval_95_upper`
- `ess_bulk`
- `r_hat`

`order_index` defines the parameter column order in posterior sample
arrays stored in the HDF5 sidecar. `parameter.posterior` is rebuilt from
this loop on load; posterior summary data is not duplicated in structure
or experiment CIF files.

### 8. Store plot-ready Bayesian caches in explicit manifest categories

Bayesian plotting should not require expensive post-load preparation
when the project was saved after a successful Bayesian fit. Plot-ready
caches therefore have their own manifest categories in
`analysis/analysis.cif`, with the actual arrays stored in HDF5.

`_bayesian_distribution_cache` supports
`project.display.posterior.distribution(...)`:

- `param_unique_name`
- `x_path`
- `density_path`
- `n_grid`
- `n_draws_cached`

`_bayesian_pair_cache` supports `project.display.posterior.pairs(...)`:

- `param_unique_name_x`
- `param_unique_name_y`
- `id`
- `x_path`
- `y_path`
- `density_path`
- `contour_level_path`
- `n_grid_x`
- `n_grid_y`
- `n_draws_cached`

`_bayesian_pair_cache` rows are keyed by the persisted `id` field so
each cached parameter pair has stable identity in both Python and CIF.
When a caller does not provide an explicit `id`, implementations should
derive one from the normalized `param_unique_name_x` and
`param_unique_name_y` values.

`_bayesian_predictive_dataset` supports
`project.display.posterior.predictive(...)`:

- `experiment_name`
- `x_axis_name`
- `x_path`
- `best_sample_prediction_path`
- `lower_95_path`
- `upper_95_path`
- `lower_68_path`
- `upper_68_path`
- `draws_path`
- `n_x`
- `n_draws_cached`

`_bayesian_predictive_dataset` is keyed by `experiment_name` in this
schema, with at most one cached predictive dataset per experiment.

The manifest rows are the source of truth for HDF5 paths. HDF5 group
naming conventions are implementation details and may change as long as
the manifest remains valid.

### 9. Store bulk Bayesian arrays in `analysis/results.h5`

`analysis/analysis.cif` remains the text metadata entry point. Numerical
arrays large enough to make CIF unwieldy are stored in:

- `analysis/results.h5`

The reference implementation uses a direct `h5py` dependency to read
and write this sidecar.

Required canonical posterior arrays, when available:

- `/posterior/parameter_samples`
- `/posterior/log_posterior`
- `/posterior/draw_index`

Expected shapes:

- `/posterior/parameter_samples`: `(n_draws, n_chains, n_parameters)`
- `/posterior/log_posterior`: `(n_draws, n_chains)`
- `/posterior/draw_index`: `(n_draws,)`

Recommended plot-cache array layout:

- `/posterior/distribution/<id>/x`
- `/posterior/distribution/<id>/density`
- `/posterior/pairs/<id>/x`
- `/posterior/pairs/<id>/y`
- `/posterior/pairs/<id>/density`
- `/posterior/pairs/<id>/contour_levels`
- `/predictive/<experiment>/x`
- `/predictive/<experiment>/best_sample_prediction`
- `/predictive/<experiment>/lower_95`
- `/predictive/<experiment>/upper_95`
- `/predictive/<experiment>/lower_68`
- `/predictive/<experiment>/upper_68`
- `/predictive/<experiment>/draws`

The sidecar is optional for summary-only restore. If it is missing,
`_bayesian_parameter_posterior` can still restore parameter summaries
and fit-result tables, but posterior plots that require arrays or
plot-ready caches must warn clearly or offer recomputation.

Do not persist backend-specific runtime objects such as DREAM driver
instances, raw engine result objects, or ArviZ `InferenceData`.

### 10. Prepare Bayesian plot data immediately after sampling

After DREAM sampling completes, the UX should include an explicit
post-processing step before the fit is considered fully saved:

```text
Processing Bayesian results...
```

During this step, EasyDiffraction should prepare:

- posterior parameter summaries
- convergence diagnostics
- parameter correlation summaries
- distribution density cache arrays
- pair density and contour cache arrays
- posterior predictive bands and cached draws for available experiments
- HDF5 sidecar datasets and CIF manifest rows

For saved projects, `project.analysis.fit()` already triggers a save at
the end of fitting. In that case the post-processing step should run
before the automatic save writes `analysis/analysis.cif` and
`analysis/results.h5`. For unsaved projects, the same prepared data
remains in memory and is written on the next `project.save_as(...)` or
`project.save()`.

The display methods should then prefer persisted plot caches:

```python
project.display.posterior.distribution()
project.display.posterior.pairs()
project.display.posterior.predictive(expt_name='hrpt')
```

When valid caches are available, these calls should only load arrays and
render plots. They should not rerun posterior summarization, KDE,
contour preparation, or posterior predictive calculations.

### 11. Restore order is configuration first, fit state second

Load order should be:

1. standard analysis configuration
2. aliases and constraints
3. active mode-specific settings
4. `_fit_state`
5. `_fit_parameter`
6. `_fit_result`
7. `_fit_parameter_correlation`
8. deterministic metadata categories when `result_kind` is
   `deterministic`
9. Bayesian metadata categories when `result_kind` is `bayesian`
10. Bayesian HDF5 sidecar arrays and plot caches

This ensures bounds and live parameter references are available before
fit-specific summaries and cached plot data are attached.

### 12. Saved examples use current `_fitting.*` tags

Suggested deterministic `analysis/analysis.cif` fragment:

```cif
_fitting.mode_type single
_fitting.minimizer_type "lmfit (leastsq)"

_fit_state.schema_version 1

loop_
_fit_parameter.param_unique_name
_fit_parameter.fit_min
_fit_parameter.fit_max
_fit_parameter.fit_bounds_uncertainty_multiplier
_fit_parameter.start_value
_fit_parameter.start_uncertainty
lbco.cell.length_a 3.8895 3.8920 4.0 3.8909 0.0003
hrpt.peak.broad_gauss_u 0.05 0.11 4.0 0.08 0.007

_fit_result.result_kind deterministic
_fit_result.success true
_fit_result.message "Fit converged"
_fit_result.iterations 37
_fit_result.fitting_time 1.82
_fit_result.reduced_chi_square 1.031

_deterministic_result.optimizer_name lmfit
_deterministic_result.method_name leastsq
_deterministic_result.objective_name chi_square
_deterministic_result.objective_value 2568.4
_deterministic_result.n_data_points 2500
_deterministic_result.n_parameters 5
_deterministic_result.n_free_parameters 2
_deterministic_result.degrees_of_freedom 2498
_deterministic_result.covariance_available true
_deterministic_result.correlation_available true

loop_
_deterministic_parameter_result.order_index
_deterministic_parameter_result.param_unique_name
_deterministic_parameter_result.final_value
_deterministic_parameter_result.final_uncertainty
_deterministic_parameter_result.at_lower_bound
_deterministic_parameter_result.at_upper_bound
0 lbco.cell.length_a 3.89091 0.0003 false false
1 hrpt.peak.broad_gauss_u 0.08 0.007 false false

loop_
_fit_parameter_correlation.source_kind
_fit_parameter_correlation.param_unique_name_i
_fit_parameter_correlation.param_unique_name_j
_fit_parameter_correlation.correlation
deterministic lbco.cell.length_a hrpt.peak.broad_gauss_u 0.42
```

Suggested Bayesian `analysis/analysis.cif` fragment:

```cif
_fitting.mode_type single
_fitting.minimizer_type "bumps (dream)"

_fit_state.schema_version 1

loop_
_fit_parameter.param_unique_name
_fit_parameter.fit_min
_fit_parameter.fit_max
_fit_parameter.fit_bounds_uncertainty_multiplier
_fit_parameter.start_value
_fit_parameter.start_uncertainty
lbco.cell.length_a 3.8895 3.8920 4.0 3.8909 0.0003
hrpt.peak.broad_gauss_u 0.05 0.11 4.0 0.08 0.007

_fit_result.result_kind bayesian
_fit_result.success true
_fit_result.message "Sampler completed"
_fit_result.iterations 3000
_fit_result.fitting_time 82.4
_fit_result.reduced_chi_square 1.031

_bayesian_result.sampler_name dream
_bayesian_result.point_estimate_name best_sample
_bayesian_result.success true
_bayesian_result.sampler_completed true
_bayesian_result.best_log_posterior -1542.77
_bayesian_result.credible_interval_inner 0.68
_bayesian_result.credible_interval_outer 0.95
_bayesian_result.has_posterior_samples true
_bayesian_result.has_distribution_cache true
_bayesian_result.has_pair_cache true
_bayesian_result.has_posterior_predictive true
_bayesian_result.sidecar_file "results.h5"

_bayesian_sampler.steps 3000
_bayesian_sampler.burn 600
_bayesian_sampler.thin 1
_bayesian_sampler.pop 20
_bayesian_sampler.parallel 0
_bayesian_sampler.init lhs
_bayesian_sampler.random_seed 12345

_bayesian_convergence.converged true
_bayesian_convergence.max_r_hat 1.01
_bayesian_convergence.min_ess_bulk 812.4
_bayesian_convergence.n_draws 2400
_bayesian_convergence.n_chains 20
_bayesian_convergence.n_parameters 2

loop_
_bayesian_parameter_posterior.order_index
_bayesian_parameter_posterior.unique_name
_bayesian_parameter_posterior.display_name
_bayesian_parameter_posterior.best_sample_value
_bayesian_parameter_posterior.median
_bayesian_parameter_posterior.uncertainty
_bayesian_parameter_posterior.interval_68_lower
_bayesian_parameter_posterior.interval_68_upper
_bayesian_parameter_posterior.interval_95_lower
_bayesian_parameter_posterior.interval_95_upper
_bayesian_parameter_posterior.ess_bulk
_bayesian_parameter_posterior.r_hat
0 lbco.cell.length_a "length_a" 3.89091 3.89090 0.0003 3.8906 3.8912 3.8903 3.8915 812.4 1.01

loop_
_bayesian_distribution_cache.param_unique_name
_bayesian_distribution_cache.x_path
_bayesian_distribution_cache.density_path
_bayesian_distribution_cache.n_grid
_bayesian_distribution_cache.n_draws_cached
lbco.cell.length_a /posterior/distribution/0/x /posterior/distribution/0/density 256 48000

loop_
_bayesian_predictive_dataset.experiment_name
_bayesian_predictive_dataset.x_axis_name
_bayesian_predictive_dataset.x_path
_bayesian_predictive_dataset.best_sample_prediction_path
_bayesian_predictive_dataset.lower_95_path
_bayesian_predictive_dataset.upper_95_path
_bayesian_predictive_dataset.lower_68_path
_bayesian_predictive_dataset.upper_68_path
_bayesian_predictive_dataset.draws_path
_bayesian_predictive_dataset.n_x
_bayesian_predictive_dataset.n_draws_cached
hrpt ttheta /predictive/hrpt/x /predictive/hrpt/best_sample_prediction /predictive/hrpt/lower_95 /predictive/hrpt/upper_95 /predictive/hrpt/lower_68 /predictive/hrpt/upper_68 /predictive/hrpt/draws 2500 200
```

## Consequences

### Positive

- `analysis/analysis.cif` becomes the single text manifest for
  analysis-owned fit state.
- Saved DREAM projects have enough fit bounds to run again from the CLI.
- Bayesian save/load separates compact CIF metadata from large HDF5
  arrays.
- Restored posterior displays can render from cached arrays without
  expensive recomputation.
- Parameter posterior summaries are rebuilt from analysis-level data
  rather than duplicated in model CIF.

### Trade-offs

- The runtime fit-results ADR must be read as "runtime-only unless a
  narrower persistence ADR defines a saved projection"; this ADR defines
  that projection.
- Bayesian persistence now spans CIF and HDF5, so save/load must
  validate consistency between manifest rows and sidecar datasets.
- Post-fit processing increases the time between sampler completion and
  final saved project state, but makes later display calls much faster.
- Cached plot arrays are derived data and must be invalidated when a new
  fit runs or when the project changes in ways that make the saved fit
  result stale.

## Deferred Work

- Exact compression and chunking policy for HDF5 datasets.
- Multiple saved Bayesian runs per project.
- Optional covariance persistence beyond correlation summaries.
- Cache invalidation UX for manual edits after a saved fit.
- Persistence for posterior-capable minimizers beyond DREAM.
