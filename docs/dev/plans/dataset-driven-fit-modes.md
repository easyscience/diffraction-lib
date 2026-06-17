# Plan: Dataset-Driven Fit Mode Availability

Governed by [`AGENTS.md`](../../../AGENTS.md). No deliberate exceptions
to those instructions are taken in this plan.

Implements ADR
[`dataset-driven-fit-modes`](../adrs/suggestions/dataset-driven-fit-modes.md)
(Status: Proposed — this plan promotes it to `accepted/` as part of the
implementation, per §Change Discipline). Closes issue **85 — Retain
Per-Experiment Fitted Parameters for Plotting**
([`open/highest_retain-per-experiment-fitted-parameters-for-plotting.md`](../issues/open/highest_retain-per-experiment-fitted-parameters-for-plotting.md))
by removing the `single`-with-N path that caused it.

## ADR

This plan **owns** the ADR `dataset-driven-fit-modes` (currently a
suggestion). Phase 1 promotes it to `accepted/` (P1.8). The change also
extends the accepted
[`fit-mode-categories`](../adrs/accepted/fit-mode-categories.md) ADR but
does not modify it.

## Summary of the change

- Fit-mode availability becomes **applicability-based**:
  `fitting_mode.show_supported()` lists only the modes whose
  applicability predicate the loaded project satisfies — `single`
  (exactly one loaded experiment), `joint` (≥2), `sequential` (exactly
  one loaded experiment). Readiness — each scheduled experiment has
  measured data, and `sequential` has a resolvable `data_dir` matching
  files — is checked at `fit()`, not for visibility.
- `single` is restricted to exactly one experiment; the multi-experiment
  loop (`single`-with-N) is removed, which **closes issue 85** by
  construction.
- The now-orphaned `_parameter_snapshots` / `plot_param_series_from_snapshots`
  fallback is deleted; parameter-evolution plotting stays on the
  `sequential` `results.csv` path.
- `sequential` keeps its folder-sweep behaviour; its data-source config
  gains a clear "no files" fit-time error and a `copy_data` flag (default
  off) with a defined, idempotent round-trip contract. (The
  template-derived `file_pattern` default from the ADR is deferred — see
  Decision 4.)

## Decisions (from the ADR — see it for rationale)

1. Applicability drives `show_supported()`; readiness is enforced only
   at `fit()`. The `.type` setter stays permissive (any mode), so CIF
   restore keeps a stored mode and rejection happens at fit time.
2. **Applicability is by total loaded-experiment count; measured-data is
   readiness.** `single`/`sequential` are applicable when the project
   holds exactly one loaded experiment, `joint` when it holds ≥2 —
   regardless of measured-vs-calculated. The requirement that each
   scheduled experiment actually has measured data is a **readiness**
   check enforced at `fit()` by the existing
   `Fitter._require_measured_data` guard (a calculated-only experiment
   yields a clear fit-time error, not a hidden mode). This keeps
   `show_supported()` and `fit()` consistent for mixed
   measured/calculated projects, and avoids any "schedule only the
   measured subset" filtering. **This refines the ADR's "experiment with
   measured data" applicability wording into the applicability/readiness
   split; the ADR text is aligned at promotion (P1.8).**
3. `copy_data` (default `False`): at `fit()`, before the sweep, copy
   matched files into `<project>/data/sequential/`, rewrite persisted
   `data_dir` to that relative destination (portability), overwrite on
   name conflict; only the `sequential_fit` fields are serialized. The
   copy is **idempotent**: when the resolved source directory is already
   the copy destination (the post-reload case), the copy is skipped and
   the run uses the archived files.
4. `data_dir` has no smart default. **`file_pattern` keeps its current
   `'*'` default for the first step**; the ADR's "derive the glob from
   the template experiment's data-file extension" is deferred because the
   experiment model does not retain its source data-file path today
   (deriving it requires new experiment source-path metadata + its
   persistence and tests). The ADR's stated `'*'` fallback is therefore
   the shipped first-step behaviour; the derived default is a tracked
   follow-up. The ADR text is aligned at promotion (P1.8).

## Open questions

- **`fitting-exercise-si-lbco.py` pedagogy (P1.7).** This tutorial fits
  multiple experiments per project in default (`single`) mode. The plan
  switches those fits to `joint`; if the exercise intends *independent*
  per-experiment fits, it should instead be split into single-experiment
  projects. Default taken: switch to `joint`; confirm during review if
  the pedagogy requires otherwise.
- **Resume** stays `single`-only as today; per-point `sequential` resume
  is out of scope (ADR Open Questions).
- **Template-derived `file_pattern` (deferred).** Needs new experiment
  source-data-path metadata (plus persistence and tests). The first step
  ships the `'*'` default; a follow-up adds the source-path metadata and
  derives `*.ext` from it. Tracked as Deferred Work in the ADR at
  promotion (P1.8).

## Concrete files likely to change

Phase 1 (implementation):

- `src/easydiffraction/analysis/categories/fitting_mode/default.py` —
  `_supported_types(filters)` returns applicable modes.
