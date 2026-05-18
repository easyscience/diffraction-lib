# ADR: Parameter Correlation Persistence

**Status:** Proposed  
**Date:** 2026-05-13

## Context

`plot_param_correlations()` can currently visualize either:

- deterministic parameter correlations derived from engine covariance
- Bayesian correlations derived from posterior samples

After project reload, this correlation information is not available
unless the underlying runtime objects are rebuilt. For Bayesian fits,
full posterior samples may not always be restored. For deterministic
fits, engine covariance is typically not persisted at all.

The correlation matrix is an analysis-owned summary, not model state. It
therefore belongs in `analysis/analysis.cif`, not in structure or
experiment CIF files.

## Decision

### 1. Add a `_fit_parameter_correlation` loop category

Persist pairwise parameter correlations in a new analysis-owned loop:

- `source_kind`
- `param_unique_name_i`
- `param_unique_name_j`
- `correlation`

Suggested example:

```cif
loop_
_fit_parameter_correlation.source_kind
_fit_parameter_correlation.param_unique_name_i
_fit_parameter_correlation.param_unique_name_j
_fit_parameter_correlation.correlation
posterior cosio.atom_site.Co1.adp_iso cosio.atom_site.Co2.adp_iso 0.87
```

`source_kind` records how the correlation was obtained, for example:

- `deterministic`
- `posterior`

### 2. Store only the upper triangle excluding the diagonal

Each row stores one unordered parameter pair with
`param_unique_name_i < param_unique_name_j` in a stable ordering.

The diagonal is omitted because it is always 1.0 and can be rebuilt on
load.

This keeps the CIF loop compact while remaining lossless for the
correlation matrix.

### 3. Treat the loop as a summary, not a replacement for raw samples

For Bayesian fits, `_fit_parameter_correlation` is a persisted summary.
It does not replace posterior samples or posterior pair data.

This means:

- correlation heatmaps can be restored from the loop alone
- posterior pair plots still require posterior samples

### 4. Deterministic and Bayesian fits share the same loop schema

The same loop category is used for both deterministic and Bayesian fit
results. The distinction is carried by `source_kind`, not by separate
loop names.

### 5. Suggested restore behavior

On load:

- if `_fit_parameter_correlation` is present, correlation summaries are
  restored into a lightweight analysis-owned correlation structure
- if it is absent, correlation plots fall back to whatever live runtime
  information is available

### 6. Suggested user-facing behavior

```python
# Restored from analysis.cif when available
project.display.plotter.plot_param_correlations()
```

If only the correlation loop is restored, the user still gets the
correlation heatmap without needing raw posterior samples.

## Consequences

### Positive

- Deterministic and Bayesian correlation summaries survive reload.
- Correlation heatmaps no longer depend entirely on runtime-only data.
- The schema is compact and fit-type-agnostic.

### Trade-offs

- The correlation loop is a derived summary, so it must be kept in sync
  with the latest fit result.
- Restored correlation data is not enough for posterior pair plots or
  predictive summaries.

## Deferred Work

- optional storage of covariance matrices in addition to correlations
- multiple named correlation sources for the same saved project
- full correlation restoration for pair-plot density surfaces
