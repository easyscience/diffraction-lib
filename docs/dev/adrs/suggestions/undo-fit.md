# ADR: Undo Fit

**Status:** Proposed  
**Date:** 2026-05-18

## Status Note

The rollback anchors described here are already persisted and restored.
Current code saves `_fit_parameter.start_value` and
`_fit_parameter.start_uncertainty` in `analysis/analysis.cif`, and the
CLI already reserves `PROJECT_DIR undo`, but no rollback operation is
implemented yet.

## Context

The accepted fit-state persistence design now stores
`_fit_parameter.start_value` and `_fit_parameter.start_uncertainty` in
`analysis/analysis.cif`. Those fields capture the last committed pre-fit
scalar state for each fitted parameter and are the essential rollback
anchors for any undo feature.

This branch also introduced project-first CLI routing and reserved a
top-level `undo` command shape, but the command is still only a
placeholder. The actual rollback semantics are still undecided.

Parameter-level posterior access remains a separate proposal. Undo must
not depend on `parameter.posterior` existing.

## Decision

### 1. Add an analysis-owned `undo_fit()` operation

The rollback operation belongs on `Analysis`:

```python
project.analysis.undo_fit()
```

`Analysis` owns fit execution, fit metadata, and the persisted fit-state
projection, so it is the correct public owner.

### 2. Initial undo scope is scalar rollback plus fit-state clear

The first undo implementation restores each fitted parameter's saved
pre-fit scalar state and clears fit-derived state that belongs only to
the discarded fit.

After `undo_fit()`:

- `parameter.value` is restored from `_fit_parameter.start_value`
- `parameter.uncertainty` is restored from
  `_fit_parameter.start_uncertainty`
- `analysis.fit_results` is cleared
- persisted fit-state summaries and Bayesian caches for the discarded
  fit are cleared

If a future `parameter.posterior` API exists, undo should clear that
projection too. It is not a prerequisite for the initial implementation.

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

These belong to analysis configuration, not fit output.

### 4. Undo is single-level for now

Only the latest saved pre-fit snapshot is addressable. Multi-level undo
and redo require a dedicated snapshot-history design and remain
deferred.

### 5. CLI exposure follows the project-first command style

The command-line surface should follow the current CLI style:

```bash
python -m easydiffraction PROJECT_DIR undo
```

This command should:

- load the saved project from `PROJECT_DIR`
- execute `project.analysis.undo_fit()`
- save the recovered state back to the same project directory by default
- support `--dry` to preview the rollback without overwriting files
- fail with a clear non-zero exit status when no usable undo snapshot is
  available

Compatibility aliases may remain if the CLI supports them, but the
project-first form is the canonical user-facing syntax.

## Consequences

### Positive

- The accepted fit-state persistence already provides the minimum saved
  anchors required for cross-session undo.
- Users gain a predictable recovery path after a poor fit without
  needing full historical fit snapshots.
- The feature aligns naturally with saved-project workflows in both
  Python and the CLI.

### Trade-offs

- Undo restores visible scalar parameter state, not a full historical
  runtime result object.
- Older saved projects may still need the uncertainty-clearing fallback.
- Multi-level undo remains unsupported.

## Deferred Work

- exact restoration of previous posterior-derived displays beyond the
  scalar rollback anchors
- multi-level undo and redo
- confirmation or preview UX beyond `--dry`
- any dependency on a future `parameter.posterior` API
