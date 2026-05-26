# Plan: Undo Fit

## Project guidance

This plan adheres to [`AGENTS.md`](../../../AGENTS.md). No deliberate
exceptions are claimed.

## ADR

This plan implements [`undo-fit.md`](../adrs/suggestions/undo-fit.md)
(currently in `docs/dev/adrs/suggestions/`; P1.6 promotes it to
`docs/dev/adrs/accepted/`). The ADR specifies a single-level scalar
rollback driven by the existing `_fit_parameter.start_value` and
`_fit_parameter.start_uncertainty` anchors, fit-result/posterior
clearing, an in-memory `undo_fit()` operation with disk side-effects
deferred to `project.save()`, idempotent no-op semantics for every
"nothing to undo" case, and a split persistence/load gate so that
`_fit_parameter` rows survive undo+save+reload while `_fit_result.*`
does not.

The plan also relies on these already-accepted ADRs without modifying
them:

- [`analysis-cif-fit-state.md`](../adrs/accepted/analysis-cif-fit-state.md)
  for the existing persistence layout that this plan extends.
- [`minimizer-category-consolidation.md`](../adrs/accepted/minimizer-category-consolidation.md)
  for the HDF5 sidecar truncation semantics reused on undo.
- [`minimizer-input-output-split.md`](../adrs/accepted/minimizer-input-output-split.md)
  for the input/output category split that places `_fit_result.*` on the
  active minimizer's paired output category.

## Branch and PR

- Current branch: `undo-fit` (already matches the plan slug, branched
  off `develop`).
- PR target branch: `develop` (per `AGENTS.md` §Planning).
- Do not push the branch until the user asks.

## Decisions

Decisions already pinned in the ADR; restated here so the implementation
has a single reference surface.

- **In-memory rollback only.** `Analysis.undo_fit()` mutates parameter
  scalars, `fit_results`, posterior summaries, the persisted
  `_fit_result.*` and `_fit_parameter_correlations` categories, the
  `_persisted_fit_state_sidecar` dict, and the
  `_has_persisted_fit_state` flag. No CIF or HDF5 file is rewritten;
  disk side-effects happen on the subsequent `project.save()`. CLI
  `--dry` skips that save (mirrors
  `easydiffraction PROJECT_DIR fit --dry`).
- **Preserve `_fit_parameter` rows.** Undo does not call
  `Analysis._clear_persisted_fit_state()` because that wipes the
  user-owned `fit_min`/`fit_max`/`fit_bounds_uncertainty_multiplier`
  projections and the `start_value`/`start_uncertainty` anchors needed
  for idempotence.
- **Result-kind is the on-disk marker.** The save and load gates in
  `Analysis._fit_state_categories()` /
  `_has_persisted_fit_state_sections()` are split so that
  `_fit_parameter` rows are persisted/restored whenever the loop has
  entries (independent of any fit-result flag), while `_fit_result.*`
  and `_fit_parameter_correlations` are gated on the presence of
  `_fit_result.result_kind`. The in-memory
  `Analysis._has_persisted_fit_state()` flag is set on load iff
  `_fit_result.result_kind` is present in the CIF.
- **No-op detection.** A second `undo_fit()` call (in the same session
  or across save+reload) finds every fitted parameter already at its
  `_fit_parameter.start_value` within float tolerance, returns without
  mutating state, and emits the INFO message `"No fit to undo."`. The
  same branch fires when no `_fit_parameter.start_value` rows exist at
  all (never-fit projects, legacy projects predating the start-value
  schema).
- **No `RuntimeError`.** `undo_fit()` never raises for nothing-to-undo.
  The CLI exits status 0 in all no-op cases.
- **Reuse existing helpers.** `Analysis._clear_fit_result_projection()`
  already resets `_fit_result.*` descriptors via
  `fit_result._reset_result_descriptors()`; the new `undo_fit()`
  composes it with a correlation-clear, posterior-clear, sidecar reset,
  and scalar restore — rather than introducing a new bespoke helper that
  duplicates `_clear_persisted_fit_state`.
