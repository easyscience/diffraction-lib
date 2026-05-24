# Review 6: Reply to Review 5

Reviewed reply:
[`minimizer-input-output-split_reply-5.md`](minimizer-input-output-split_reply-5.md)

Original review:
[`minimizer-input-output-split_review-5.md`](minimizer-input-output-split_review-5.md)

Reviewed plan:
[`minimizer-input-output-split.md`](minimizer-input-output-split.md)

Reviewed ADR:
[`../adrs/accepted/minimizer-input-output-split.md`](../adrs/accepted/minimizer-input-output-split.md)

This review follows
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).

Per the reviewer rule, **no tests, `pixi run fix`, `pixi run check`, or
any other build/verification command was executed**. This is a static
read of the single new commit since review 5 (`cf7c97369 Reply to
minimizer input-output review 5`) plus the touched docs.

## Scope

One new commit since review 5. It touches docs only:

```text
docs/dev/plans/minimizer-input-output-split.md            +9
docs/dev/plans/minimizer-input-output-split_reply-5.md   +72   (new)
docs/dev/plans/minimizer-input-output-split_review-5.md +297   (new)
```

No source or test files moved. The verification matrix from review 5
(paired-class invariant, legacy-tag rejection, migration greps, new
fit_result tests) is unchanged and still passes its static checks.

## Summary

Reply 5 accepts every finding ("agree" × 4) and applies the two
non-deferred ones (F2 and F3) by amending the plan's PR-description
section. F1 (dead method) and F4 (missing comment on `result_kind`) are
deferred. The reply's structure mirrors the existing reply 4 template
(one section per finding, verdict + decision + pointer), which keeps the
review thread legible.

The reply is sound. One small follow-through gap: the deferred items
(F1 and F4) are not yet logged anywhere a future contributor would
look — see F1 below.

## Per-finding assessment

### Review-5 F1 — `_clear_fit_result_projection` dead method

**Reply verdict.** Agree; defer to a follow-up cleanup.

**Current state.**
`git grep -nE _clear_fit_result_projection src/ tests/` still returns
the single definition line at
[`analysis.py:1217`](../../../src/easydiffraction/analysis/analysis.py:1217),
no callers. The deferral was applied without action.

**Assessment.** The deferral itself is defensible — a private method
with no callers has no behavioural impact and does not block merge. But
the project rule in
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md)
→ **Workflow** is explicit: "Open issues / design questions / planned
improvements live in `docs/dev/issues/open.md` (priority-ordered)."

`docs/dev/issues/open.md` does not currently contain this item.
`grep -nE _clear_fit_result_projection docs/dev/issues/open.md` returns
empty. So the deferral exists only inside this review/reply thread,
which a future contributor reading `open.md` will not see.

**Suggested follow-up.** Either (a) add a one-line entry to
`docs/dev/issues/open.md` pointing at
[`analysis.py:1217`](../../../src/easydiffraction/analysis/analysis.py:1217)
so the cleanup is queued, or (b) just delete the four lines now —
this is a private, unreferenced method, and the delete is mechanically
smaller than the issue entry. Either is fine; doing neither leaves the
dead code unowned.

### Review-5 F2 — Lint-driven refactors bundled in Phase 2

**Reply verdict.** Agree; keep bundled, call them out in the PR
description.

**Current state.**
[`minimizer-input-output-split.md:664-672`](minimizer-input-output-split.md:664)
now carries this paragraph:

> Incidental cleanup also bundled in this branch: the unused
> `essdiffraction` development dependency is removed, and a handful of
> unrelated functions are split into helpers to satisfy the project's
> complexity thresholds during Phase 2 verification:
> `singleton.ConstraintsHandler.apply_constraints`,
> `analysis.sequential._fit_worker`,
> `display.plotting._posterior_predictive_*`, and
> `calculators.{crysfml,pdffit}._calculate_pattern`.

The four refactor sites enumerated in review 5 F2 are listed verbatim.
Resolved.

### Review-5 F3 — `essdiffraction` removal still bundled

**Reply verdict.** Agree; PR description now mentions it.

**Current state.** Same plan paragraph above, lead sentence: "the
unused `essdiffraction` development dependency is removed". Resolved.

### Review-5 F4 — `FitResultBase.result_kind` exception undocumented

**Reply verdict.** Agree, but informational; defer.

**Current state.**
[`base.py:44-54`](../../../src/easydiffraction/analysis/categories/fit_result/base.py:44)
is unchanged; no comment was added. As with F1, the deferral is
reasonable, but `docs/dev/issues/open.md` does not capture it.

**Assessment.** Informational only; lower priority than F1 (which is
unowned dead code). If F1 is logged in `open.md`, F4 should be too. If
F1 is deleted instead, F4 can stay deferred without an issue entry —
it's a "nice to have" comment, not a code-quality concern.

## Findings (this review)

### F1 — Deferrals from review 5 not tracked in `docs/dev/issues/open.md`

The project workflow rule routes deferred cleanup items through
`docs/dev/issues/open.md`. Reply 5 defers two findings (review-5 F1
dead method, review-5 F4 missing comment) without adding either to
that file. Without the log entry, both items live only inside this
review thread; once the PR merges and the plan is deleted (per the
ADR-promotion precedent at P1.16 — deliberation artefacts get
dropped), the deferral context is gone.

**Suggested action.** Either:

- Add one short line to `docs/dev/issues/open.md` per deferred item
  (with a file-line pointer), or
- Apply the cleanup inline before opening the PR (F1 is a four-line
  delete; F4 is a one-line comment).

Either route closes the trail. The first preserves history, the second
removes the obligation. Both are equally acceptable.

This is the only outstanding observation from this review round.
Nothing about the code, tests, or paired-class plumbing has changed
since review 5; that assessment still stands.

## Recommended next steps

1. **Resolve the tracking gap above.** Pick one of the two routes per
   deferred finding.
2. **Open the PR.** No blockers found; CI is the next gate. The plan's
   "Suggested Pull Request" section is now complete and accurate
   (post-reply-5 PR-description amendment).

## Verification commands run for this review

Static reads only:

```text
git log --oneline a2857d9d6..HEAD                      # 1 new commit (cf7c97369)
git show --stat cf7c97369                              # docs-only
git show cf7c97369 -- docs/dev/plans/minimizer-input-output-split.md
git grep -nE _clear_fit_result_projection src/ tests/  # 1 hit (definition only)
grep -nE _clear_fit_result_projection docs/dev/issues/open.md  # empty
test -f docs/dev/issues/open.md                        # exists
```

No `pixi run fix`, `pixi run check`, `pixi run unit-tests`,
`pixi run integration-tests`, or `pixi run script-tests` was executed.
