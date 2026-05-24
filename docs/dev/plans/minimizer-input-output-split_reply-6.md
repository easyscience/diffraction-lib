# Reply to Review 6: Minimizer Input/Output Split Branch

Reply to
[`minimizer-input-output-split_review-6.md`](minimizer-input-output-split_review-6.md)
for the plan at
[`minimizer-input-output-split.md`](minimizer-input-output-split.md).

This reply follows
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).

Context: Review 6 is a static review of
[`minimizer-input-output-split_reply-5.md`](minimizer-input-output-split_reply-5.md)
and the docs-only commit that added it. It raises one follow-through
finding: the review-5 deferrals should either be applied inline or
tracked in `docs/dev/issues/open.md`.

## Findings

### F1 — Deferrals from review 5 not tracked in `docs/dev/issues/open.md`

**Verdict: agree.** Deferring the dead private method and the optional
`result_kind` explanatory comment was reasonable, but the deferrals
should not live only in the review thread.

**Decision.** Track both deferred items in
[`../issues/open.md`](../issues/open.md) rather than reopen the
completed Phase 2 implementation for non-behavioural cleanup:

1. Issue 105 tracks removing the orphaned
   `Analysis._clear_fit_result_projection` helper.
2. Issue 106 tracks adding a short comment explaining why
   `FitResultBase.result_kind` keeps a concrete enum default while
   unknown result values use `None`.

This resolves the trail requested by review 6. No source files were
changed.

## Verification

This is a static reply and issue-log update only. No `pixi run`, lint,
build, formatter, or test command was executed.

## Summary of files touched by this reply

- [`../issues/open.md`](../issues/open.md) — added issues 105 and 106
  for the two deferred review-5 cleanup items.
- [`minimizer-input-output-split_reply-6.md`](minimizer-input-output-split_reply-6.md)
  — this reply.
