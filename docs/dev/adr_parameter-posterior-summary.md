# ADR: Parameter-Level Posterior Projection and Bayesian Persistence

**Status:** Proposed  
**Date:** 2026-05-13

## Context

`GenericParameter` already stores fit-adjacent helper data such as
`uncertainty`, `fit_min`, and `fit_max`, while `value` remains the
single scalar used by calculations.

Bayesian DREAM currently keeps posterior state only on
`analysis.fit_results` via `BayesianFitResults`, including
`posterior_samples`, `posterior_parameter_summaries`,
`posterior_predictive`, diagnostics, and sampler settings. The current
architecture document describes this state as runtime-only and not
serialized.

`analysis.fit_results` already changes by analysis type: deterministic
fits use `FitResults`, while posterior-capable fits such as DREAM use
`BayesianFitResults`. This ADR preserves that result-model split.

The user-facing need is more local: when a posterior-capable fit has
completed, each parameter should expose a compact Bayesian summary for
inspection without forcing users to traverse `analysis.fit_results`. At
the same time, `parameter.value` must remain the only scalar used by the
live model, minimizer setup, constraints, and category updates.

There is also a staleness problem. After a manual parameter edit or a
new fit, fit-derived helper data must be cleared or replaced as a group.
Keeping old posterior summaries after the active parameter state changes
would mislead users.

One more implementation constraint matters: minimizers currently apply
final fitted values through `_set_value_from_minimizer(...)` and then
write `param.uncertainty = ...` directly. If `uncertainty` and posterior
metadata become read-only fit outputs and the public `value` setter
starts clearing stale fit metadata on manual edits, fit-result
application must move to a dedicated internal update path so that valid
fit outputs are installed atomically instead of being cleared
accidentally.

## Decision

### 1. Add one optional posterior object to each parameter

Each `GenericParameter` will gain a read-only `posterior` property whose
default value is `None`.

This property is convenience metadata only. It does not participate in
calculations. `parameter.value` remains the only scalar used by the live
model.

### 2. Reuse the existing Bayesian summary container

Do not add separate flat parameter attributes such as `median`,
`map_estimate`, `interval_95`, `r_hat`, or `ess_bulk`.

Instead, the parameter-level projection reuses the existing
`PosteriorParameterSummary` object already produced for
`BayesianFitResults`. This keeps one grouped summary shape for display,
inspection, and later persistence.

The summary object currently provides the right level of detail:

- `map_estimate`
- `median`
- `uncertainty`
- `interval_68`
- `interval_95`
- `r_hat`
- `ess_bulk`

`unique_name` and `display_name` remain redundant but acceptable when
the object is attached to a parameter.

Different communities use different names for this scalar spread term:
`standard deviation`, `estimated standard deviation` (`e.s.d.`), and
`standard uncertainty` (`s.u.` / `su`). The public EasyDiffraction API
selects `uncertainty` as the canonical name because it already matches
the existing parameter API, aligns better with CIF terminology, and can
be used consistently for both deterministic and Bayesian results. For
Bayesian summaries, this `uncertainty` value is computed from the
posterior standard deviation.

The internal field names stay compact and code-oriented. User-facing
tables, summaries, and plot annotations should use these friendly
labels:

- `map_estimate` -> `MAP estimate`
- `median` -> `Median`
- `uncertainty` -> `Standard uncertainty`
- `interval_68` -> `68% credible interval`
- `interval_95` -> `95% credible interval`
- `r_hat` -> `R-hat`
- `ess_bulk` -> `Bulk ESS`

Asymmetric interval information remains explicit through the stored
lower and upper bounds. For example, `parameter.posterior.interval_95`
returns a `(lower, upper)` tuple rather than one symmetric uncertainty
value.

Example user access:

