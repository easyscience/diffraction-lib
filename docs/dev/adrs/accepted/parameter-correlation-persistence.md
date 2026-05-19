# ADR: Parameter Correlation Persistence

## Status

Accepted current design.

## Date

2026-05-19

## Group

Analysis and fitting.

## Context

`plot_param_correlations()` can visualize either deterministic parameter
correlations derived from engine covariance or Bayesian correlations
derived from posterior samples.

Reloaded projects still need correlation heatmaps even when the raw
runtime covariance or posterior arrays are unavailable. The broader
fit-state layout is defined in `analysis-cif-fit-state.md`; this ADR
records the narrower persisted correlation-summary projection within
that accepted design.

Correlation data is analysis-owned derived state, not model state. It
therefore belongs in `analysis/analysis.cif`, not in structure or
experiment CIF files.

## Decision

Persist pairwise parameter correlations in `_fit_parameter_correlation`
rows inside `analysis/analysis.cif`.

### Correlation summary schema

Store one row per unique parameter pair with these fields:

- `id`
- `source_kind`
- `param_unique_name_i`
- `param_unique_name_j`
- `correlation`

Example:

```cif
loop_
_fit_parameter_correlation.id
_fit_parameter_correlation.source_kind
_fit_parameter_correlation.param_unique_name_i
_fit_parameter_correlation.param_unique_name_j
_fit_parameter_correlation.correlation
1 posterior cosio.atom_site.Co1.adp_iso cosio.atom_site.Co2.adp_iso 0.87
```

Normalize each row to the upper triangle excluding the diagonal.
`param_unique_name_i` and `param_unique_name_j` use a stable ordering so
only one unordered pair is stored. The diagonal is omitted because it is
always `1.0` and can be rebuilt on load.

Use the same loop for deterministic and Bayesian projections. The source
is carried by `source_kind`, currently `deterministic` or `posterior`.

### Summary-only role

`_fit_parameter_correlation` is a persisted summary. It does not replace
posterior samples, posterior pair densities, or covariance matrices.

This summary is enough to restore correlation heatmaps. It is not enough
to restore richer pair-plot density surfaces or covariance-specific
workflows.

### Restore behavior

On load, restore `_fit_parameter_correlation` rows into an analysis-
owned correlation collection.

When runtime covariance or posterior samples are unavailable,
`project.display.plotter.plot_param_correlations()` may rebuild a square
correlation matrix from the persisted rows and the restored fit-result
parameter ordering.

### Relation to the broader fit-state ADR

`analysis-cif-fit-state.md` remains the source of truth for the full
fit-state projection, save/load ordering, and Bayesian sidecar layout.
This ADR records the implemented correlation-specific piece of that
accepted design.

## Consequences

- Deterministic and Bayesian correlation summaries survive reload.
- Correlation heatmaps no longer depend entirely on runtime-only data.
- The schema stays compact and fit-type-agnostic.
- Posterior pair plots and covariance-specific workflows still need
  richer runtime or persisted data.

## Deferred Work

- optional storage of covariance matrices in addition to correlations
- multiple named correlation sources for the same saved project
- full correlation restoration for pair-plot density surfaces
