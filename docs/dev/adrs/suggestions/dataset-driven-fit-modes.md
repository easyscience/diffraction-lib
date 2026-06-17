# ADR: Dataset-Driven Fit Modes and Sequential Redefinition

## Status

Proposed.

## Date

2026-06-16

## Group

Analysis and fitting.

## Context

The analysis layer offers three fit modes through the `fitting_mode`
switchable category established by
[`fit-mode-categories`](accepted/fit-mode-categories.md): `single`,
`joint`, and `sequential`. In practice the mapping from these modes to
the scientist's intent is overloaded and partly broken.

The real scientific intents are:

1. **One dataset, one model** — fit a single measured pattern.
2. **Several datasets of one sample, one consistent answer** — e.g.
   neutron + x-ray of the same crystal, fit together with shared
   structure parameters.
3. **A series of the same sample, fit per point to track parameter
   evolution** — e.g. lattice parameter vs temperature.
4. **Compare different models** — handled by separate projects (out of
   scope here, by project owner's decision).

Intent 3 is where the current modes break down. It is served today by
**two unrelated code paths**:

- `single` mode with **multiple loaded experiments**
  (`_fit_single_experiments`, `analysis.py`): it loops the loaded
  experiments and fits each in turn. Because the structure object is
  shared across experiments (`Fitter._collect_fit_parameters` uses
  `structures.free_parameters`), each fit starts from the previous
  experiment's refined values (an implicit carry-forward) and
  **overwrites** the shared structure. Per-experiment results are not
  retained on the structure, so plotting an earlier experiment shows the
  _last_ experiment's calculated pattern — this is **issue 85**. A
  legacy in-memory `_parameter_snapshots` store plus
  `plot_param_series_from_snapshots` exists only as a fallback for this
  path.
- `sequential` mode: fits **exactly one** loaded experiment as a
  _template_ against a **folder of files on disk**
  (`sequential_fit.data_dir` / `file_pattern`), writing per-point
  results to `analysis/results.csv` with parameter-evolution plots. A
  guard test asserts `match='exactly 1 experiment'`, so this mode
  **cannot run with two or more loaded experiments**.

So one scientific intent ("fit a series, track evolution") is split
across two names, two implementations, and one of them is buggy. This
also makes mode availability confusing: `single` is the friendly name
for the one-dataset case yet silently doubles as a multi-dataset series
fitter; `sequential` sounds general but is narrowly a folder sweep;
`joint` requires ≥2 experiments.

This ADR proposes aligning the modes to intent, driving their
availability from the number of loaded experiments, and reframing issue
85 as a correctness requirement of a redefined `sequential` mode rather
than a defect to patch in place. It extends, and partly revises,
[`fit-mode-categories`](accepted/fit-mode-categories.md).

## Decision

### 1. Compute fit-mode availability from the loaded-experiment count

`fitting_mode.show_supported()` returns only the modes that make sense
for the data currently loaded:

| Experiments loaded | Available modes         |
| ------------------ | ----------------------- |
| 0                  | — (no fitting possible) |
| 1                  | `single`                |
| ≥ 2                | `joint`, `sequential`   |

This is wired through the existing switchable-category selector
contract: `FittingMode._supported_types(filters)` (today it ignores
`filters`) consumes the experiment count and returns the valid list. The
owner does not gain any new `analysis.*` setter — the
category-owned-selector contract from
[`switchable-category-owned-selectors`](accepted/switchable-category-owned-selectors.md)
is preserved.

The choice the scientist actually makes — "fit them **together** or **in
turn**?" — therefore only appears when it is meaningful (≥2 datasets).
With one dataset there is no choice to make.

### 2. Restrict `single` to exactly one loaded experiment

`single` means "fit the one loaded dataset." It is no longer a
multi-experiment loop. This removes the `single`-with-N behaviour that
caused issue 85.

### 3. Redefine `sequential` to fit each loaded dataset in turn

`sequential` becomes: fit each of the ≥2 **loaded** experiments one
after another, **carrying the refined parameters forward** as the
starting point for the next experiment, and **retaining per-dataset
results** so each point can be re-plotted and its parameter evolution
charted.

This absorbs the old `single`-with-N behaviour (which was already an
implicit carry-forward) and makes it correct. The name matches the
behaviour: each fit is seeded by the previous one, in sequence.

Scope of the carry-forward is made precise:

- **Shared (structure) parameters** are carried forward — the refined
  values of point _i_ become the starting values for point _i+1_. This
  is the scientifically meaningful "track the model as it evolves"
  behaviour (e.g. lattice parameter across a temperature ramp).
- **Per-experiment parameters** (scale, background, instrument terms)
  are refined independently for each point and are **not** cross-applied
  between experiments.
- The series order is **deterministic**: experiments are fit in their
  project collection order — never an arbitrary or hash order. A
  configurable reverse/custom ordering is **not** part of the first
  step: the existing `reverse` flag lives on the parked `sequential_fit`
  category (Decision 5a) and has no loaded-dataset home, and this ADR
  adds no new owner-level setter or category for it. Ordering control is
  therefore deferred to the input-source follow-up; until then users
  order the series by the order in which they add experiments.

### 3a. Preconditions that make loaded experiments a valid series

`show_supported()` lists `sequential` based on experiment **count only**
(≥2), so the offered list stays predictable and explainable from what
the scientist can see. The richer preconditions are enforced at **fit
time** with specific, actionable errors rather than by silently
withholding the mode:

- **Measured data on every experiment** in the series (reuse the
  existing `_require_measured_data` guard).
- **A shared structure model**: every experiment in the series must
  reference the same structure(s); a sequential run carries _those_
  parameters forward, so a project whose experiments point at different
  structures is not a single series and is rejected with a clear error.
- **Each experiment individually fittable**: a valid calculator and a
  non-empty free-parameter set. Experiment/calculator _types_ may differ
  across points (the carry-forward acts on the shared structure), so the
  series is not constrained to one probe or instrument.
- **Stable order** as defined in Decision 3.

When any precondition fails, the error names the offending experiment
and the rule, so a scientist is never left with a mode that "is offered
but will not run" without an explanation.

### 4. Fix issue 85 as the core of the new `sequential`

A loaded-dataset `sequential` mode is only correct if it retains each
experiment's fitted parameters. Issue 85 is therefore **resolved by
construction** of this mode, not by a separate snapshot-restore patch.
The existing per-point evolution output (`results.csv` /
`plot_param_series`) becomes the shared result surface for `sequential`,
so the legacy `_parameter_snapshots` fallback can be unified into it
rather than left as dead code.

### 4a. Replay contract — re-plotting must not mutate live state

Because all loaded experiments share one live structure object,
re-applying a stored per-point parameter set to plot an earlier point is
itself a mutation. Without a rule, fixing issue 85 could introduce a new
bug: plotting point A silently changes the structure used by point B,
later calculations, `save`, and `undo`. The contract is therefore:

- **The live model is authoritative and is not perturbed by viewing.**
  After a `sequential` run the live model holds the last point's values
  (consistent with carry-forward); plotting or recomputing any point
  must leave that live state exactly as it was.
- **Per-point recomputation is scoped and self-restoring.** Applying a
  point's stored parameters happens inside a temporary context that
  captures the affected live values, computes, and restores them on exit
  (including on error). This is an internal-only, reversible apply — it
  never reaches `save` or `undo`.
- **Prefer reading over recomputing.** Where a point's calculated arrays
  can be persisted/cached alongside its parameters, plotting reads them
  directly and avoids touching the live structure at all; the scoped
  apply-then-restore is the fallback when a recompute is unavoidable.
- **`save` / `undo` operate on the live model only** and are defined to
  be independent of whatever point was last plotted.

### 5. Hide irrelevant mode categories from display; never mutate the attribute set

Mode-specific configuration categories (`joint_fit`, `sequential_fit`,
`sequential_fit_extract`) remain **eagerly instantiated** in
`Analysis.__init__` and are **always present as attributes**. What
changes is _visibility_: the existing display filter (`_help_filter`,
`analysis.py`) and serialization filter (`_serializable_categories`) are
extended so that categories irrelevant to the available modes (given the
current experiment count and active mode) are hidden from
`analysis.help()` / display and omitted from CIF.

The alternative — making `analysis.sequential_fit` literally absent when
fewer than two datasets are loaded — is rejected: it would require
dynamic class-shape mutation on every experiment add/remove, breaks
introspection and CIF restore, and conflicts with the "eager, explicit
`__init__`, no runtime class mutation" architecture in §Architecture.
Hiding from the surface gives the user the same clean experience without
the fragility.

### 5a. The folder-of-files sweep is parked for the first step

The redefined `sequential` (loaded datasets) and the existing folder
sweep cannot share the `sequential_fit` / `sequential_fit_extract`
surface at the same time: those categories model folder input
(`data_dir`, `file_pattern`, `max_workers`, `chunk_size`, `reverse`,
extraction rules) that loaded-dataset `sequential` does not read. Two
input models also cannot live under one count-gated mode, because the
folder sweep requires **exactly one** loaded template while
loaded-dataset `sequential` requires **≥2** — opposite preconditions.
The first step therefore commits to one contract instead of leaving the
surface ambiguous:

- Loaded-dataset `sequential` uses **neither** `sequential_fit` nor
  `sequential_fit_extract`.
- The folder-sweep execution path and its two categories are **retained
  in the codebase but parked**: not reachable through the `fitting_mode`
  selector in this step, hidden from the analysis display surface, and
  omitted from CIF serialization (so stale folder settings cannot
  survive under a mode that no longer reads them).
- The parked capability is restored — as an explicit input source or a
  separate `scan` mode — by the deferred input-source ADR (see Open
  Questions and Deferred Work). The new `sequential` is designed so that
  slot-in is additive, not a rewrite.

**Owner confirmation required.** Parking the folder sweep is a
**temporary removal of an existing, tested user-facing workflow** (CSV
output, extraction rules, crash recovery, parallel workers). Per
§"Change Discipline" this removal must be explicitly approved before
implementation. The documented alternative that avoids any removal is to
split the folder sweep into its own `scan` mode **now** (available when
exactly one experiment is loaded); that keeps the feature continuously
available but revises the agreed availability table by adding `scan` to
the one-dataset row (see Alternatives Considered).

### 6. Validate at fit time with clear, user-facing errors

Mode preconditions are enforced when `fit()` runs, with actionable
`ValueError` messages (matching the boundary-validation idiom already
used for measured data and joint-fit weights):

- selecting a mode invalid for the current experiment count (e.g. a
  stored `single` mode after a second dataset is loaded) → clear error
  naming the valid modes;
- `sequential` with no fittable series → clear error.

No silent auto-switching of the mode behind the user's back.

## Consequences

### Positive

- One mode per scientific intent; the only real choice (together vs in
  turn) surfaces only when ≥2 datasets are loaded.
- Issue 85 is fixed, not papered over: `sequential` retains per-dataset
  results by design.
- The `single`/`sequential` semantic overload disappears; `sequential`
  finally matches its name.
- The legacy `_parameter_snapshots` fallback is unified into the
  `results.csv` evolution surface instead of lingering as a parallel
  path.
- Availability and visibility are computed, so they track experiment
  add/remove automatically with no dynamic attribute juggling.

### Trade-offs

- Redefining `sequential` is a **behavioural change to an existing,
  tested feature**. The first step parks the folder-of-files sweep
  (Decision 5a), which is a temporary removal of a user-facing workflow
  requiring owner sign-off; its tests are reworked and its restoration
  is a tracked follow-up. The no-removal alternative (`scan` now) trades
  this off against a revised availability table.
- "Fit each loaded dataset independently from the same starting model"
  (pure independence, no carry-forward) is no longer a distinct mode
  unless carry-forward is made optional (Open Questions).
- Mode availability now depends on mutable project state (experiment
  count), so help/display output changes as data is loaded — intended,
  but a shift from static mode listing.

### Compatibility

- Project is in beta: no shims. Tutorials, tests, and CLI that rely on
  `single`-with-N or folder-based `sequential` are updated to the new
  semantics.
- CIF restore: a persisted `fitting_mode.type` that is invalid for the
  restored experiment count is kept as stored but rejected with a clear
  error at fit time (see Decision 6); it is not silently rewritten.

## Alternatives Considered

### Remove `single`-with-N entirely and delete the snapshot code

Earlier direction: restrict `single` to one dataset and **drop** the
"fit each loaded dataset" capability altogether, deleting
`_parameter_snapshots` / `plot_param_series_from_snapshots` as dead
code; multi-dataset users would use `joint` or separate projects.
Rejected because the project owner wants a per-dataset series fit for ≥2
loaded datasets — i.e. exactly the behaviour this ADR renames to
`sequential` — so the capability is kept and fixed, not removed.

### Keep folder-based `sequential`, only gate its visibility by count

Show `sequential` at ≥2 datasets while leaving it folder-based.
Rejected: it would offer a mode that immediately errors with "exactly 1
experiment," and its behaviour (sweep a disk folder) would not match the
loaded datasets the user sees.

### Split the folder sweep into a `scan` mode now

Instead of parking the folder sweep (Decision 5a), promote it to a
distinct `scan` mode in this step: `sequential_fit` /
`sequential_fit_extract` belong to `scan`, loaded-dataset `sequential`
uses neither, and the surface conflict is resolved with no feature
removal. The cost is that `scan` (needing exactly one loaded template)
appears in the **one-dataset** row alongside `single`, revising the
agreed availability table. This is the recommended fallback if the owner
declines the temporary removal in Decision 5a; the choice between "park
now, restore later" and "split into `scan` now" is the main decision the
owner must confirm.

### Gate `sequential` visibility by whether a data folder is configured

Show `sequential` only once `sequential_fit.data_dir` is set. Rejected
for discoverability: a non-programmer scientist cannot find a workflow
hidden behind a string field they do not know to set (§Project Context
favours discoverability).

### Collapse to two modes (`joint`, `sequential`) with `single` = N-of-1

Drop `single` as a name and treat one dataset as `sequential` with a
single point. Rejected for UX: `single` is the clearest label for the
common one-dataset case, even if internally it is the degenerate series.

## Open Questions

These were deliberately deferred during design and should be resolved
before or during the implementation plan.

### Long-term home of the folder-of-files sweep

Decision 5a settles the _first-step_ contract (park the folder sweep, or
— per Alternatives — split it into `scan` now). What remains open is its
**long-term** home once the first step ships:

- **Unify** it into `sequential` as an optional _input source_ (loaded
  datasets by default, a folder for large series) — likely the best
  long-term home for one mental model and one evolution output.
- Keep it as a permanent **separate** `scan` / `parametric` mode.

The new `sequential` must be designed so either path is additive, not a
rewrite. This choice, and the Decision 5a "park vs split now" call, are
the two folder-sweep decisions the owner needs to make.

### Carry-forward vs independent

Should `sequential` always seed each fit from the previous point
(carry-forward, good for smooth ramps but a bad point can poison the
next), or offer an independent variant (each from the same starting
model, unbiased and parallelisable)? Proposed default: carry-forward,
with an option to disable.

### Naming

Keep `sequential`, or choose a term that reads better to scientists for
"per-dataset series" (e.g. `series`). Proposed: keep `sequential`.

### Resume support

Resume is currently "single mode only" (`_validate_fit_request`). Define
whether the redefined `single` (one dataset) keeps resume, and whether
`sequential` supports per-point resume.

## Deferred Work

- The folder-sweep unification/retirement (see Open Questions) is out of
  scope for the first implementation; this ADR only requires that the
  new `sequential` not preclude it.
- Detailed result-file/export layout for the unified evolution output is
  governed by
  [`fit-output-files-and-data-exports`](suggestions/fit-output-files-and-data-exports.md).