- **No-op detection key.** The "is a fit-result currently committed"
  check uses `Analysis._has_persisted_fit_state()` (the in-memory flag)
  — **not** `self._fit_results is None` and **not** the public
  `self.fit_results` property. The private slot misses loaded projects
  whose lazy restore has not yet fired; the public property triggers the
  lazy restore as a side-effect of the check, which is the wrong thing
  to do mid-undo. The flag is the canonical signal because it is set
  true on load iff `_fit_result.result_kind` is present in the CIF and
  reset false by undo itself.
- **`undo_fit()` returns a small outcome object.** A frozen
  `UndoFitOutcome` dataclass (under `src/easydiffraction/analysis/`)
  capturing `restored_parameter_names: tuple[str, ...]`,
  `cleared_fit_result: bool`, `cleared_sidecar: bool`, and
  `was_no_op: bool` — enough for the CLI to render the ADR §Examples
  summary without diffing pre/post scalars (which would misclassify
  legitimate undos of fits that did not move any parameter).
- **Per-row posterior clearing.** Each `_fit_parameter` row also carries
  Bayesian posterior summary fields (`posterior_best_sample_value`,
  `posterior_median`, `posterior_uncertainty`, the 68/95 interval
  columns, `posterior_gelman_rubin`,
  `posterior_effective_sample_size_bulk`) populated by Bayesian fits.
  Undo clears these per-row fields in place — they are fit-derived, not
  user-owned — while keeping `fit_min`, `fit_max`,
  `fit_bounds_uncertainty_multiplier`, `start_value`, and
  `start_uncertainty` intact. This keeps the saved CIF consistent with
  the live `Parameter.posterior = None` state after undo.
- **No new dependencies.** All work uses the existing standard library,
  numpy, and project utilities.

## Open questions

These remain open for review feedback but should not block
implementation; the implementer should pick the listed default unless
feedback says otherwise.

- **Float tolerance for "already at start_value" detection.** Default:
  `math.isclose(current, start, rel_tol=1e-12, abs_tol=0.0)` per scalar,
  matching the strictest comparison the project already uses elsewhere.
  Alternative: a single `np.allclose` over the whole parameter vector
  with the same tolerances.
- **Tutorial coverage.** The plan does not add a new tutorial notebook
  for undo by default. If the reviewer requires user-facing tutorial
  coverage, add an `ed-XX.py` source plus regenerated notebook in Phase
  2 via `pixi run notebook-prepare`.

## Concrete files likely to change

- `src/easydiffraction/analysis/analysis.py`
  - Refactor `_fit_state_categories()` (around lines 1482-1500) and its
    caller (around lines 1025-1027) to split the save gate.
  - Split `_restore_live_parameter_state()` (around lines 550-571) into
    bounds-and-anchors and posterior helpers so live bounds survive an
    undo+save+reload cycle.
  - Add `undo_fit()` public method and any private helpers
    (`_undo_scalar_rollback`, `_undo_clear_fit_result_state`,
    `_undo_is_noop`, `_undo_clear_per_row_posterior_fields`) it
    composes.
  - Add the `UndoFitOutcome` frozen dataclass (small module-local public
    type the method returns).
- `src/easydiffraction/io/cif/serialize.py`
  - Refactor `_has_persisted_fit_state_sections()` (around lines
    580-590) to use `_fit_result.result_kind` as the marker.
  - Refactor `_restore_persisted_fit_state()` and
    `_restore_common_fit_state()` (around lines 593-617) so
    `_fit_parameter` loading is decoupled from the fit-result presence
    check.
- `src/easydiffraction/project/project.py`
  - Update `_load_project_analysis()` (around lines 164-176) to call the
    new bounds-and-anchors helper whenever `_fit_parameter` rows are
    present in the loaded analysis, independent of
    `_has_persisted_fit_state()`.
