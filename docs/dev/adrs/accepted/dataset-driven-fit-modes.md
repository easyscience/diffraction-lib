# ADR: Dataset-Driven Fit Mode Availability

## Status

Accepted.

## Date

2026-06-16

## Group

Analysis and fitting.

## Context

The analysis layer offers three fit modes through the `fitting_mode`
switchable category established by
[`fit-mode-categories`](fit-mode-categories.md): `single`,
`joint`, and `sequential`. Two problems make the current surface
confusing and partly incorrect.

**`single` is overloaded.** It is the friendly name for the one-dataset
case, but it _also_ silently loops over multiple loaded experiments,
fitting each in turn (`_fit_single_experiments`, `analysis.py`). Because
the structure object is shared across experiments
(`Fitter._collect_fit_parameters` uses `structures.free_parameters`),
each fit overwrites the shared structure and per-experiment results are
not retained — so plotting an earlier experiment shows the _last_
experiment's calculated pattern. This is **issue 85**. A legacy
in-memory `_parameter_snapshots` store plus
`plot_param_series_from_snapshots` exists only as a fallback for this
`single`-with-N path.

**The mode list is static.** All three modes are always offered, even
when a mode cannot run on the current project, and there is no signal of
which mode actually fits the loaded data:

- `joint` requires ≥2 loaded experiments (`_prepare_joint_fit`).
- `sequential` requires **exactly one** loaded experiment used as a
  _template_, swept over a **folder of files on disk**
  (`sequential_fit.data_dir` / `file_pattern`), writing per-point
  results to `analysis/results.csv` with parameter-evolution plots. A
  guard test asserts `match='exactly 1 experiment'`.

The intended `sequential` workflow is already good and should be kept as
is: load one dataset, tune the model interactively, switch to
`sequential`, point at a folder (plus a file extension), and run.

This ADR therefore (1) makes mode availability reflect what each mode
can actually do on the current project, (2) restricts `single` to the
one-dataset case — which removes the buggy multi-loop and closes issue
85 — (3) keeps `sequential` as the folder sweep it already is, and (4)
tidies the `sequential` data-source configuration (sensible defaults, an
optional copy-into-project flag, and room for a future remote source).
It extends [`fit-mode-categories`](fit-mode-categories.md).

An earlier draft of this ADR proposed redefining `sequential` to fit the
loaded datasets in turn; that direction was dropped (see Alternatives
Considered) in favour of keeping the existing, tested `sequential`
behaviour and solving issue 85 by restricting `single`.

## Decision

### 1. Mode availability is precondition-based, not a static list

Two distinct concepts are separated explicitly so that offering a mode
and being able to run it do not collapse into one rule:

- **Applicability** — "could this mode apply to the project as loaded?"
  This drives `fitting_mode.show_supported()`.
- **Readiness** — "is this mode fully configured to run right now?" This
  is checked only at `fit()` time and produces the Decision 6 errors.

`fitting_mode.show_supported()` lists exactly the modes whose
**applicability** predicate the current project satisfies. This is wired
through the existing switchable-category selector
(`FittingMode._supported_types(filters)`, which today ignores its
`filters`); it now consumes project state. No new owner-level setter is
added — the category-owned-selector contract from
[`switchable-category-owned-selectors`](switchable-category-owned-selectors.md)
is preserved.

**Applicability** predicates (drive `show_supported()`) are by **total
loaded-experiment count**:

- `single` → exactly one loaded experiment.
- `joint` → two or more loaded experiments.
- `sequential` → exactly one loaded experiment (the template). It
  deliberately does **not** require a configured data source, so
  `sequential` is offered as soon as one dataset is loaded — preserving
  the intended workflow of switching to it and *then* pointing it at a
  folder.

**Readiness** (checked at `fit()` time, see Decisions 4 and 6) covers
everything beyond the count: each scheduled experiment must have measured
data (enforced by the existing `Fitter._require_measured_data` guard — a
calculated-only experiment yields a clear fit-time error, not a hidden
mode), and `sequential` additionally needs a resolvable `data_dir` that
matches at least one file. An unconfigured or empty source is a clear
fit-time error, **not** a reason to hide the mode. Counting *loaded* (not
*measured*) experiments for applicability keeps `show_supported()` and
`fit()` consistent for mixed measured/calculated projects without any
"schedule only the measured subset" filtering.

The availability table is a **consequence** of the applicability
predicates, not a hard-coded rule:

| Experiments loaded | Available modes        |
| ------------------ | ---------------------- |
| 0                  | — (nothing fittable)   |
| 1                  | `single`, `sequential` |
| ≥ 2                | `joint`                |

