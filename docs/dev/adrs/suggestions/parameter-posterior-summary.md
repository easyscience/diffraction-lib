# ADR: Parameter-Level Posterior Projection

**Status:** Proposed **Date:** 2026-05-13

## Context

`GenericParameter` already stores fit-adjacent helper data such as
`uncertainty`, `fit_min`, and `fit_max`, while `value` remains the
single scalar used by calculations.

Bayesian DREAM currently keeps posterior state only on
`analysis.fit_results` via `BayesianFitResults`, including
`posterior_samples`, `posterior_parameter_summaries`,
`posterior_predictive`, diagnostics, and sampler settings. The accepted
runtime-fit-results ADR describes this state as runtime-only and not
serialized unless a narrower persistence ADR defines a saved projection.

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
`best_sample_value`, `interval_95`, `r_hat`, or `ess_bulk`.

Instead, the parameter-level projection reuses the existing
`PosteriorParameterSummary` object already produced for
`BayesianFitResults`. This keeps one grouped summary shape for display,
inspection, and restore from persisted analysis state.

The summary object currently provides the right level of detail:

- `best_sample_value`
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

- `best_sample_value` -> `Best posterior sample`
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
  best_sample_value = param.posterior.best_sample_value
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

### 8. Commit best posterior sample to `parameter.value` after Bayesian fits

After a posterior-capable fit, `parameter.value` is committed from the
best posterior sample.

The best posterior sample is chosen because it is a coherent joint point
estimate across all free parameters. Marginal medians remain available
on `parameter.posterior`, but they are summary data rather than the
active live model state.

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

### 10. Rebuild posterior from analysis-level state

Canonical Bayesian state is owned by `analysis.fit_results`, not by
individual parameters. The saved fit-state format and restore order are
defined in `analysis-cif-fit-state.md`.

`parameter.posterior` is never serialized as a per-parameter property.
It is rebuilt from the analysis-level saved result projection when that
projection is available.

Two restore levels matter for the parameter API:

- summary-only restore can populate `parameter.posterior` and fit-result
  tables
- full restore can also support posterior plots and predictive plots

If the saved project has no analysis-level posterior summary for a
parameter, `parameter.posterior` remains `None`.

Example user access after load:

```python
project = Project.load('/path/to/project')

param = project.phases['lbco'].cell.length_a
posterior = param.posterior

if posterior is not None:
  print(posterior.best_sample_value)
  print(posterior.uncertainty)
  print(posterior.interval_68)

project.analysis.display.fit_results()
```

Posterior plot availability after load follows the fit-state restore
level defined in `analysis-cif-fit-state.md`.

### 11. Keep parameter posterior data rebuilt, not duplicated

`parameter.posterior` is always rebuilt from analysis-level fit state.

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
- `analysis.fit_results` remains the canonical runtime source for full
  Bayesian state.
- Partial restore can still expose parameter summaries when
  analysis-level saved state contains them.
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

## Layering and Ownership

To keep `core/` free of Bayesian computations, the parameter object must
not compute posterior summaries itself.

The summary object is created by posterior-capable fit code and then
attached to parameters as already-computed metadata. `core/variable.py`
should avoid eager runtime imports of Bayesian helper modules; a
type-only import is acceptable.

## Deferred Work

This ADR defines the parameter-level posterior projection. It defers:

- persistence for future posterior-capable minimizers beyond DREAM
- enabling currently unsupported single-crystal predictive draw plots

## Implementation Notes

- The first implementation should only populate `parameter.posterior`
  for DREAM.
- Existing `PosteriorParameterSummary` instances should be reused rather
  than copied into a second summary type unless implementation reveals a
  concrete layering problem that cannot be resolved cleanly.
- `parameter.posterior` should always be rebuilt from analysis-level
  Bayesian data rather than serialized redundantly at parameter level.

## Chosen Defaults

- `parameter.value` remains committed to the best posterior sample after
  posterior fits.
- If a project is loaded with only posterior summaries, restoring
  `parameter.posterior` is acceptable for table display and parameter
  inspection.
