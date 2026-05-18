# ADR: Analysis CIF Fit State

## Status

Accepted current design.

## Date

2026-05-18

## Group

Analysis and fitting.

## Context

`analysis/analysis.cif` already persists analysis configuration such as
`_fitting.minimizer_type`, `_fitting.mode_type`, aliases, constraints,
and active fit-mode settings. That configuration alone is not enough to
reopen a saved project and continue the same fit-result, plotting, and
command-line workflow.

Analysis-owned fit state needs to persist:

- fit bounds and bound provenance
- pre-fit scalar snapshots for recovery workflows
- compact status metadata for the latest saved fit projection
- deterministic correlation summaries
- Bayesian summary metadata and manifests for bulk array sidecars
- plot-ready Bayesian caches so restored posterior displays do not need
  to recompute on first use

Committed model parameter values and uncertainties already persist in
structure and experiment CIF files through the accepted free-flag CIF
encoding. Those committed values must remain the source of truth for the
current model state.

The accepted runtime fit-results ADR keeps backend runtime objects
runtime-only unless a narrower persistence ADR defines a saved
projection. This ADR defines that narrower saved projection.

## Decision

Persist analysis-owned fit state as explicit sibling categories in
`analysis/analysis.cif`, with large Bayesian arrays stored in
`analysis/results.h5`.

Do not add a dedicated `_fit_state` category or
`_fit_state.schema_version`. Persisted fit state is detected from
`_fit_result` and the related fit-state categories.

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

`_fit_result` stores the latest saved fit header:

- `result_kind`
- `success`
- `message`
- `iterations`
- `fitting_time`
- `reduced_chi_square`

`_fit_parameter_correlation` stores pairwise deterministic or posterior
correlation summaries keyed by a persisted `id`. Only unique parameter
pairs are stored.

### Deterministic fit projection

Deterministic fits persist `_deterministic_result` in addition to the
common categories above.

`_deterministic_result` stores compact optimizer metadata and counts:

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

Do not persist a `_deterministic_parameter_result` category. Final
deterministic parameter values and uncertainties already persist in the
model CIF files, and restored deterministic ordering comes from
`_fit_parameter`.

### Bayesian fit projection

Bayesian fits persist these additional categories:

- `_bayesian_result`
- `_bayesian_sampler`
- `_bayesian_convergence`
- `_bayesian_parameter_posterior`
- `_bayesian_distribution_cache`
- `_bayesian_pair_cache`
- `_bayesian_predictive_dataset`

`_bayesian_result` stores the saved Bayesian header and sidecar flags,
including `sidecar_file`, `has_posterior_samples`,
`has_distribution_cache`, `has_pair_cache`, and
`has_posterior_predictive`.

`_bayesian_sampler` stores the resolved sampler settings used for the
run. `parallel` persists the resolved non-negative worker count as an
integer.

`_bayesian_convergence` stores convergence metadata and posterior array
shape counts.

`_bayesian_parameter_posterior` stores one summary row per sampled
parameter, including credible intervals, uncertainty, ESS, and R-hat.
Its row order defines the saved posterior parameter order.

`_bayesian_distribution_cache`, `_bayesian_pair_cache`, and
`_bayesian_predictive_dataset` store manifest rows for plot-ready
posterior caches. Distribution and predictive caches are persisted for
any Bayesian fit with posterior samples, including single-parameter
fits. Pair caches and posterior correlation summaries are only persisted
when more than one parameter was sampled.

`parameter.posterior` is not part of this accepted design. This ADR
persists analysis-level posterior summaries and caches only. Any future
parameter-level posterior API remains a separate decision.

### Bayesian sidecar

Persist large Bayesian arrays in `analysis/results.h5` using `h5py`.
This includes canonical posterior arrays and any saved distribution,
pair, and predictive cache arrays referenced by the CIF manifests.

The persisted `sidecar_file` value is a local file name only. It must
resolve to a basename inside the project `analysis/` directory. Absolute
paths and traversal paths are rejected and fall back to `results.h5`.

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
2. common fit-state categories
3. deterministic or Bayesian fit-specific categories according to
   `_fit_result.result_kind`
4. Bayesian sidecar arrays when a Bayesian sidecar is expected

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
load must validate consistency between manifest rows and bulk datasets.

The accepted runtime fit-results ADR should now be read as runtime-only
except where this narrower projection explicitly persists fit-state
metadata, summaries, and cache arrays.
