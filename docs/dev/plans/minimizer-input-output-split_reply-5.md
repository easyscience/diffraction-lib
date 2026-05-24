# Reply to Review 5: Minimizer Input/Output Split Branch

Reply to
[`minimizer-input-output-split_review-5.md`](minimizer-input-output-split_review-5.md)
for the plan at
[`minimizer-input-output-split.md`](minimizer-input-output-split.md).

This reply follows
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).

Context: Review 5 is a post-Phase-2 static review. It reports no
blockers and lists two cleanup findings plus two informational notes.

## Findings

### F1 — `_clear_fit_result_projection` is defined but never called

**Verdict: agree.** The method became dead private code after the
reply-4 cleanup changed `_clear_persisted_fit_state` to replace
`self._fit_result` with a fresh paired instance.

**Decision.** Defer this to a follow-up cleanup rather than reopening
the completed Phase 2 implementation for a non-behavioural private
method deletion. If another code cleanup commit is made on this branch
before PR opening, deleting the method there is fine; it is not required
for merge.

### F2 — Phase 2 bundles lint-driven refactors outside the split

**Verdict: agree.** These changes are outside the conceptual
minimizer/fit-result split. They were a direct result of the Phase 2
`pixi run check` complexity gate, and they preserve behaviour while
following the repository rule to refactor rather than raise or silence
lint thresholds.

**Decision.** Keep the refactors bundled in this branch instead of
rewriting history or splitting them now. The plan's suggested PR
description has been updated to call them out explicitly under
"Incidental cleanup" so reviewers know why unrelated files changed.

### F3 — `essdiffraction` removal is still bundled

**Verdict: agree.** This remains unrelated to the input/output split and
was a separate CI dependency cleanup request.

**Decision.** Keep it bundled, matching the reply-4 decision. The plan's
suggested PR description now mentions the `essdiffraction` removal
alongside the lint-driven refactors.

### F4 — `FitResultBase.result_kind` exception undocumented

**Verdict: agree, but treat as informational.** `result_kind` needs a
valid enum default because it is used to decide deterministic versus
Bayesian projection handling. The `None`/`allow_none=True` convention is
still correct for result values that are unknown before a fit.

**Decision.** Defer the optional explanatory comment to a follow-up. The
current behaviour is intentional, tested through the fit-result unit
tests, and not a merge blocker.

## Verification

This is a static reply and PR-description update only. No `pixi run`,
lint, build, formatter, or test command was executed.

## Summary of files touched by this reply

- [`docs/dev/plans/minimizer-input-output-split.md`](minimizer-input-output-split.md)
  — updated the suggested PR description with the incidental cleanup
  note requested by review 5.
- [`docs/dev/plans/minimizer-input-output-split_reply-5.md`](minimizer-input-output-split_reply-5.md)
  — this reply.