- `src/easydiffraction/__main__.py`
  - Replace the `undo` command stub (around lines 230-242) with a real
    implementation: load project, call `project.analysis.undo_fit()`,
    consume the returned `UndoFitOutcome` to render the ADR §Examples
    summary, save unless `--dry`.
- `docs/dev/adrs/suggestions/undo-fit.md` →
  `docs/dev/adrs/accepted/undo-fit.md`
  - Move file, update Status from "Proposed" to "Accepted", drop the
    now-stale "Status Note" section.
- `docs/dev/adrs/index.md`
  - Update the `Undo Fit` row from `Suggestion` to `Accepted` and
    repoint the link from `suggestions/` to `accepted/`.

The following files are listed for awareness but should remain unchanged
unless the implementation surfaces a specific reason to touch them:

- `src/easydiffraction/core/variable.py` — `Parameter._posterior`
  already has `_set_posterior()` (around line 446); `undo_fit()` calls
  it with `None` rather than introducing a new clearing primitive.
- `src/easydiffraction/analysis/categories/fit_result/base.py` —
  `_reset_result_descriptors()` already exists; do not add new reset
  entry points.
- `src/easydiffraction/analysis/categories/fit_parameter_correlations/`
  — clearing today happens via
  `self._fit_parameter_correlations = FitParameterCorrelations()` in
  `_clear_persisted_fit_state`; reuse the same idiom in `undo_fit()`.

## Agent commit policy

When an AI agent follows this plan via `/draft-impl-1`, every completed
Phase 1 implementation step must be staged with explicit paths and
committed locally before moving to the next implementation step or the
Phase 1 review gate. Stage only the files modified for the step, per
`AGENTS.md` §Commits, and never use blanket `git add .` or `git add -A`.
The suggested commit messages below are single-purpose and align 1-to-1
with their step.

## Implementation steps (Phase 1)

- [x] **P1.1 — Split fit-state persistence gate (save side).**

  In `src/easydiffraction/analysis/analysis.py`, change the save gate so
  `_fit_parameter` rows are serialized whenever they have entries,
  independent of `_has_persisted_fit_state()`. Keep `_fit_result.*` and
  `_fit_parameter_correlations` gated on the flag.

  Approach: refactor `Analysis._fit_state_categories()` into two callers
  — one that returns the always-persistent categories (`fit_parameters`)
  and one that returns the flag-gated categories (`fit_result`,
  `fit_parameter_correlations`). The single call site at `analysis.py`
  around lines 1025-1027 then extends the category list from both,
  applying the flag gate only to the second.

  No observable behavior change today (today's flow always either has
  both `_fit_parameter` rows AND the flag set, or neither), but the
  refactor is the prerequisite for P1.4.

  Stage: `src/easydiffraction/analysis/analysis.py`.

  Commit: `Split fit-state save gate from _fit_parameter rows`

- [x] **P1.2 — Split fit-state persistence gate (load side).**

  In `src/easydiffraction/io/cif/serialize.py`, change
  `_has_persisted_fit_state_sections()` to detect
  `_fit_result.result_kind` as the canonical "fit-result is present"
  marker; drop the `_fit_parameter.param_unique_name` and
  `_fit_parameter_correlation.param_unique_name_i` loop tags from the
  marker set.

  Split `_restore_common_fit_state()` (and adjust
  `_restore_persisted_fit_state()` accordingly) so that:
  - `fit_parameters.from_cif(block)` is called whenever the
    `_fit_parameter` loop is present in the CIF (independent of the
    result-kind check).
  - `fit_result.from_cif(block)` and
    `fit_parameter_correlations.from_cif(block)` plus
    `analysis._set_has_persisted_fit_state(value=True)` are called only
    when `_fit_result.result_kind` is present.

  Stage: `src/easydiffraction/io/cif/serialize.py`.

  Commit: `Use _fit_result.result_kind as the fit-state load marker`

