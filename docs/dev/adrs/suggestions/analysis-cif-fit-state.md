# ADR: Analysis CIF Fit State

**Status:** Proposed  
**Date:** 2026-05-13

## Context

`analysis/analysis.cif` currently persists analysis configuration such
as `_fit.minimizer_type`, `_fit.mode`, aliases, constraints, and
joint-fit weights. It does not persist analysis-owned fit state such as
fit bounds, bound provenance, pre-fit scalar snapshots, or latest
fit-status metadata.

At the same time, parameter CIF serialization already carries the
committed parameter `value`, the current `free` state, and the current
`uncertainty` via CIF bracket notation. That data belongs to the model
and should remain in structure or experiment CIF files.

The missing piece is analysis-owned fit state:

- fit controls that apply to parameters during fitting but are not part
  of the model itself
- latest fit-status metadata shown by `display.fit_results()`
- deterministic and Bayesian fit metadata that should survive project
  reloads and command-line workflows

This separation matters because:

- Bayesian plotting after reload needs `fit_min`, `fit_max`, and bound
  provenance even when raw posterior arrays are absent
- command-line users need a saved pre-fit starting state to recover from
  a poor minimization run
- `analysis.fit_results` already changes by fit type, but its persisted
  projection should have a stable analysis-owned home

The accepted runtime-fit-results ADR describes fit results as
runtime-only. This ADR proposes a narrower persisted projection of the
latest fit state, not a direct dump of backend runtime objects.

## Decision

### 1. `analysis/analysis.cif` becomes the home of analysis-owned fit state

The analysis CIF file will persist:

- fit configuration
- aliases and constraints
- joint-fit weights
- per-parameter fit controls owned by analysis
- latest fit-status metadata common to deterministic and Bayesian fits
- fit-type-specific extensions defined in separate ADRs

Committed parameter values remain in structure or experiment CIF files.
They are not duplicated into `analysis/analysis.cif`.

### 2. Add a real `_fit_parameter` loop

Introduce a new analysis-owned loop category:

```cif
loop_
_fit_parameter.param_unique_name
_fit_parameter.fit_min
_fit_parameter.fit_max
_fit_parameter.fit_bounds_uncertainty_multiplier
_fit_parameter.start_value
_fit_parameter.start_uncertainty
cosio.atom_site.Co1.adp_iso 0.0000 0.1200 4.0 0.0312 0.0021
cosio.atom_site.Co2.adp_iso 0.0000 0.1200 4.0 0.0312 0.0021
```

Fields:

- `param_unique_name`
- `fit_min`
- `fit_max`
- `fit_bounds_uncertainty_multiplier`
- `start_value`
- `start_uncertainty`

Rationale:

- `fit_min` and `fit_max` are required to restore deterministic and
  Bayesian fit controls faithfully.
- `fit_bounds_uncertainty_multiplier` preserves the provenance of
  uncertainty-derived bounds for restored Bayesian plot annotations.
- `start_value` and `start_uncertainty` capture the last committed
  pre-fit scalar state and enable fit recovery workflows, especially in
  command-line usage.
- `start_uncertainty` preserves a user-visible pre-fit uncertainty
  instead of treating it as disposable fit residue.

### 3. Add a generic `_fit_result` single-item category

Persist the latest fit-status metadata shared across fit types in a
single analysis-owned category:

- `result_kind`
- `success`
- `message`
- `iterations`
- `fitting_time`
- `reduced_chi_square`

Suggested CIF fragment:

```cif
_fit_result.result_kind deterministic
_fit_result.success yes
_fit_result.message "Fit converged"
_fit_result.iterations 37
_fit_result.fitting_time 1.82
_fit_result.reduced_chi_square 1.031
```

`result_kind` distinguishes the latest persisted fit projection, for
example `deterministic` or `bayesian`.

### 4. Persist only stable fit-status fields here

The `_fit_result` category is for generic status fields that are stable
across engines and already belong to the result model.

It should not persist backend runtime objects or arbitrary engine
payloads.

Metrics such as R-factors shown by `display.fit_results()` are derived
from observed and calculated data and can be recomputed after load when
needed. They do not need to be part of the first persisted fit-state
schema.

### 5. Fit-type-specific extensions build on this ADR

This ADR defines the common `analysis.cif` contract for deterministic
and Bayesian fitting.

Fit-type-specific extensions are layered on top:

- Bayesian persistence extends this with `_bayesian_*` categories and an
  HDF5 sidecar, as described in `parameter-posterior-summary.md`.
- Future fit-specific summaries should follow the same pattern: generic
  shared fields in `_fit_result`, specialized fields in separate
  categories.

### 6. Restore order is analysis-first, fit-type-second

Load order should be:

1. standard analysis configuration
2. aliases and constraints
3. joint-fit weights
4. `_fit_parameter`
5. `_fit_result`
6. fit-type-specific extensions such as `_bayesian_*`

This ensures that generic fit controls are available before restoring
specialized fit summaries.

### 7. Suggested full `analysis.cif` example

```cif
_fit.minimizer_type "bumps (dream)"
_fit.mode single

loop_
_alias.label
_alias.param_unique_name
biso_Co1 cosio.atom_site.Co1.adp_iso
biso_Co2 cosio.atom_site.Co2.adp_iso

loop_
_constraint.expression
"biso_Co2 = biso_Co1"

loop_
_fit_parameter.param_unique_name
_fit_parameter.fit_min
_fit_parameter.fit_max
_fit_parameter.fit_bounds_uncertainty_multiplier
_fit_parameter.start_value
_fit_parameter.start_uncertainty
cosio.atom_site.Co1.adp_iso 0.0000 0.1200 4.0 0.0312 0.0021
cosio.atom_site.Co2.adp_iso 0.0000 0.1200 4.0 0.0312 0.0021

_fit_result.result_kind bayesian
_fit_result.success yes
_fit_result.message "Sampler converged"
_fit_result.iterations 3000
_fit_result.fitting_time 82.4
_fit_result.reduced_chi_square 1.031

# Bayesian-specific extension categories follow here.
```

## Consequences

### Positive

- `analysis.cif` becomes the single analysis-owned source of fit state.
- Deterministic and Bayesian persistence share one common base schema.
- Fit bounds, bound provenance, and start values survive project
  reloads.
- Command-line workflows gain a persisted pre-fit starting state.

### Trade-offs

- The runtime fit-results ADR must be updated because fit state is no
  longer entirely runtime-only.
- Analysis persistence becomes more stateful and must be kept in sync
  with live parameter objects.
- Some existing serializer assumptions will need refactoring so that
  `analysis.cif` owns fit metadata rather than individual parameters.

## Deferred Work

- Bayesian-specific categories and HDF5 sidecar details remain in
  `parameter-posterior-summary.md`.
- Undo semantics for `start_value` and `start_uncertainty` are defined
  in a separate ADR.
- Correlation-matrix persistence is defined in a separate ADR.