Predicate-based applicability is preferred over a central `if count >= 2`
switch because it is **honest** (it can also reflect, e.g., an
experiment with no measured data, not just a count), **extensible** (a
future remote data source becomes another way `sequential`'s readiness
is satisfied — see Deferred Work), and keeps the selector contract
clean.

### 2. Restrict `single` to exactly one loaded experiment

`single` means "fit the one loaded dataset." It is no longer a
multi-experiment loop. This removes the `single`-with-N behaviour.

### 3. Keep `sequential` as the folder-of-files sweep

`sequential` keeps its current behaviour unchanged: one loaded
experiment as a template, swept over a folder of data files, producing
per-point `results.csv` and parameter-evolution plots. It is offered
**alongside `single` when exactly one dataset is loaded** — matching the
real workflow (tune one dataset, then switch to `sequential` and point
at a folder). There is no redefinition and no behavioural change to the
sweep itself.

### 4. Tidy the `sequential` data-source configuration

The `sequential_fit` category keeps `data_dir`, `file_pattern`,
`max_workers`, `chunk_size`, and `reverse`, with these refinements:

- **`file_pattern` keeps its `'*'` default (first step).** Deriving the
  glob from the loaded template experiment's data-file extension is
  **deferred** (see Deferred Work): the experiment model does not retain
  its source data-file path today, so the extension is unavailable
  without new source-path metadata. The shipped first-step default is
  therefore `'*'` (the explicit fallback); the derived default is a
  tracked follow-up.
- **No smart default for `data_dir`.** It stays unset by default; a
  silent auto-pickup of files from a guessed folder would be surprising.
  An unset `data_dir` is a clear fit-time error (Decision 6).
- **`copy_data` (new boolean, default `False`).** When `False`
  (default), matched files are referenced in place; when `True`, the
  matched files are copied into the project so it is self-contained.
  Default-off avoids surprising large copies for thousand-file series,
  while letting users opt into a portable, archived project. To avoid
  shipping a decided field with an undefined contract, the **minimal
  first-step behaviour is fully specified here**:
  - **Timing.** The copy happens at `fit()` time, during `sequential`
    readiness resolution, *before* the sweep begins — not at config
    time (so it always reflects the `data_dir`/`file_pattern` in effect
    for that run).
  - **Destination.** A fixed project-relative folder
    (`<project>/data/sequential/`); the run then reads its inputs from
    there. The destination is derived, not separately configurable.
  - **Conflict policy.** Idempotent overwrite: a destination file of the
    same name is overwritten so the in-project copy always matches the
    current source. (Users with very large series leave `copy_data`
    off.)
  - **Round-trip / portability contract.** Once a copy succeeds, the
    persisted `data_dir` is **rewritten to the project-relative copy
    destination** (`data/sequential/`). The saved project is therefore
    self-contained: on reload — even moved or shared, with the original
    external source gone — `sequential` readiness resolves against the
    in-project copy. `file_pattern` persists as set (the copied files
    keep their names, so it still matches). The copy is **idempotent**:
    when the resolved source directory is already the copy destination
    (the post-reload case, where `data_dir` already points at
    `data/sequential/`), the copy is skipped and the run uses the
    archived files. Re-running `fit()` against a fresh external
    `data_dir` re-copies and refreshes the archive.
  - **What is serialized.** The `sequential_fit` fields — including
    `copy_data` and the (possibly rewritten) `data_dir` / `file_pattern`
    — are written to CIF as for any category. When `copy_data=False`,
    `data_dir` persists exactly as the user set it (reference in place);
    when `copy_data=True`, it persists as the in-project destination per
    the round-trip contract above. The copied data files themselves are
    project artifacts, not CIF content.

### 5. Close issue 85 by removing `single`-with-N

With `single` restricted to one experiment, the multi-experiment loop
that overwrote the shared structure no longer exists, so issue 85 cannot
occur. The `_parameter_snapshots` in-memory store and
`plot_param_series_from_snapshots` fallback — fed **only** by
`single`-with-N — lose their producer and are removed as dead code.
Parameter-evolution plotting remains served by `sequential`'s
`results.csv` path (`_plot_param_series_from_csv`).

### 6. Validate at fit time with clear errors; never switch modes silently

- Selecting a mode whose preconditions the project does not meet (e.g. a
  persisted `single` after a second dataset is loaded, or `joint` with
  one dataset) → a clear `ValueError` naming the valid modes.
- `sequential` with an unset/unresolvable `data_dir` or no matching
  files → a clear `ValueError` recommending the user check/set
  `data_dir` and `file_pattern`. This is an **error**, not a warning:
  the user explicitly asked to fit, and there is nothing to fit.