- [x] **P1.3 — Decouple live-parameter restoration from fit-result
      flag.**

  P1.2 ensures `_fit_parameter` rows load from CIF independently of the
  fit-result flag, but the rows are projected onto live `Parameter`
  objects by `Analysis._restore_live_parameter_state()`
  (`src/easydiffraction/analysis/analysis.py` lines 550-571), and that
  method is called only when `_has_persisted_fit_state()` is true
  (`src/easydiffraction/project/project.py` lines 175-176). Under the
  new contract the flag is false when only `_fit_parameter` rows exist
  on disk, so without this step live
  `Parameter.fit_min`/`fit_max`/`fit_bounds_uncertainty_multiplier`
  would silently revert to their defaults after an undo+save+reload
  cycle and `Parameter._fit_start_value`/`_fit_start_uncertainty` would
  not be repopulated for the next idempotent undo check.

  Split `_restore_live_parameter_state()` into two helpers on
  `Analysis`:
  - `_restore_live_parameter_bounds_and_anchors(param_map)` — projects
    `row.fit_min.value`, `row.fit_max.value`,
    `row.fit_bounds_uncertainty_multiplier.value`,
    `row.start_value.value`, and `row.start_uncertainty.value` onto the
    matching live `Parameter` for each row. No posterior side-effect.
    Safe to call whenever `_fit_parameter` rows are present.
  - `_restore_live_parameter_posterior(param_map)` — projects
    `row.posterior_summary(...)` onto `parameter._set_posterior(...)`
    and keeps the existing conditional
    `parameter.uncertainty = posterior.standard_deviation` branch for
    finite posterior standard deviations. Safe to call only when a
    fit-result is present.

  Update `_load_project_analysis()` in
  `src/easydiffraction/project/project.py` (lines 164-176) so the
  bounds-and-anchors helper runs whenever `_fit_parameter` rows are
  present in the loaded analysis, and the posterior helper runs only
  when `_has_persisted_fit_state()` is true. Build the parameter map
  once and reuse it for both calls.

  Stage: `src/easydiffraction/analysis/analysis.py`,
  `src/easydiffraction/project/project.py`.

  Commit: `Decouple live-bound restoration from fit-result flag`