```python
param = project.phases['lbco'].cell.length_a

current_value = param.value
current_uncertainty = param.uncertainty

if param.posterior is not None:
  map_estimate = param.posterior.map_estimate
  median = param.posterior.median
  uncertainty = param.posterior.uncertainty
  low95, high95 = param.posterior.interval_95
  r_hat = param.posterior.r_hat
  ess_bulk = param.posterior.ess_bulk
```

### 3. Make fit outputs read-only for the user

`uncertainty` becomes a read-only fit output on the public parameter
API. `posterior` is also read-only.

Users may inspect these properties, but only internal fit-application
paths may set or clear them.

This keeps the writable public parameter state focused on user intent:
`value`, `free`, `fit_min`, `fit_max`, and related configuration.

### 4. Populate it only for posterior-capable fit methods

Only fit methods that actually produce posterior summaries may populate
`parameter.posterior`.

At present this means only `bumps (dream)`.

Do not add a generic minimizer-capability abstraction yet. That would
introduce a new abstraction before there is a second concrete posterior
fit method. When another posterior-capable minimizer exists, the shared
contract can be extracted then.

### 5. Treat parameter-level posterior data as a projection, not the canonical result

The canonical Bayesian result remains `analysis.fit_results`.

`parameter.posterior` is a synchronized projection of the current fit
result for user convenience. It must never be the only place where
Bayesian information lives, because it cannot represent joint posterior
arrays, predictive summaries, or cross-parameter correlations.

### 6. Clear or replace fit-derived metadata as a group

Fit-derived helper data on a parameter must be coherent.

The following policy applies:

- Manual edit of `parameter.value` clears `parameter.uncertainty` and
  `parameter.posterior`.
- A deterministic fit replaces `value` and `uncertainty`, then clears
  `posterior`.
- A posterior fit replaces `value`, `uncertainty`, and `posterior`
  together.

Manual user edits of `uncertainty` and `posterior` are not supported,
because both are read-only fit outputs.

Configuration attributes such as `free`, `fit_min`, `fit_max`, units,
and `fit_bounds_uncertainty_multiplier` are not cleared by this policy.
They are parameter configuration or user intent, not posterior output.

### 7. Add a dedicated internal fit-application path

To support the clearing policy above, fit application must not rely on
public setters alone.

Implementation should add private helpers on `GenericParameter` to set
and clear fit-derived state explicitly, for example:

- `_set_uncertainty(...)`
- `_set_posterior(...)`
- `_clear_fit_metadata()`
- `_apply_deterministic_fit_update(...)`
- `_apply_posterior_fit_update(...)`

The exact helper names can be refined during implementation, but the
design requirement is fixed: manual user edits clear stale metadata,
while internal fit application installs fresh metadata atomically.

### 8. Commit MAP to `parameter.value` after Bayesian fits

After a posterior-capable fit, `parameter.value` is committed from the
maximum-a-posteriori estimate.

MAP is chosen because it is a coherent joint point estimate across all
free parameters. Marginal medians remain available on
`parameter.posterior`, but they are summary data rather than the active
live model state.

### 9. Keep `uncertainty` as a convenience scalar after Bayesian fits

`parameter.uncertainty` remains a single convenience scalar even after
posterior fits.

For posterior-capable fits, populate it from posterior standard
deviation and expose it as `uncertainty`. This preserves one scalar API
term across deterministic and Bayesian results while keeping the
calculation itself statistically conventional.

Asymmetric interval information is not squeezed into
`parameter.uncertainty`; it remains available only via
`parameter.posterior`.

### 10. Persist canonical Bayesian state at analysis level

Canonical Bayesian state is owned by `analysis.fit_results`, not by
individual parameters.

When the active result is a `BayesianFitResults` instance, persistence
must save enough data to restore two distinct capability levels:

- summary-only restore for parameter inspection and tables
- full restore for posterior plots and predictive plots

`parameter.posterior` is never serialized as a per-parameter property.
It is always rebuilt from the canonical analysis-level persisted data.

### 11. Persist fit-control and Bayesian metadata in `analysis/analysis.cif`

