# ADR: Undo Fit

**Status:** Proposed  
**Date:** 2026-05-13

## Context

The new `_fit_parameter.start_value` and
`_fit_parameter.start_uncertainty` fields in `analysis/analysis.cif`
capture the last committed pre-fit scalar state for each fitted
parameter. This is useful when a minimization run produces a poor result
and the user wants to return to the state from immediately before the
fit.

This need is especially important in command-line workflows, where the
user may save a project after a bad fit and reopen it later expecting a
simple way to roll back to the pre-fit state.

However, these snapshots alone do not define undo semantics. The API
owner, rollback scope, and interaction with fit-derived metadata must be
explicit.

## Decision

### 1. Add an analysis-owned `undo_fit()` operation

The rollback operation belongs on `Analysis`, for example:

```python
project.analysis.undo_fit()
```

`Analysis` owns the fit lifecycle, fit metadata, and persisted
`analysis.cif` state, so it is the correct owner for this operation.

### 2. Initial undo scope is scalar rollback plus posterior clear

The first undo implementation restores each fitted parameter's saved
pre-fit scalar state and clears fit state that belongs only to the
discarded fit.

It does not attempt to restore every possible runtime detail of the
previous fit result.

After `undo_fit()`:

- `parameter.value` is restored from `_fit_parameter.start_value`
- `parameter.uncertainty` is restored from
  `_fit_parameter.start_uncertainty`
- `parameter.posterior` is cleared
- `analysis.fit_results` is cleared

This gives the user a safe, predictable return to the pre-fit visible
parameter state without pretending to restore a full historical result.

If an older saved project lacks `start_uncertainty`, clearing
`parameter.uncertainty` remains an acceptable compatibility fallback.

### 3. Undo does not roll back user configuration

The initial undo operation does not revert:

- aliases
- constraints
- fit bounds
- minimizer type
- fit mode
- joint-fit weights

These are analysis configuration, not fit output.

### 4. Undo is single-level for now

Only the latest saved pre-fit state is addressable.

The initial API does not create a stack of historical fits. Supporting
multiple undo levels would require a dedicated snapshot history design
and is deferred.

### 5. Persisted scalar snapshots are the rollback anchors

The minimum persisted state required for clean cross-session undo is the
pair of `_fit_parameter.start_value` and
`_fit_parameter.start_uncertainty` defined in
`analysis-cif-fit-state.md`.

If a parameter has no saved `start_value`, `undo_fit()` leaves that
parameter unchanged.

If a parameter has no saved `start_uncertainty`, `undo_fit()` may clear
that parameter's uncertainty as a compatibility fallback for older saved
projects.

### 6. Suggested user flow

```python
project.analysis.fit()

# Decide that the latest fit should be discarded.
project.analysis.undo_fit()

# Save the recovered state if desired.
project.save()
```

### 7. Add a top-level `undo-fit` CLI command

Because command-line recovery is one of the main motivations for this
feature, undo must also be exposed through the existing top-level CLI.

Suggested command:

```bash
python -m easydiffraction undo-fit PROJECT_DIR
```

This command should:

- load the saved project from `PROJECT_DIR`
- execute `project.analysis.undo_fit()`
- save the recovered state back to the same project directory by default
- support `--dry` to perform the rollback in memory without overwriting
  project files
- emit a clear message describing whether the latest fit snapshot was
  successfully discarded

Suggested dry-run form:

```bash
python -m easydiffraction undo-fit PROJECT_DIR --dry
```

If the project does not contain a usable undo snapshot, the command
should fail with a clear non-zero exit status instead of silently doing
nothing.

## Consequences

### Positive

- Users gain a simple recovery path after a poor fit.
- The feature works naturally with saved projects and both Python and
  command-line workflows.
- The initial scope stays small and does not require full historical fit
  snapshots.

### Trade-offs

- Undo restores pre-fit scalar parameter state, not a full historical
  `fit_results` object.
- Older saved projects that do not carry `start_uncertainty` may still
  fall back to clearing uncertainty.
- Multi-level undo remains unsupported.

## Deferred Work

- exact restoration of previous posterior-derived projections beyond the
  scalar parameter snapshot
- multi-level undo / redo
- user-facing confirmation or preview APIs
- rollback of fit-type-specific persisted summaries beyond parameter
  values