- [x] **P1.4 — Add `Analysis.undo_fit()` public method.**

  In `src/easydiffraction/analysis/analysis.py`, add a new public method
  on `Analysis` and the `UndoFitOutcome` frozen dataclass it returns:

  ```python
  @dataclass(frozen=True)
  class UndoFitOutcome:
      """Summary of a single `Analysis.undo_fit()` call."""

      restored_parameter_names: tuple[str, ...]
      cleared_fit_result: bool
      cleared_sidecar: bool
      was_no_op: bool


  def undo_fit(self) -> UndoFitOutcome:
      """Roll back the last committed fit's scalar state and clear
      fit-derived outputs. Idempotent and never raises for
      nothing-to-undo. See docs/dev/adrs/accepted/undo-fit.md."""
  ```

  Behaviour per ADR §2 and §6:
  1. **No-op detection.** If `not self._has_persisted_fit_state()` (the
     in-memory flag, **not** `self._fit_results is None` and **not**
     `self.fit_results`) **and** either no `_fit_parameter` rows exist
     or every fitted parameter is already at its `start_value` within
     float tolerance (`math.isclose(rel_tol=1e-12, abs_tol=0.0)`), emit
     the INFO message `"No fit to undo."` and return
     `UndoFitOutcome(restored_parameter_names=(), cleared_fit_result=False, cleared_sidecar=False, was_no_op=True)`
     without mutating any state.
  2. Otherwise, scalar rollback. For each row in `self.fit_parameters`
     (i.e. `_fit_parameter` entries) whose `row.start_value.value` is
     not `None`:
     - Look up the live `Parameter` by `row.param_unique_name.value`.
     - Restore `parameter.value` from `row.start_value.value`.
     - If `row.start_uncertainty.value` is not `None`, restore
       `parameter.uncertainty`; otherwise set
       `parameter.uncertainty = None` and log the legacy-schema fallback
       once at INFO level.
     - Call `parameter._set_posterior(None)`.
     - Record `row.param_unique_name.value` in the
       `restored_parameter_names` accumulator.
  3. Clear each `_fit_parameter` row's per-row posterior summary fields
     in place (`posterior_best_sample_value`, `posterior_median`,
     `posterior_uncertainty`, the 68/95 interval columns,
     `posterior_gelman_rubin`, `posterior_effective_sample_size_bulk`)
     via a small helper — these fields are fit-derived, not user-owned,
     and would otherwise project stale posterior data back onto live
     `Parameter.posterior` after an undo+save+reload+restore cycle via
     P1.3's posterior helper. This helper still visits every
     `_fit_parameter` row, including rows without `start_value` anchors,
     because posterior summaries are fit-derived even when scalar
     rollback has no safe anchor.
  4. Track `cleared_fit_result = self._has_persisted_fit_state()`
     **before** mutating state — this captures whether the call actually
     discarded a committed fit-result vs only rolled back live scalars.
  5. Clear `_fit_result.*` via `self._clear_fit_result_projection()`.
  6. Reset `_fit_parameter_correlations` via
     `self._fit_parameter_correlations = FitParameterCorrelations()`.
  7. Track `cleared_sidecar = bool(self._persisted_fit_state_sidecar)`
     before resetting it, then reset `_persisted_fit_state_sidecar` to
     `{}`.
  8. Set `_has_persisted_fit_state` to `False` via
     `self._set_has_persisted_fit_state(value=False)`.
  9. Set `self.fit_results = None` (this also resets
     `self._fitter.results` per the existing setter at lines 427-430).
  10. Return
      `UndoFitOutcome(restored_parameter_names=tuple(...), cleared_fit_result=..., cleared_sidecar=..., was_no_op=False)`.

  Compose the body from focused private helpers (`_undo_is_noop`,
  `_undo_scalar_rollback`, `_undo_clear_per_row_posterior_fields`,
  `_undo_clear_fit_result_state`) to stay below `pyproject.toml`'s
  `max-statements`/`max-branches` thresholds. Type-annotate the public
  method and the helpers; numpy-style docstring on `undo_fit()` with
  `Raises` omitted (the method never raises for this scope).

  Stage: `src/easydiffraction/analysis/analysis.py`.

  Commit: `Add Analysis.undo_fit() rollback operation`

- [x] **P1.5 — Wire the CLI `undo` command.**

  In `src/easydiffraction/__main__.py`, replace the stub at lines
  230-242 with a real implementation:
  1. Add a `--dry` flag to the `undo` command, matching the existing
     `fit` command's `dry` parameter.
  2. Load the project with `_load_project(project_dir)`.
  3. Call `outcome = project.analysis.undo_fit()`. The returned
     `UndoFitOutcome` is the sole source of truth for what happened — do
     **not** diff pre/post scalars to infer no-op status, because a
     legitimate undo of a fit that did not move any parameter would show
     zero scalar diff and be misclassified.
  4. If `outcome.was_no_op`, emit the single-line "No fit to undo for
     '<project_name>'. Project state is unchanged." message and exit 0.
  5. Otherwise render the per-line ✅ summary from ADR §Examples, using:
     - `len(outcome.restored_parameter_names)` for the "Restored N
       parameters" count
     - `outcome.cleared_fit_result` to decide whether to emit the
       "Cleared analysis.fit_results" line
     - `outcome.cleared_sidecar` to decide whether to emit the "Cleared
       analysis/results.h5 (Bayesian sidecar)" line For `--dry`, prefix
       with "Would undo …" and use the "would be restored/cleared"
       verbs; do not call `project.save()`.
  6. For a real run (non-dry), call `project.save()` after `undo_fit()`
     and emit the "Saved project to <path>." line.
  7. Exit status 0 in every case (no-op, dry, real).

  Stage: `src/easydiffraction/__main__.py`.

  Commit: `Wire CLI undo to Analysis.undo_fit()`

