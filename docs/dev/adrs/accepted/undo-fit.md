# ADR: Undo Fit

**Status:** Accepted  
**Date:** 2026-05-18

## Context

The accepted fit-state persistence design now stores
`_fit_parameter.start_value` and `_fit_parameter.start_uncertainty` in
`analysis/analysis.cif`. Those fields capture the last committed pre-fit
scalar state for each fitted parameter and are the essential rollback
anchors for any undo feature.

This branch also introduced project-first CLI routing and reserved a
top-level `undo` command shape, but the command is still only a
placeholder. The actual rollback semantics are still undecided.

Parameter-level posterior summaries are now first-class on the live
`Parameter` object (see
[`minimizer-category-consolidation.md`](../accepted/minimizer-category-consolidation.md)
and the `_posterior` slot on `core.variable.Parameter`). Undo must clear
that summary for every fitted parameter. Saved projects that predate the
posterior slot persist no posterior data, so clearing it is a silent
no-op for them — undo does not depend on any specific
posterior-persistence schema.

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
- `parameter.posterior` is cleared on every fitted parameter (was
  populated by Bayesian fits; deterministic fits already carry `None`,
  so undo is a no-op for that field there)
- `analysis.fit_results` is cleared
- `_fit_result.*` is cleared — purely fit-derived (R-factors,
  goodness-of-fit, iteration counts, …); no user-owned data lives here
- `_fit_parameter_correlations` is cleared — purely fit-derived
- `_fit_parameter` rows are **preserved**. The collection carries both
  user-owned fit controls (`fit_min`, `fit_max`,
  `bounds_uncertainty_multiplier`) and the rollback anchors
  themselves (`start_value`, `start_uncertainty`). Clearing the whole
  collection — which is what `Analysis._clear_persisted_fit_state()`
  does at the start of a new fit — would silently drop the user's bounds
  and erase the anchors needed for idempotence (§6). Undo therefore
  leaves these rows in place; the next fit rewrites them via
  `_capture_fit_parameter_state()`.
- `analysis/results.h5` is cleared in memory only: the
  `Analysis._persisted_fit_state_sidecar` dict is reset to empty. All
  canonical groups (`/posterior`, `/distribution_cache`, `/pair_cache`,
  `/predictive`, plus `/emcee_chain` for emcee fits) belong to the
  discarded fit, so the next save writes an empty sidecar and truncates
  the file. This is the same truncation that runs at the start of a new
  fit — see
  [`minimizer-category-consolidation.md`](../accepted/minimizer-category-consolidation.md)
  §4.

The sequential history file `analysis/results.csv` is **not** touched by
undo. Sequential fits record one row per swept row, accumulated across
many fits; "the most recent fit" has no unique row to roll back.
Sequential rollback is deferred.

**Disk side-effects.** `undo_fit()` mutates in-memory state only —
parameter values and uncertainties, `analysis.fit_results`, the
posterior summary on each fitted `Parameter`, the persisted-fit-state
result categories, and the `_persisted_fit_state_sidecar` dict. No CIF
file or HDF5 sidecar is rewritten until `project.save()` runs. This
separation is what makes the CLI `--dry` flag (§5) implementable via the
same public operation: call `undo_fit()`, skip the save.

**Persistence and load contract.** Preserving `_fit_parameter` rows in
memory is not enough on its own: today the analysis CIF save side gates
all three persisted-fit-state categories (`_fit_parameter`,
`_fit_result`, `_fit_parameter_correlations`) together on
`Analysis._has_persisted_fit_state()`
(`src/easydiffraction/analysis/analysis.py` around lines 1025-1027 and
1482-1500), and the load side uses any one of `_fit_result.result_kind`,
the `_fit_parameter` loop, or the `_fit_parameter_correlation` loop as
the "fit-state is present" marker
(`src/easydiffraction/io/cif/serialize.py`
`_has_persisted_fit_state_sections` around lines 580-590). Under that
coupling, an undo+save+reload cycle would re-trigger
`_restore_persisted_fit_state()` because the preserved `_fit_parameter`
rows still satisfy the loop marker, the lazy `fit_results` rebuild path
at `src/easydiffraction/analysis/analysis.py` lines 421-425 would
fabricate a stale or empty `FitResults`, and idempotent no-op detection
(§6) would never fire because `analysis.fit_results` would be non-`None`
again.

The persistence layer must therefore split this single gate into two
independent ones:

- **`_fit_parameter` rows** carry user-owned bounds and rollback
  anchors. They are written to `analysis/analysis.cif` whenever any rows
  exist, and they are read back on load whenever the loop is present in
  the CIF — both **independent of** any fit-result presence flag.
- **`_fit_result.*` and `_fit_parameter_correlations`** describe a
  committed fit-result. They are written only when a fit-result is
  currently present (after a successful fit and before any undo) and
  read back only when `_fit_result.result_kind` is present in the CIF.
- **`_fit_result.result_kind`** is the canonical "fit-result is present"
  marker on disk. The `_fit_parameter` loop and the
  `_fit_parameter_correlation` loop no longer count toward that
  decision. `Analysis._has_persisted_fit_state()` is set true on load
  iff `_fit_result.result_kind` is present in the CIF.

After `undo_fit()` + `project.save()`, the saved CIF therefore carries
`_fit_parameter` rows (bounds and anchors), no `_fit_result.*`, and no
`_fit_parameter_correlation` rows. After loading that project,
`Analysis._has_persisted_fit_state()` returns `False`, the lazy
`fit_results` rebuild path does not fire, and `analysis.fit_results`
returns `None`. A subsequent `undo_fit()` call lands in the no-op branch
of §6 because every fitted parameter is already at its saved
`start_value`. Idempotence therefore survives the save+reload cycle, not
just within a single session.

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
  — the rewritten `analysis/analysis.cif` reflects the rolled-back
  scalars and `analysis/results.h5` is truncated