The existing `analysis/analysis.cif` file remains the text metadata
entry point for analysis persistence.

The persisted fit-control and Bayesian metadata is split into explicit
CIF categories.

#### 11.1 `_fit_parameter` loop

Stores analysis-owned per-parameter fit metadata that is not currently
covered by parameter CIF serialization.

This loop exists because the committed parameter CIF representation
already carries the active `value`, current `free` state, and current
`uncertainty`, but it does not carry fit bounds, bound provenance, or
the pre-fit uncertainty snapshot needed by undo. Those fields are
required for Bayesian plot ranges, pair-plot bound annotations, and
clean fit rollback after project reload.

Fields:

- `param_unique_name`
- `fit_min`
- `fit_max`
- `fit_bounds_uncertainty_multiplier`
- `start_value`
- `start_uncertainty`

`fit_min` and `fit_max` are required for restored Bayesian plotting.
`fit_bounds_uncertainty_multiplier` is required if restored plots should
preserve the uncertainty-derived bound annotation exactly. `start_value`
and `start_uncertainty` are required for clean cross-session undo. If
omitted, restored fit reports may show `N/A` for `start` and `change`,
and undo may need to clear uncertainty as a compatibility fallback.

#### 11.2 `_bayesian_result` single item

Stores one saved Bayesian result header with these fields:

- `schema_version`
- `sampler_name`
- `point_estimate_name`
- `success`
- `sampler_completed`
- `reduced_chi_square`
- `fitting_time`
- `best_log_posterior`
- `credible_interval_inner`
- `credible_interval_outer`
- `has_posterior_samples`
- `has_posterior_predictive`
- `sidecar_file`

For the current design, `point_estimate_name` is always `map`.

#### 11.3 `_bayesian_sampler` single item

Stores resolved sampler settings actually used for the run:

- `steps`
- `burn`
- `thin`
- `pop`
- `parallel`
- `init`
- `random_seed`

This persists the existing runtime `sampler_settings` in an explicit,
schema-driven form rather than as an open-ended key/value mapping.

#### 11.4 `_bayesian_convergence` single item

Stores top-level convergence and shape metadata:

- `converged`
- `max_r_hat`
- `min_ess_bulk`
- `n_draws`
- `n_chains`
- `n_parameters`

Per-parameter `r_hat` and `ess_bulk` remain in the parameter summary
loop described below.

#### 11.5 `_bayesian_parameter_posterior` loop

Stores one canonical posterior summary row per sampled parameter. These
rows are the source used to rebuild `parameter.posterior` on load.

Fields:

- `order_index`
- `unique_name`
- `display_name`
- `map_estimate`
- `median`
- `uncertainty`
- `interval_68_lower`
- `interval_68_upper`
- `interval_95_lower`
- `interval_95_upper`
- `ess_bulk`
- `r_hat`

`order_index` defines the parameter order used by posterior sample
columns in the sidecar arrays.

#### 11.6 `_bayesian_predictive_dataset` loop

Stores one manifest row per persisted posterior predictive summary.

Fields:

- `experiment_name`
- `x_axis_name`
- `x_path`
- `map_prediction_path`
- `lower_95_path`
- `upper_95_path`
- `lower_68_path`
- `upper_68_path`
- `draws_path`
- `n_x`
- `n_draws_cached`

This loop tells the loader which arrays to read from the sidecar file
for each experiment-level predictive summary.

#### 11.7 Suggested CIF fragments

The active parameter value remains in the structure or experiment CIF as
it does today, for example:

```cif
_atom_site_U_iso_or_equiv 0.0319(21)
```

Analysis-owned fit-control and Bayesian metadata then lives in
`analysis/analysis.cif`, for example:

