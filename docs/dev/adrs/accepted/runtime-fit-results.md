# ADR: Runtime Fit Results

## Status

Accepted current design.

## Date

2026-05-17

## Group

Analysis and fitting.

## Context

Analysis settings are persisted in `analysis/analysis.cif`, but full fit
outputs can include large arrays, posterior samples, predictive caches,
and diagnostics. Persisting all of that by default would make project
directories heavy and would require a broader result schema.

## Decision

Persist fit configuration, not full runtime fit results.

Per-experiment calculator selection lives in experiment files. Common
fit configuration and fit-mode settings live in `analysis/analysis.cif`.
Runtime fit outputs such as `analysis.fit_results`, posterior samples,
posterior predictive arrays, summaries, and diagnostics remain
runtime-only unless a later ADR narrows the persisted projection.

## Consequences

Saved projects remain focused on reusable model and analysis settings.
Result persistence can be added later through specific ADRs without
making the initial project layout carry large runtime artifacts.
