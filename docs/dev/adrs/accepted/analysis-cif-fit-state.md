# ADR: Analysis CIF Fit State

## Status

Accepted current design.

## Date

2026-05-18

## Group

Analysis and fitting.

## Context

`analysis/analysis.cif` already persists analysis configuration such as
`_minimizer.type`, `_fitting_mode.type`, aliases, constraints, and
active fit-mode settings. That configuration alone is not enough to
reopen a saved project and continue the same fit-result, plotting, and
command-line workflow.

Analysis-owned fit state needs to persist:

- fit bounds and bound provenance
- pre-fit scalar snapshots for recovery workflows
- compact status metadata for the latest saved fit projection
- deterministic correlation summaries
- minimizer-specific fit outputs on the paired `_fit_result.*` category
- per-parameter posterior summaries on `_fit_parameter`
- large posterior arrays and plot caches in `analysis/results.h5`

Committed model parameter values and uncertainties already persist in
structure and experiment CIF files through the accepted free-flag CIF
encoding. Those committed values must remain the source of truth for the
current model state.

The accepted runtime fit-results ADR keeps backend runtime objects
runtime-only unless a narrower persistence ADR defines a saved
projection. This ADR defines that narrower saved projection.

## Decision

Persist analysis-owned fit state as explicit analysis categories in
`analysis/analysis.cif`, with large posterior arrays stored in
`analysis/results.h5`.

Do not add a dedicated `_fit_state` category or
`_fit_state.schema_version`. Persisted fit state is detected from
`_fit_result`, `_fit_parameter`, and `_fit_parameter_correlation`.

### Common fit-state categories

Persist these common categories for any saved fit projection:

- `_fit_parameter`
- `_fit_result`
- `_fit_parameter_correlation`

`_fit_parameter` stores analysis-owned per-parameter fit controls and
pre-fit scalar snapshots:

- `param_unique_name`
- `fit_min`
- `fit_max`
- `fit_bounds_uncertainty_multiplier`
- `start_value`
- `start_uncertainty`

For Bayesian fit projections, `_fit_parameter` also stores per-parameter
posterior summaries:

- `posterior_best_sample_value`
- `posterior_median`
- `posterior_uncertainty`
- `posterior_interval_68_low`
- `posterior_interval_68_high`
- `posterior_interval_95_low`
- `posterior_interval_95_high`
- `posterior_gelman_rubin`
- `posterior_effective_sample_size_bulk`

`_fit_result` stores the latest saved fit header and scalar
family-specific fit outputs:

- `result_kind`
- `success`
- `message`
- `iterations`
- `fitting_time`
- `reduced_chi_square`

`_fit_parameter_correlation` stores pairwise deterministic or posterior
correlation summaries keyed by a persisted `id`. Only unique parameter
pairs are stored.

### Minimizer fit projection

The active `_minimizer.*` category stores user-selected solver inputs
only. Scalar outputs are written to the paired `_fit_result.*` category.
Deterministic fit-result classes add compact fit output counts:

- `objective_name`
- `objective_value`
- `n_data_points`
- `n_parameters`
- `n_free_parameters`
- `degrees_of_freedom`
- `covariance_available`
- `correlation_available`
- `exit_reason`

Do not persist a `_deterministic_parameter_result` category. Final
deterministic parameter values and uncertainties already persist in the
model CIF files, and restored deterministic ordering comes from
`_fit_parameter`.

Bayesian minimizer classes store sampler inputs under `_minimizer.*`:

- `sampling_steps`
- `burn_in_steps`
- `thinning_interval`
- `population_size`
- `parallel_workers`
- `initialization_method`
- `random_seed`

Bayesian fit-result classes store scalar outputs under `_fit_result.*`:

- `point_estimate_name`
- `sampler_completed`
- `credible_interval_inner`
- `credible_interval_outer`
- `acceptance_rate_mean`
- `gelman_rubin_max`
- `effective_sample_size_min`
- `best_log_posterior`

Bayesian per-parameter posterior summaries are stored on the
corresponding `_fit_parameter` rows. Their row order defines the saved
posterior parameter order.

`FitResults.optimizer_name` and `FitResults.method_name` are restored
from the active minimizer category class instead of being persisted as
independent CIF fields. Each concrete minimizer category declares a
class-level `_engine_metadata: ClassVar[dict[str, str]]` containing
those two display values. This keeps the persisted projection to the
user-selected `_minimizer.type` and removes duplicated deterministic
metadata from `_minimizer.*`.

### Posterior sidecar

Persist large posterior arrays in `analysis/results.h5` using `h5py`.
This includes canonical posterior arrays and saved distribution, pair,
and predictive cache arrays. The HDF5 file is self-describing; no CIF
manifest rows or sidecar filename tags are persisted.

The sidecar filename is fixed to `results.h5` inside the project
`analysis/` directory.

If the sidecar is missing on load, summary rows in
`analysis/analysis.cif` still restore fit tables and metadata. Features
that require missing bulk arrays must warn clearly instead of failing
silently.

### Save and restore behavior

After a fit completes, project save writes the fit-state projection
before the project is considered fully persisted. For Bayesian fits,
that includes the prepared summaries and saved plot caches used by
posterior displays.

Load order is:

1. standard analysis configuration
2. `_minimizer.*` settings according to the active `_minimizer.type`
3. common and family-specific `_fit_result.*` fields on the paired class
4. `_fit_parameter` and `_fit_parameter_correlation`
5. posterior sidecar arrays when a Bayesian result is expected

Persist backend runtime objects, optimizer instances, and raw driver
payloads nowhere in this design.

## Consequences

Saved projects reopen with enough fit-state context to display the last
saved result and rerun fits without rebuilding analysis-owned bounds by
hand.

Deterministic persistence stays compact because committed parameter
values remain in the model CIF files instead of being duplicated in a
second deterministic per-parameter result loop.

Bayesian persistence spans CIF metadata and an HDF5 sidecar, so save and
load must validate consistency between `_fit_parameter` rows and bulk
datasets.

The accepted runtime fit-results ADR should now be read as runtime-only
except where this narrower projection explicitly persists fit-state
metadata, summaries, and cache arrays.
