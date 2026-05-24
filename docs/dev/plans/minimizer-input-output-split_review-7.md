# Review 7: Reply to Review 6

Reviewed reply:
[`minimizer-input-output-split_reply-6.md`](minimizer-input-output-split_reply-6.md)

Original review:
[`minimizer-input-output-split_review-6.md`](minimizer-input-output-split_review-6.md)

Reviewed plan:
[`minimizer-input-output-split.md`](minimizer-input-output-split.md)

Reviewed ADR:
[`../adrs/accepted/minimizer-input-output-split.md`](../adrs/accepted/minimizer-input-output-split.md)

This review follows
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).

Per the reviewer rule, **no tests, `pixi run fix`, `pixi run check`, or
any other build/verification command was executed**. This is a static
read of the single new commit since review 6 (`d5c03b01d Reply to
minimizer input-output review 6`).

## Scope

One new commit since review 6, docs-only:

```text
docs/dev/issues/open.md                                  +45
docs/dev/plans/minimizer-input-output-split_reply-6.md   +48   (new)
docs/dev/plans/minimizer-input-output-split_review-6.md +172   (new)
```

No source or test files moved.

## Summary

Reply 6 closes the only finding from review 6 by adding two
priority-ordered entries to
[`docs/dev/issues/open.md`](../issues/open.md): issue 105 (orphaned
helper) and issue 106 (`result_kind` default rationale). Both entries
are well-formed, sequentially numbered, and listed in the summary
table. No new findings.

## Verification of reply-6 action

### Review-6 F1 — Deferrals from review 5 not tracked in `open.md`

**Reply verdict.** Agree; track in `open.md`.

**Current state.**
[`open.md:1785-1827`](../issues/open.md:1785) now contains two new
entries:

- **Issue 105 — Remove Orphaned Fit-Result Reset Helper.** Source
  attribution: `minimizer-input-output-split` review 6. Points at
  [`analysis.py#L1217`](../../../src/easydiffraction/analysis/analysis.py#L1217),
  which is the exact definition line of the orphaned method.
  Description and proposed fix match review-5 F1.
- **Issue 106 — Document `FitResultBase.result_kind` Default
  Rationale.** Source attribution: same. Points at
  [`base.py#L44`](../../../src/easydiffraction/analysis/categories/fit_result/base.py#L44),
  the descriptor construction line. Description matches review-5 F4
  and reply-5's intent paragraph.

Both rows also appear in the summary table at the foot of `open.md`
with severity 🟢 Low and the correct types (Cleanup, Code
readability). Numbering is contiguous with the prior tail (104 → 105 →
106).

One minor nit on attribution accuracy: the substantive findings
originated in review 5 (F1 dead method, F4 `result_kind` comment).
Review 6 only flagged the tracking gap. Sourcing both new issues to
"review 6" is defensible (review 6 caused the issue entries to be
created) and not worth correcting; the pointers and descriptions are
right, which is what matters for a future contributor following the
trail.

Resolved.

## Findings (this review)

None. The action requested by review 6 was applied verbatim; the entry
format matches the surrounding entries; the cross-references between
code and `open.md` are accurate; the summary table is updated.

The substantive code review from review 5 still stands: paired-class
invariant is solid, legacy-tag rejection is comprehensive, new
fit_result unit tests cover the required behaviour, migration greps
return clean. Nothing has changed since.

## Recommended next steps

1. **Open the PR.** No remaining blockers. Plan is fully `[x]`. PR
   description (per the post-reply-5 amendment) is accurate. Both
   deferred cleanups are tracked in `open.md` and can be picked up
   independently of this PR.
2. **CI is the next gate.** The reviewer chain has not run any `pixi
   run` command across reviews 4-7; trust the author's Phase 2 pass
   and gate on the merge pipeline.

## Verification commands run for this review

Static reads only:

```text
git log --oneline cf7c97369..HEAD                # 1 new commit (d5c03b01d)
git show --stat d5c03b01d                        # docs-only
git show d5c03b01d -- docs/dev/issues/open.md    # exact added entries
grep -nE '^## (105|106)\.' docs/dev/issues/open.md   # both present, sequential
grep -nE '^\| (105|106) '   docs/dev/issues/open.md  # both in summary table
git grep -nE _clear_fit_result_projection src/ tests/  # still 1 hit
                                                       # (definition only — by design,
                                                       # tracked as issue 105)
```

No `pixi run fix`, `pixi run check`, `pixi run unit-tests`,
`pixi run integration-tests`, or `pixi run script-tests` was executed.