- [x] **P1.6 — Promote `undo-fit` ADR to accepted.**

  This step intentionally runs **after** `/draft-impl-1`'s Phase A
  cleanup commit. Phase A commits the ADR while it still lives at
  `docs/dev/adrs/suggestions/undo-fit.md` (Phase A's commit message
  therefore reads `Add undo-fit ADR suggestion` per the AGENTS.md §Agent
  Shortcuts spec, because the ADR is under `suggestions/` at commit
  time). P1.6 is the separate promotion commit that records the
  design→accepted transition alongside the implementation that justifies
  it. The result is two ADR-related commits in this PR:
  1. `Add undo-fit ADR suggestion` (Phase A, before P1.1)
  2. `Promote undo-fit ADR to accepted` (this step)

  This split is deliberate and consistent with the shortcut lifecycle:
  Phase A only commits whatever the ADR is at task start; it does not
  move files. The plan handles the move as an explicit P1 step so the
  diff is auditable.

  Move `docs/dev/adrs/suggestions/undo-fit.md` to
  `docs/dev/adrs/accepted/undo-fit.md` (preserve git history with
  `git mv`). Update inside the file:
  - Change `**Status:** Proposed` to `**Status:** Accepted`.
  - Drop the `## Status Note` section (lines 6-12 in the current file) —
    the rollback operation is no longer aspirational.

  Update `docs/dev/adrs/index.md`: in the `Analysis and fitting` group,
  change the `Undo Fit` row's `Status` cell from `Suggestion` to
  `Accepted` and update the link target from `suggestions/undo-fit.md`
  to `accepted/undo-fit.md`. Keep the short description as-is.

  Stage: `docs/dev/adrs/suggestions/undo-fit.md`,
  `docs/dev/adrs/accepted/undo-fit.md`, and `docs/dev/adrs/index.md`.

  Commit: `Promote undo-fit ADR to accepted`

- [x] **P1.7 — Phase 1 review gate.**

  No code change. Mark every preceding `[ ]` in this section as `[x]`,
  stage `docs/dev/plans/undo-fit.md`, and commit the checklist update
  alone. `/review-impl-1` cannot begin until every prior P1 step is
  `[x]`.

  Stage: `docs/dev/plans/undo-fit.md`.

  Commit: `Reach Phase 1 review gate`

## Phase 2 verification

Run after `/review-impl-1` closes with the final-review sentinel.
Capture output where useful with the zsh-safe pattern from `AGENTS.md`
§Workflow.

1. **`pixi run fix`** — apply auto-fixes. Includes regenerated
   `docs/dev/package-structure/full.md` / `short.md`. Commit any
   resulting diff:

   ```sh
   pixi run fix
   ```

   Commit: `Apply pixi run fix auto-fixes`

2. **`pixi run check`** — run static checks until clean. Capture output
   if a failure needs analysis:

   ```sh
   pixi run check > /tmp/easydiffraction-check.log 2>&1; check_exit_code=$?; tail -n 200 /tmp/easydiffraction-check.log; exit $check_exit_code
   ```

   Any mechanical fix is its own commit. Per `AGENTS.md` §Code Style, do
   not raise complexity thresholds, add `# noqa`, or silence checks —
   refactor instead. If a check failure suggests a public-API change
   beyond what the ADR pins, stop and ask before editing.

