# Reply to Review 4: Minimizer Input/Output Split Branch

Reply to
[`minimizer-input-output-split_review-4.md`](minimizer-input-output-split_review-4.md)
for the plan at
[`minimizer-input-output-split.md`](minimizer-input-output-split.md).

This reply follows
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).

Context: Review 4 is a post-Phase-1 static review. Phase 2 has not
started. The review confirms the Phase 1 gate and raises five findings,
none marked as a blocker.

## Findings

### F1 — `FitResultBase` common-header defaults diverge from family classes

**Verdict: agree.** The split makes the old common-header defaults more
visible: `success=False`, `message=''`, and `iterations=0` now sit next
to family-specific result descriptors that deliberately use
`default=None, allow_none=True`. The same mismatch exists for Bayesian
`point_estimate_name='best_sample'` and `sampler_completed=False`.

**Decision.** Address during Phase 2 cleanup before adding the new
`fit_result` unit tests. Align the common result header and Bayesian
result-only fields with the `None`/`allow_none=True` convention so
pre-fit CIF output keeps using `?` rather than values that look like a
completed or failed fit.

### F2 — `_clear_persisted_fit_state` resets descriptors before replacing the instance

**Verdict: agree.** Calling `_clear_fit_result_projection()` on the old
instance immediately before replacing `self._fit_result` is dead work.

**Decision.** Address during Phase 2 cleanup. Keep the fresh-instance
shape and drop the redundant reset call; that preserves the paired-class
invariant and removes the wasted descriptor walk.

### F3 — `_settings_used_rows` carries an unreachable fallback branch

**Verdict: agree.** `_setting_descriptor_names` is a controlled
class-level declaration and each name should resolve to a descriptor.
The fallback branch is defensive code for an invalid internal
declaration.

**Decision.** Address during Phase 2 cleanup. Drop the fallback and let
an invalid `_setting_descriptor_names` entry fail loudly.

### F4 — Phase 2 not started; one test file expected to break

**Verdict: agree.** This is exactly the expected Phase 1 to Phase 2
gate. `test_lsq_base.py` still targets result fields that moved from
`analysis.minimizer` to `analysis.fit_result`.

**Decision.** No extra plan change needed. P2.1 remains the migration
step for the stranded tests, and P2.2 adds the missing fit-result unit
test coverage.

### F5 — Unrelated dependency cleanup landed alongside Phase 1

**Verdict: agree that it is unrelated to the input/output split ADR.**
The `essdiffraction` removal was a direct CI dependency cleanup request,
not part of this design change.

**Decision.** Keep it in the branch unless the PR owner wants a cleaner
history split. If it remains bundled, call it out explicitly in the PR
description so reviewers understand the `pixi.lock` churn is a separate
CI/dependency cleanup.

## Phase 2 Carry-Forward

Before running the normal Phase 2 verification sequence, include a small
cleanup pass for F1 through F3:

1. Align pre-fit result defaults to `None` where result fields are not
   known yet.
2. Remove the redundant old-instance fit-result reset before replacing
   `self._fit_result`.
3. Remove the unreachable settings-table fallback branch.

Then proceed with the existing Phase 2 checklist:

- P2.1 test migration.
- P2.2 new `fit_result` unit tests.
- P2.3 `pixi run fix` and `pixi run check`.
- P2.4 `pixi run unit-tests`.
- P2.5 `pixi run integration-tests`.
- P2.6 `pixi run script-tests`.

## Verification

This is a static reply only. No `pixi run`, lint, build, formatter, or
test command was executed.

## Summary of files touched by this reply

- [`docs/dev/plans/minimizer-input-output-split_reply-4.md`](minimizer-input-output-split_reply-4.md)
  — this reply.