```cif
_fit.minimizer_type "bumps (dream)"
_fit.mode single

loop_
_fit_parameter.param_unique_name
_fit_parameter.fit_min
_fit_parameter.fit_max
_fit_parameter.fit_bounds_uncertainty_multiplier
_fit_parameter.start_value
_fit_parameter.start_uncertainty
cosio.atom_site.Co1.adp_iso 0.0000 0.1200 4.0 0.0312 0.0021
cosio.atom_site.Co2.adp_iso 0.0000 0.1200 4.0 0.0312 0.0021

_bayesian_result.schema_version 1
_bayesian_result.sampler_name dream
_bayesian_result.point_estimate_name map
_bayesian_result.success yes
_bayesian_result.sampler_completed yes
_bayesian_result.reduced_chi_square 1.031
_bayesian_result.fitting_time 82.4
_bayesian_result.best_log_posterior -1542.77
_bayesian_result.credible_interval_inner 0.68
_bayesian_result.credible_interval_outer 0.95
_bayesian_result.has_posterior_samples yes
_bayesian_result.has_posterior_predictive yes
_bayesian_result.sidecar_file "bayesian_data.h5"

_bayesian_sampler.steps 3000
_bayesian_sampler.burn 600
_bayesian_sampler.thin 1
_bayesian_sampler.pop 20
_bayesian_sampler.parallel 0
_bayesian_sampler.init lhs
_bayesian_sampler.random_seed 12345

_bayesian_convergence.converged yes
_bayesian_convergence.max_r_hat 1.01
_bayesian_convergence.min_ess_bulk 812.4
_bayesian_convergence.n_draws 2400
_bayesian_convergence.n_chains 20
_bayesian_convergence.n_parameters 2

loop_
_bayesian_parameter_posterior.order_index
_bayesian_parameter_posterior.unique_name
_bayesian_parameter_posterior.display_name
_bayesian_parameter_posterior.map_estimate
_bayesian_parameter_posterior.median
_bayesian_parameter_posterior.uncertainty
_bayesian_parameter_posterior.interval_68_lower
_bayesian_parameter_posterior.interval_68_upper
_bayesian_parameter_posterior.interval_95_lower
_bayesian_parameter_posterior.interval_95_upper
_bayesian_parameter_posterior.ess_bulk
_bayesian_parameter_posterior.r_hat
0 cosio.atom_site.Co1.adp_iso "Co1 ADP" 0.0319 0.0317 0.0021 0.0298 0.0339 0.0278 0.0361 812.4 1.01
1 cosio.atom_site.Co2.adp_iso "Co2 ADP" 0.0320 0.0318 0.0020 0.0300 0.0338 0.0281 0.0359 830.7 1.00

loop_
_bayesian_predictive_dataset.experiment_name
_bayesian_predictive_dataset.x_axis_name
_bayesian_predictive_dataset.x_path
_bayesian_predictive_dataset.map_prediction_path
_bayesian_predictive_dataset.lower_95_path
_bayesian_predictive_dataset.upper_95_path
_bayesian_predictive_dataset.lower_68_path
_bayesian_predictive_dataset.upper_68_path
_bayesian_predictive_dataset.draws_path
_bayesian_predictive_dataset.n_x
_bayesian_predictive_dataset.n_draws_cached
hrpt ttheta /predictive/hrpt/x /predictive/hrpt/map_prediction /predictive/hrpt/lower_95 /predictive/hrpt/upper_95 /predictive/hrpt/lower_68 /predictive/hrpt/upper_68 /predictive/hrpt/draws 2500 200
```

### 12. Persist bulk arrays in `analysis/bayesian_data.h5`

Large numerical arrays are stored outside CIF text in a single sidecar
file:

- `analysis/bayesian_data.h5`

The sidecar is optional. Summary-only restore remains valid without it.

HDF5 is selected instead of NPZ because the persisted Bayesian payload
is a structured collection of named datasets with heterogeneous shapes,
optional groups, and potentially large predictive arrays. HDF5 provides
explicit hierarchical storage, dataset metadata, selective reads, and a
better long-term path for compression or chunking. NPZ is simpler, but
it is flatter and less suitable once the saved Bayesian state grows
beyond a small set of arrays.

