# Reply to Review 3: Minimizer Input/Output Split Plan

Reply to
[`minimizer-input-output-split_review-3.md`](minimizer-input-output-split_review-3.md)
for the plan at
[`minimizer-input-output-split.md`](minimizer-input-output-split.md).

This reply follows
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).

## Findings

### Finding 1 — CIF ordering steps still contradictory

**Verdict: partial — intent was correct in reply 2, wording could be
misread.**

The reviewer acknowledges review 2 F1 and F2 are addressed and
re-raises only the CIF-ordering concern. Reading the post-reply-2
text, P1.11 did already state the conditional contract explicitly
("`self.fit_result` is **conditionally** included only when persisted
fit state exists … Do not promote `fit_result` to an unconditional
category"). However, the same step opened with a paragraph about the
**read** side that mentioned "after `_minimizer.*`" and the reviewer
appears to have carried that ordering language across into the
**emit** side, where it is exactly what we do not want.

**Action taken.** Rewrote P1.11 with the no-reordering rule as the
**first** sentence of the step, before any read/emit detail:

> **No category-list reordering is performed in this step.** Neither
> `Analysis._serializable_categories()` nor
> `Analysis._fit_state_categories()` is restructured. `fit_result`
> stays conditionally included by `_fit_state_categories()` only
> when `self._has_persisted_fit_state()` is true — exactly as today.
> Pre-fit projects continue to emit no `_fit_result.*` block.

The remaining bullets list only content-level changes (which
descriptors flow through emit/read, the legacy-tag rejection
message), and each is explicitly framed as "no reordering, no new
call" or "no code change is required here". The earlier phrasing
about the read order being "already correct" was retained but moved
below the no-reordering rule and reframed as a confirmation rather
than a directive.

P1.12 was already clear that `_fit_state_categories()` is unchanged
(it just walks the paired instance after P1.6 wires it). No further
P1.12 edits.

**Plan section:** P1.11 (rewritten with the no-reordering rule as
the first paragraph; intent unchanged but explicit).

## Verification

This is a static reply only. No `pixi run`, lint, build, formatter,
or test command was executed.

## Summary of files touched by this reply

- [`docs/dev/plans/minimizer-input-output-split.md`](minimizer-input-output-split.md)
  — P1.11 reworded to lead with the no-reordering rule.
- [`docs/dev/plans/minimizer-input-output-split_reply-3.md`](minimizer-input-output-split_reply-3.md)
  — this reply.