- support `--dry` to preview the rollback without writing any file. The
  in-memory rollback still runs (so the summary numbers are real), but
  `project.save()` is skipped. This mirrors the existing
  `easydiffraction PROJECT_DIR fit --dry` semantics.
- exit cleanly (status 0) in every no-op case enumerated in §6 — a
  project that has nothing to undo is not an error condition, whether it
  has never been fit, was already undone, or predates the start-value
  persistence schema

Compatibility aliases may remain if the CLI supports them, but the
project-first form is the canonical user-facing syntax.

### 6. Error paths and idempotence

`undo_fit()` is safe to call when nothing is left to undo. The operation
never raises for "nothing to undo" — every absence-of-data case
collapses into the same no-op branch so that scripts can call `undo`
unconditionally:

- If `analysis.fit_results` is `None` **and** every fitted parameter is
  already at its saved `_fit_parameter.start_value` (within float
  tolerance), `undo_fit()` is a clean no-op. It returns without mutating
  anything and emits a short `"No fit to undo."` message at INFO level.
- If saved `_fit_parameter.start_value` rows are present but the current
  `Parameter.value` differs, `undo_fit()` performs the rollback per §2
  even when `analysis.fit_results` happens to be `None` — the persisted
  snapshot is the source of truth, not the in-memory result object.
- If no `_fit_parameter.start_value` row exists at all — either because
  the project has never been fit, or because it is a legacy project that
  predates start-value persistence — `undo_fit()` is also a clean no-op.
  There is nothing fitted to roll back, the live `Parameter` state is
  untouched, and the same `"No fit to undo."` INFO message is emitted.
  The Python operation does not raise and the CLI does not exit non-zero
  in this case (§5).
- If a saved project predates `_fit_parameter.start_uncertainty` (older
  fit-state schema but `start_value` is present), the
  uncertainty-clearing fallback from §2 applies; `parameter.uncertainty`
  is set to `None` and the fallback is logged once at INFO level.

Calling `undo_fit()` twice in a row is therefore safe: the second call
finds parameters already at their start values and `fit_results` already
cleared, and exits cleanly via the first no-op branch. The same applies
across save+reload cycles — the persistence and load contract in §2
ensures that an undone project, once reloaded, still presents
`analysis.fit_results == None` and preserved
`_fit_parameter.start_value` rows, so the second undo remains a clean
no-op rather than a fresh rollback. Scripted workflows that call `undo`
on every saved project regardless of fit history are also safe: undo is
always either a rollback or a no-op, never an error.

## Examples

### Python API

```python
import easydiffraction as ed

project = ed.Project.load('projects/lbco_hrpt')

# After a fit has been committed, the project carries refined state:
project.analysis.fit_results               # FitResults(success=True, ...)
project.structures['lbco'].cell.length_a.value          # 3.8913
project.structures['lbco'].cell.length_a.uncertainty    # 0.0001

# Roll back to the last saved pre-fit state:
project.analysis.undo_fit()

# Scalar state is now restored; the result object is gone:
project.analysis.fit_results                            # None
project.structures['lbco'].cell.length_a.value          # 3.8800 (start_value)
project.structures['lbco'].cell.length_a.uncertainty    # 0.0000 (start_uncertainty)

# Persist the rollback to disk; analysis/results.h5 is cleared too:
project.save()
```

For Bayesian fits, the same call also clears `parameter.posterior` on
every fitted parameter and truncates `analysis/results.h5` (the
`/posterior`, `/distribution_cache`, `/pair_cache`, `/predictive`, and
`/emcee_chain` groups).

### CLI

Standard invocation — loads the project, undoes the last fit, and saves
the rolled-back state back to the same directory:

```
$ python -m easydiffraction projects/lbco_hrpt undo
Undoing last fit for 'lbco_hrpt'...
✅ Restored 8 parameters to their pre-fit values.
✅ Cleared analysis.fit_results.
✅ Cleared analysis/results.h5 (Bayesian sidecar).
✅ Saved project to projects/lbco_hrpt.
```

Dry-run preview — prints the same summary without writing anything:

```
$ python -m easydiffraction projects/lbco_hrpt undo --dry
Would undo last fit for 'lbco_hrpt' (dry run, no files written):
  - 8 parameters would be restored to pre-fit values
  - analysis.fit_results would be cleared
  - analysis/results.h5 (Bayesian sidecar) would be cleared
```

No-op cases — the project has nothing to undo. All three sub-cases exit
cleanly (status 0) with the same single-line message: (a) no fit has
ever been run on the project, (b) undo was already called and persisted,
or (c) the project is a legacy project that predates
`_fit_parameter.start_value` persistence and therefore has no saved
anchors at all:

```
$ python -m easydiffraction projects/lbco_hrpt undo
No fit to undo for 'lbco_hrpt'. Project state is unchanged.
$ echo $?
0
```

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
  scalar rollback anchors (the `parameter.posterior` summary is cleared
  by undo but not _restored_ to a prior posterior state)
- multi-level undo and redo (single-level only for now per §4)
- sequential-fit row-level rollback (each row in `analysis/results.csv`
  is appended over time; "the most recent fit" has no unique row to
  address)
- confirmation or preview UX beyond `--dry` (no interactive prompt, no
  diff view of which parameters change)