#### 12.1 Required core HDF5 dataset paths when posterior samples are saved

- `posterior_parameter_samples`
- `posterior_log_posterior`
- `posterior_draw_index`

Expected array shapes:

- `posterior_parameter_samples`: `(n_draws, n_chains, n_parameters)`
- `posterior_log_posterior`: `(n_draws, n_chains)` when available
- `posterior_draw_index`: `(n_draws,)` when available

If `posterior_log_posterior` or `posterior_draw_index` are unavailable,
their corresponding header flags remain false and the arrays may be
omitted.

#### 12.2 Predictive dataset keys

Posterior predictive arrays are addressed through the
`_bayesian_predictive_dataset` manifest rather than inferred from file
ordering.

Recommended HDF5 dataset naming is:

- `predictive__<experiment>__x`
- `predictive__<experiment>__map_prediction`
- `predictive__<experiment>__lower_95`
- `predictive__<experiment>__upper_95`
- `predictive__<experiment>__lower_68`
- `predictive__<experiment>__upper_68`
- `predictive__<experiment>__draws`

The manifest, not the naming convention, is the source of truth.

Recommended HDF5 group layout is:

- `/posterior/parameter_samples`
- `/posterior/log_posterior`
- `/posterior/draw_index`
- `/predictive/<experiment>/x`
- `/predictive/<experiment>/map_prediction`
- `/predictive/<experiment>/lower_95`
- `/predictive/<experiment>/upper_95`
- `/predictive/<experiment>/lower_68`
- `/predictive/<experiment>/upper_68`
- `/predictive/<experiment>/draws`

The manifest remains the canonical mapping used by the loader, so this
layout is recommended rather than mandatory.

#### 12.3 What is not persisted in the sidecar

Do not persist backend-specific runtime objects such as `engine_result`,
the DREAM driver, or ArviZ `InferenceData`.

Those objects can be rebuilt from canonical saved arrays when needed, or
left unavailable after load.

### 13. Restore flow and partial-availability policy

Persistence must support both full and partial restore.

#### 13.1 Save flow

When `Project.save()` sees `analysis.fit_results` as a
`BayesianFitResults` instance:

1. It writes standard analysis configuration to `analysis/analysis.cif`.
2. It appends `_fit_parameter`, `_bayesian_result`, `_bayesian_sampler`,
   `_bayesian_convergence`, and `_bayesian_parameter_posterior`.
3. If posterior predictive summaries are available, it also writes the
   `_bayesian_predictive_dataset` manifest.
4. If posterior sample arrays or predictive arrays are available, it
   writes `analysis/bayesian_data.h5`.

#### 13.2 Load flow

When `Project.load()` restores `analysis/analysis.cif`:

1. Standard analysis configuration is restored first.
2. If `_fit_parameter` is present, fit bounds, bound provenance, and
   optional pre-fit scalar snapshots are restored by matching
   `param_unique_name` to live parameters.
3. If Bayesian categories are present, a lightweight
   `BayesianFitResults` instance is rebuilt from persisted metadata and
   parameter summary rows.
4. `parameter.posterior` is rebuilt by matching summary rows to live
   parameters via `unique_name`.
5. `parameter.value` and `parameter.uncertainty` continue to come from
   the normal project serialization path; Bayesian restore does not
   overwrite them.
6. If `analysis/bayesian_data.h5` exists and matches the manifest,
   `posterior_samples` and `posterior_predictive` are restored.
7. If the sidecar is missing or incomplete, the restore degrades to
   summary-only mode without failing the whole project load.

#### 13.3 Partial restore behavior

The chosen partial-restore policy is:

- `parameter.posterior` and `display.fit_results()` remain available
  from saved metadata and summaries.
- Bayesian-only plots requiring canonical posterior arrays remain
  unavailable unless those arrays were restored successfully.
- Missing sidecar data should produce a clear warning, not a hard load
  failure.

