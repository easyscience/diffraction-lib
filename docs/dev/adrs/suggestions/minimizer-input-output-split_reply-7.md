# Reply to Review 7: Minimizer Input/Output Split

Reply to
[`minimizer-input-output-split_review-7.md`](minimizer-input-output-split_review-7.md)
for the ADR at
[`minimizer-input-output-split.md`](minimizer-input-output-split.md).

This reply follows
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).

## Verdict

Review 7 records no findings. Acknowledged; the ADR is unchanged in
this round.

The reviewer's summary confirms the four substantive properties of
the current ADR:

- `analysis.minimizer` stays input-only.
- Scalar fit outputs move to the paired internal `analysis.fit_result`
  projection.
- The selector-contract exception is documented (both in §1 of this
  ADR and as an entry under "ADRs amended" against
  `switchable-category-owned-selectors.md`).
- Credible interval levels stay on the output side at the fixed
  `0.68` / `0.95` values, with the combined level+naming promotion
  deferred to a follow-on ADR.
- The §Context table classifies the two real duplications (wall
  time, iteration count) separately from the cross-category
  misplacement of raw χ² vs reduced χ².

## Next steps

The ADR is ready to move from `docs/dev/adrs/suggestions/` to
`docs/dev/adrs/accepted/` whenever the maintainer decides to promote
it, at which point an implementation plan
(`docs/dev/plans/minimizer-input-output-split.md`) can be drafted
using the same slug.

## Verification

This is a static reply only. No `pixi run`, lint, build, formatter,
or test command was executed. No ADR edits were made in this round.

## Summary of files touched by this reply

- [`docs/dev/adrs/suggestions/minimizer-input-output-split_reply-7.md`](minimizer-input-output-split_reply-7.md)
  — this reply.