3. **`pixi run unit-tests`** — add tests under `tests/unit/` mirroring
   the source layout
   (`tests/unit/easydiffraction/analysis/test_analysis.py`,
   `tests/unit/easydiffraction/io/cif/test_serialize.py`,
   `tests/unit/easydiffraction/project/test_project.py` for the
   load-side decoupling, and
   `tests/unit/easydiffraction/test___main__.py` for the CLI — note the
   triple underscore matching the existing dunder module). Verify with
   `pixi run test-structure-check`. Coverage to include at minimum:
   - `Analysis.undo_fit()` happy path: pre-fit captured, fit committed,
     undo restores scalars exactly, posterior cleared, `fit_results` is
     `None`, `_has_persisted_fit_state()` false.
   - `Analysis.undo_fit()` idempotence: second call is a clean no-op, no
     log spam beyond the single `"No fit to undo."` line.
   - `Analysis.undo_fit()` never-fit no-op: project that has never been
     fit returns cleanly with `"No fit to undo."`.
   - Save+reload cycle: after `undo_fit()` + `project.save()` +
     `Project.load()`, `analysis.fit_results` is `None`,
     `_fit_parameter` rows still carry user-owned `fit_min`/`fit_max`,
     **and** the reloaded live `Parameter.fit_min` / `fit_max` /
     `fit_bounds_uncertainty_multiplier` / `_fit_start_value` /
     `_fit_start_uncertainty` equal the values they had before save
     (asserting on the live attributes, not only the stored rows, to
     catch any regression of the P1.3 split). A subsequent `undo_fit()`
     call on the reloaded project is also a no-op (`outcome.was_no_op`
     is `True`).
   - Loaded-no-movement fit: a saved project whose fit-result happens to
     leave every parameter at its `start_value` loads with
     `_has_persisted_fit_state()` true; the first `undo_fit()` on that
     loaded project performs a rollback (clears `_fit_result.*`,
     sidecar, correlations) rather than misclassifying the call as a
     no-op. Asserts that `outcome.was_no_op` is `False` and
     `outcome.cleared_fit_result` is `True` even though no scalar moved.
   - CLI `undo` command exits 0 in no-op cases and prints the expected
     message; the CLI consumes the `UndoFitOutcome` for summary numbers
     rather than diffing scalars.
   - CLI `undo --dry` does not write the project directory (assert mtime
     unchanged or use `tmp_path` fixture).

   ```sh
   pixi run unit-tests > /tmp/easydiffraction-unit-tests.log 2>&1; unit_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-unit-tests.log; exit $unit_tests_exit_code
   ```

   Each logical test addition is a separate commit.

4. **`pixi run integration-tests`** — extend or rely on existing
   integration coverage that round-trips a project through
   `Project.save()` + `Project.load()`. Add an integration test
   demonstrating undo across the save+reload cycle if existing coverage
   does not exercise it.

   ```sh
   pixi run integration-tests > /tmp/easydiffraction-integration-tests.log 2>&1; integration_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-integration-tests.log; exit $integration_tests_exit_code
   ```

5. **`pixi run script-tests`** — run the tutorial script suite. No new
   tutorial is required by default; if the reviewer requested one (per
   Open Questions), update the `ed-XX.py` source and run
   `pixi run notebook-prepare` before this step.

   ```sh
   pixi run script-tests > /tmp/easydiffraction-script-tests.log 2>&1; script_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-script-tests.log; exit $script_tests_exit_code
   ```

   Leave generated CSV files under `docs/dev/benchmarking/` untracked
   per `AGENTS.md` §Workflow.

## Suggested Pull Request

**Title:** Add undo-fit rollback to Analysis and CLI

**Description (user-facing):**

This change introduces a single-level "undo last fit" operation for
EasyDiffraction projects. After running a fit you can now call
`project.analysis.undo_fit()` (Python) or
`python -m easydiffraction PROJECT_DIR undo` (CLI) to roll the project
back to the parameter values and uncertainties that were captured just
before the last fit started. The operation is safe to call on a project
that has nothing to undo — calling it twice in a row, or calling it on a
project that has never been fit, simply prints "No fit to undo." and
leaves everything unchanged.

The undo is single-level: only the most recent committed fit is rolled
back. Fit bounds, aliases, constraints, the minimizer choice, and the
fit mode are all left untouched — undo only reverses fit output, not fit
configuration. Bayesian posterior summaries on fitted parameters are
cleared and the `analysis/results.h5` sidecar is truncated when the
rolled-back project is saved.

The CLI's `--dry` flag previews the rollback (showing how many
parameters would be restored) without writing any file. Multi-level
undo/redo and sequential-fit row-level rollback remain deferred
follow-up work.