Example user access after load:

```python
project = Project.load('/path/to/project')

param = project.phases['lbco'].cell.length_a
posterior = param.posterior

if posterior is not None:
    print(posterior.map_estimate)
    print(posterior.uncertainty)
    print(posterior.interval_68)

project.analysis.display.fit_results()
```

Example plotting behavior after load:

```python
# Works with summary-only restore
project.analysis.display.fit_results()

# Requires canonical posterior arrays from analysis/bayesian_data.h5
project.display.plotter.plot_posterior_pairs()
project.display.plotter.plot_param_distribution(param)
project.display.plotter.plot_posterior_predictive(expt_name='hrpt')
```

### 14. Keep parameter posterior data rebuilt, not duplicated

`parameter.posterior` is always rebuilt from the canonical
`_bayesian_parameter_posterior` loop in `analysis/analysis.cif`.

Do not serialize posterior summaries again inside each parameter's own
CIF representation. Duplicating the same posterior summary data across
structure and experiment files would create multiple sources of truth.

## Consequences

### Positive

- Users get a compact Bayesian overview directly from each parameter.
- The parameter API stays tidy because posterior helpers are grouped
  into one optional object rather than many flat attributes.
- `uncertainty` and posterior metadata become clearly fit-owned rather
  than mixed user-editable and fit-editable state.
- `analysis.fit_results` remains the canonical source for full Bayesian
  state.
- `analysis/analysis.cif` becomes the home for fit-control metadata that
  does not belong in structure or experiment CIF files.
- Bayesian save/load gains a clear split between text metadata in
  `analysis/analysis.cif` and bulk numerical arrays in
  `analysis/bayesian_data.h5`.
- Partial restore works for summaries even when full posterior arrays
  are absent.
- The design matches the current rule that `value` is the only active
  scalar used for calculations.

### Trade-offs

- `GenericParameter` now holds an optional reference to analysis-derived
  metadata.
- Any manual user edit invalidates fit-derived metadata more eagerly
  than today.
- `uncertainty` becomes a read-only public property, so fit-result
  application code must be updated to use dedicated internal helpers
  rather than a mix of `_set_value_from_minimizer(...)` and public
  uncertainty assignment.
- Bayesian persistence now spans both CIF metadata and a binary sidecar,
  so save/load code must validate consistency between the two.

## Layering and Ownership

To keep `core/` free of Bayesian computations, the parameter object must
not compute posterior summaries itself.

The summary object is created by posterior-capable fit code and then
attached to parameters as already-computed metadata. `core/variable.py`
should avoid eager runtime imports of Bayesian helper modules; a
type-only import is acceptable.

## Deferred Work

This ADR now defines persistence for one canonical saved Bayesian run.

It still defers:

- support for multiple saved Bayesian runs per project
- plot-ready cache layers beyond canonical posterior and predictive data
- persistence-time compression or chunking strategies beyond the first
  HDF5 sidecar implementation
- persistence for future posterior-capable minimizers beyond DREAM
- enabling currently unsupported single-crystal predictive draw plots

## Implementation Notes

- The first implementation should only populate `parameter.posterior`
  for DREAM.
- Existing `PosteriorParameterSummary` instances should be reused rather
  than copied into a second summary type unless implementation reveals a
  concrete layering problem that cannot be resolved cleanly.
- `parameter.posterior` should always be rebuilt from restored canonical
  Bayesian data rather than serialized redundantly at parameter level.
- The sidecar reader and writer should be isolated behind explicit
  serializer helpers instead of being implemented inline in
  `Project.save()` and `Project.load()`.

## Chosen Defaults

- `parameter.value` remains committed to MAP after posterior fits.
- If a project is loaded without full posterior arrays, restoring only
  `parameter.posterior` is acceptable for table display and parameter
  inspection.
- Posterior plotting remains unavailable unless the canonical Bayesian
  containers needed by those plots are also restored.