- `src/easydiffraction/analysis/analysis.py` —
  `_supported_filters_for` context for `fitting_mode` (loaded-experiment
  count); fit-time applicability validation in `_validate_fit_request`;
  collapse `_fit_single_experiments` to one experiment; remove
  `_parameter_snapshots` (line ~602) and `_snapshot_params` (~3009);
  sequential data-source resolution + `copy_data` handling; check
  `_help_filter` / `_serializable_categories`.
- `src/easydiffraction/analysis/categories/sequential_fit/default.py` —
  add `copy_data` `BoolDescriptor` + property (mirror `reverse`).
- `src/easydiffraction/analysis/sequential.py` — no-files error;
  idempotent copy (skip self-copy) + `data_dir` rewrite.
- `src/easydiffraction/display/plotting.py` — remove
  `plot_param_series_from_snapshots` and the snapshot fallback branches
  in `plot_param_series`, `plot_all_param_series`,
  `_collect_fitted_parameter_unique_names`; no-CSV path warns and
  returns.
- `docs/docs/tutorials/fitting-exercise-si-lbco.py` (+ regenerated
  `.ipynb`) — stop relying on `single`-with-N.
- `docs/dev/issues/...` — move issue 85 to `closed/`, update index.
- `docs/dev/adrs/...` — promote ADR to `accepted/`, update index, fix
  status/links.

Phase 2 (verification — tests):

- `tests/unit/easydiffraction/analysis/categories/test_fitting_mode*` /
  `test_fitting*` — applicability predicates given experiment counts.
- `tests/unit/easydiffraction/analysis/test_analysis*` — fit-time
  validation errors; single-exactly-one.
- `tests/.../sequential_fit` + `tests/integration/fitting/test_sequential.py`
  — `copy_data` round-trip, idempotent self-copy (source == destination
  skips), no-files error.
- `tests/unit/easydiffraction/display/test_plotting_coverage.py`,
  `tests/.../test_analysis_coverage.py`,
  `tests/integration/fitting/test_analysis_and_fit_category_support.py`
  — drop snapshot-based expectations; assert no-CSV warns.

## Branch and PR notes

- Branch: `dataset-driven-fit-modes` (already checked out).
- PR targets `develop`. Do not push unless asked.

## Implementation steps (Phase 1)

Per §Planning and §Commits: when an AI agent follows this plan, every
completed Phase 1 step is staged with **explicit paths** and committed
locally (atomic, single-purpose) before moving on. Mark each `- [ ]` as
`- [x]` in the same commit that completes it.

  Applicability/readiness contract used across P1.1–P1.3 (Decision 2):
  applicability counts **total loaded experiments**; the
  measured-data requirement is a **readiness** check left to the
  existing `Fitter._require_measured_data` guard at `fit()`. No
  "schedule only the measured subset" filtering is introduced.

- [x] **P1.1 — Applicability-based `show_supported()`.**
  Add an Analysis helper that returns the loaded-experiment count
  (`len(project.experiments)`); have `_supported_filters_for` pass that
  count to the `fitting_mode` category; implement
  `FittingMode._supported_types(filters)` to return `single`
  (count == 1), `joint` (count ≥ 2), `sequential` (count == 1).
  Files: `analysis.py`, `fitting_mode/default.py`.
  Commit: `Offer fit modes by project applicability`

- [x] **P1.2 — Enforce mode preconditions at fit time.**
  In `_validate_fit_request`, reject a selected mode whose applicability
  predicate the project does not meet — `single`/`sequential` unless
  exactly one experiment is loaded, `joint` unless ≥2 — with a clear
  `ValueError` naming the valid modes. Keep the `.type` setter permissive
  so CIF restore is not rejected. Measured-data readiness stays with
  `Fitter._require_measured_data` (no change needed there). Files:
  `analysis.py`.
  Commit: `Validate fit mode against loaded experiments`

- [x] **P1.3 — Restrict `single` to exactly one experiment.**
  With P1.2 guaranteeing exactly one loaded experiment for `single`,
  collapse `_fit_single_experiments` to fit that one experiment (no
  loop); drop the per-experiment `_snapshot_params` call. Files:
  `analysis.py`.
  Commit: `Fit a single experiment in single mode`

- [x] **P1.4 — Remove the `single`-with-N snapshot machinery.**
  Delete `_parameter_snapshots` and `_snapshot_params`; remove
  `plot_param_series_from_snapshots` and the snapshot fallback branches
  in `plot_param_series`, `plot_all_param_series`, and
  `_collect_fitted_parameter_unique_names`; when no `results.csv`
  exists, log a clear warning and return. Files: `analysis.py`,
  `display/plotting.py`.
  Commit: `Remove single-mode parameter snapshot fallback`