- The mode is never silently auto-switched behind the user's back.

### 7. Hide irrelevant mode categories from display; never mutate the attribute set

`joint_fit`, `sequential_fit`, and `sequential_fit_extract` remain
**eagerly instantiated** and always present as attributes. Visibility in
`analysis.help()` / display and inclusion in CIF follow the active mode
via the existing `_help_filter` and `_serializable_categories` filters.
The attribute set is never dynamically added to or removed from based on
project state, per the "eager, explicit `__init__`, no runtime class
mutation" architecture in §Architecture.

## Consequences

### Positive

- The offered mode list reflects what can actually run on the loaded
  project — far less confusing than a static three-mode list.
- The `single`/`sequential` overload is gone; issue 85 is closed by
  construction rather than patched.
- `sequential` — a substantial, tested feature — is left untouched, so
  this change is low risk.
- The dead `_parameter_snapshots` fallback is removed.
- Precondition-based detection extends cleanly to future data sources.
- `copy_data` enables self-contained projects when wanted, without
  forcing copies on large series.

### Trade-offs

- There is no built-in way to fit two or more **separately loaded**
  datasets _independently_; that is served by separate projects or by a
  folder-based `sequential` series. Accepted by the project owner
  ("compare independent results → separate projects").
- Availability now depends on mutable project state (experiment count
  and measured-data presence), so the offered list changes as data is
  loaded — intended, but a shift from the previous static listing.
- `copy_data` adds one configuration field and a copy step to maintain.

### Compatibility

- Project is in beta: no shims. Tutorials, tests, and CLI that relied on
  `single`-with-N are updated to use `joint`, `sequential`, or separate
  projects as appropriate.
- CIF restore: a persisted `fitting_mode.type` that is invalid for the
  restored project is kept as stored but rejected at fit time with a
  clear error (Decision 6); it is not silently rewritten.

## Alternatives Considered

### Redefine `sequential` to fit the loaded datasets in turn

The earlier draft of this ADR redefined `sequential` as "fit each of the
≥2 loaded experiments in turn, carrying parameters forward, retaining
per-dataset results," making it the ≥2 mode and resolving issue 85 by
its construction. Rejected: it is a risky behavioural change to a tested
feature, and it required a carry-forward design, a plot-replay contract
to avoid corrupting the shared live structure, explicit series
preconditions, and a resolution of the `sequential_fit` folder-surface
conflict (park vs split into a `scan` mode). Keeping `sequential` as the
existing folder sweep and restricting `single` achieves the same goals
with far less surface area and risk.

### Keep `single`-with-N and fix issue 85 with snapshot-restore

Retain the multi-dataset `single` loop and fix issue 85 by storing each
experiment's fitted parameters and re-applying them (in a scoped,
self-restoring context) before plotting. Rejected: it keeps and hardens
a path the owner does not want, and adds replay machinery; removing
`single`-with-N dissolves the bug instead.

### Static mode list or a central count switch

Keep listing all modes always, or gate them with a single
`if count >= 2` block. Rejected in favour of per-mode precondition
predicates, which are more honest about _why_ a mode is unavailable and
extend to future input sources.

### Auto-default `data_dir` to a project folder

Default `sequential_fit.data_dir` to a conventional in-project folder.
Rejected: silently picking up files from a guessed location is
surprising; an explicit clear error when no source is configured is
safer and more discoverable.

## Open Questions

- **Resume.** Resume is currently "single mode only"
  (`_validate_fit_request`). Confirm `single` (one dataset) keeps resume
  as today; any per-point resume for `sequential` is out of scope.

## Deferred Work

- **Remote / online data source for `sequential`.** This ADR only
  requires that the data-source configuration **not preclude** it:
  `sequential`'s input is framed conceptually as a "data source" whose
  first concrete form is a local folder (`data_dir` + `file_pattern`). A
  future ADR can add a URL / online-resource source as another way to
  satisfy the `sequential` "resolvable data source" precondition,
  reusing the same mode and `results.csv` evolution output without
  reopening the mode design.
- Advanced `copy_data` policies beyond the first-step contract in
  Decision 4 (e.g. content-hash dedup, incremental sync, a configurable
  destination) — the default-off flag and minimal overwrite contract
  ship in the first step.
- **Template-derived `file_pattern` default.** Deferred from Decision 4:
  retain the template experiment's source data-file path as new
  experiment metadata (with persistence and tests), then default the
  glob to its extension (`.xye` → `*.xye`). The first step ships the
  `'*'` default.
- Detailed result-file/export layout remains governed by
  [`fit-output-files-and-data-exports`](../suggestions/fit-output-files-and-data-exports.md).