- [x] **P1.5 — Sequential data source: no-files error, `copy_data`.**
  Add `copy_data` `BoolDescriptor` (+ property, default `False`) to
  `SequentialFit` (mirror `reverse`). In sequential resolution: raise a
  clear `ValueError` when `data_dir` is unset/unresolvable or matches no
  files (keeping the current `'*'` `file_pattern` default — the
  template-extension derivation is deferred, Decision 4). When
  `copy_data` is set, apply the **idempotent** copy: if the resolved
  source directory is already the copy destination
  (`<project>/data/sequential/`, the post-reload case), skip the copy and
  run from the archived files; otherwise copy matched files there
  (overwrite on name conflict) and rewrite the persisted `data_dir` to
  that relative destination. Files: `sequential_fit/default.py`,
  `sequential.py`, `analysis.py`.
  Commit: `Add copy_data and clearer sequential data resolution`

- [x] **P1.6 — Reconcile display/serialization filters.**
  Verify `_help_filter` and `_serializable_categories` reflect the
  active mode under the new model (sequential config hidden in `single`,
  etc.); adjust only if needed. Files: `analysis.py`.
  Commit: `Align analysis category visibility with fit modes`

- [ ] **P1.7 — Update tutorials relying on `single`-with-N.**
  In `docs/docs/tutorials/fitting-exercise-si-lbco.py`, switch the
  multi-experiment `single` fits to `joint` (see Open questions), then
  run `pixi run notebook-prepare`. Stage the `.py` and regenerated
  `.ipynb`. Files: tutorial source + notebook.
  Commit: `Update Si/LBCO exercise to joint fitting`

- [ ] **P1.8 — Close issue 85 and promote the ADR.**
  `git mv` issue 85 to `closed/retain-per-experiment-fitted-parameters-for-plotting.md`,
  rewrite its body to describe the resolution (single restricted to one
  dataset; snapshot fallback removed), and update
  `docs/dev/issues/index.md`. Promote the ADR: `git mv`
  `docs/dev/adrs/suggestions/dataset-driven-fit-modes.md` →
  `accepted/`, set its `## Status` to `Accepted`, flip its
  `docs/dev/adrs/index.md` row to `Accepted` with the `accepted/...`
  link, fix any links that pointed at `suggestions/...`
  (`git grep -n`), and remove the `_review-*`/`_reply-*` siblings if
  still present. **Align the ADR text to the refinements made during
  plan review:** Decision 1/applicability wording → loaded-experiment
  count with measured-data as readiness (plan Decision 2); Decision 4 →
  move the template-derived `file_pattern` default to Deferred Work and
  state `'*'` as the shipped default (plan Decision 4); Decision 3 → note
  the idempotent self-copy skip. Files: `docs/dev/issues/...`,
  `docs/dev/adrs/...`.
  Commit: `Close issue 85 and accept dataset-driven fit modes ADR`

- [ ] **P1.9 — Phase 1 review gate.** No-code step. Mark `[x]`, commit
  the checklist update alone with message `Reach Phase 1 review gate`,
  then stop for Phase 1 review.

## Verification (Phase 2)

Add/update tests first (see "Concrete files" Phase 2 list), then run the
full suite. Use the zsh-safe log-capture pattern from §Workflow.

```bash
pixi run fix
pixi run check > /tmp/easydiffraction-check.log 2>&1; check_exit_code=$?; tail -n 200 /tmp/easydiffraction-check.log; exit $check_exit_code
pixi run unit-tests > /tmp/easydiffraction-unit.log 2>&1; unit_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-unit.log; exit $unit_tests_exit_code
pixi run integration-tests > /tmp/easydiffraction-integration.log 2>&1; integration_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-integration.log; exit $integration_tests_exit_code
pixi run script-tests > /tmp/easydiffraction-script.log 2>&1; script_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-script.log; exit $script_tests_exit_code
pixi run test-structure-check
```

Notes:

- `pixi run fix` regenerates `docs/dev/package-structure/full.md` and
  `short.md`; include them only if changed.
- Tutorial project-path collisions, benchmark CSVs, and sandbox-only
  multiprocessing failures: handle per §Workflow.

## Status checklist

- [x] P1.1 — Applicability-based `show_supported()`
- [x] P1.2 — Enforce mode preconditions at fit time
- [x] P1.3 — Restrict `single` to exactly one experiment
- [x] P1.4 — Remove the `single`-with-N snapshot machinery
- [ ] P1.5 — Sequential data source: default, no-files error, `copy_data`
- [x] P1.6 — Reconcile display/serialization filters
- [ ] P1.7 — Update tutorials relying on `single`-with-N
- [ ] P1.8 — Close issue 85 and promote the ADR
- [ ] P1.9 — Phase 1 review gate
- [ ] Phase 2 — tests added and full verification suite green

## Suggested Pull Request

**Title:** Clearer fit modes that match your loaded data

**Description:** EasyDiffraction now offers only the fitting modes that
make sense for what you have loaded: with one dataset you get a normal
single fit (and can switch to a sequential scan over a folder of files);
with several datasets you get a combined (joint) fit. This removes a
confusing case where fitting several datasets one-by-one could make
earlier datasets plot incorrectly. Sequential scans are also clearer to
set up: you get a clear message when no data files are found, and a new
option can copy the scanned files into your project so it stays
self-contained and portable.
