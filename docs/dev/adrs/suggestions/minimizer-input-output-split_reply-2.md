# Reply to Review 2: Minimizer Input/Output Split

Reply to
[`minimizer-input-output-split_review-2.md`](minimizer-input-output-split_review-2.md)
for the ADR at
[`minimizer-input-output-split.md`](minimizer-input-output-split.md).

This reply follows
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).

## Context note on the review

The review header records that `_reply-1.md` was not visible when
review 2 was prepared, only the direct edits to the ADR. After
auditing the current ADR with `git grep` against each of the cited
phrases, three of the four findings (F1, F3-part, F4) reference text
that no longer appears in the file — they describe the pre-reply-1
shape of the ADR. F2 is a genuinely new and substantive concern; the
half of F3 that talks about the §Context table phrasing is also a
real issue worth addressing.

Each finding is handled below: F2 and the §Context half of F3 trigger
real ADR edits; F1, F4, and the §Consequences half of F3 are
confirmed-already-addressed with current line numbers cited.

## Findings

### Finding 1 — `fit_result` switchable inconsistency

**Verdict: partial — substantively resolved in reply 1; documenting
current state here.**

The review cites lines that the reply-1 edits already replaced.
Current ADR state (verified by `grep -n switchable
docs/dev/adrs/suggestions/minimizer-input-output-split.md`):

- Line 88: "**`fit_result` is not a user-facing switchable
  category.**"
- Line 96: §1 cross-references
  `switchable-category-owned-selectors.md` for the documented
  exception.
- Line 280-282: §6 reiterates "The paired `fit_result` is not a
  user-facing switchable: there is no `fit_result.type` and no
  `fit_result.show_supported()`".
- Line 345: `switchable-category-owned-selectors.md` is listed under
  "ADRs amended" with the explicit exception text:
  > §1 ("The category owns its selector") gains a paragraph carving
  > out one documented exception: a category that is fully determined
  > by another category's `type` (today only `fit_result`, derived
  > from `minimizer.type`) is allowed to omit `category.type` and
  > `category.show_supported()`.

No remaining text calls `fit_result` a switchable category, and the
amended-ADR list does include the selector ADR. The cited line
numbers (`:269-278`, `:302-311`, `:342-345`, `:320-333`) do not match
the corresponding ranges in the current file. No further ADR change.

**Plan section:** §1 (lines 80–127), §6 (lines 273–286), §"ADRs
amended" (lines 339–357) — all carry the reply-1 edits.

### Finding 2 — Configurable credible-interval levels would mislabel persisted columns

**Verdict: agree — data-integrity concern, real and substantive.**

Reply 1 promoted `credible_interval_inner` / `credible_interval_outer`
to user-writable settings while keeping the fixed
`posterior_interval_68_low/high` / `posterior_interval_95_low/high`
per-parameter column names. The reviewer correctly observes that this
allows, for example, a user-set `0.50` interval to be persisted under
a column named `posterior_interval_68_low`. That is a data-integrity
hole, not a UX warning surface.

**Action taken.** Demoted the two interval-level fields back to the
output side. They now live on `BayesianFitResult` (alongside
`acceptance_rate_mean`, `gelman_rubin_max`, etc.) with the fixed
values `0.68` and `0.95`, matching the column names. The §2 paragraph
that introduced the promotion is rewritten to explain the choice
explicitly:

> Promoting the levels to user-writable settings would let the user
> choose a 50% interval that then gets persisted under a column named
> `posterior_interval_68_low` — a data-integrity problem rather than a
> UX problem. A future suggestion ADR can promote them to settings
> and generalise the column naming (e.g.
> `posterior_interval_low_<level>`) in one combined change; doing one
> without the other is unsafe and out of scope here.

The Bayesian field list in §2 moved the two fields from `minimizer`
to `BayesianFitResult`. The Bayesian CIF example in §3 moved the two
`_minimizer.credible_interval_*` lines to `_fit_result.*`. The
Deferred-Work entry was rewritten to make the combined level+naming
follow-on explicit.

This resolves the only "settings-only minimizer" boundary question
that survived reply 1 in the opposite direction from reply 1, taking
the "or another summary-configuration category" branch that review 1
F3 originally offered.

**Plan section:** §2 (lines 131–151), §3 Bayesian example
(lines 217–240), §"Deferred Work" (interval-naming entry).

### Finding 3 — `objective_value` / `reduced_chi_square` framing

**Verdict: agree on the §Context phrasing; already addressed in
§Consequences.**

The §Consequences "Positive" bullet was rewritten in reply 1 to say
explicitly that the `objective_value`/`reduced_chi_square` pair is
**not** a duplication (current lines 294–298 — verified by `grep -n
"real duplications"`). That half is already correct.

The §Context table did still call all three rows an "overlap" without
distinguishing real duplications from cross-category misplacement,
which is genuinely inconsistent with the §2 clarification. The
reviewer is right to flag it.

**Action taken.** Rewrote the §Context table to add a fourth
"Relationship" column that classifies each row:

- Wall time → real duplication
- Iteration count → real duplication
- Objective vs reduced χ² → cross-category misplacement (two related
  but distinct scalars where the raw χ² sits on `minimizer` instead
  of with the rest of the fit outputs)

The surrounding sentence now reads "fit-output content split across
`minimizer` and `fit_result` (whether the two scalars per row are the
same value or not). §2 resolves each row above explicitly." This
removes the implicit "all three are duplicates" claim while keeping
the table as the entry point for the resolution in §2.

**Plan section:** §Context (lines 40–55), §"Positive" bullet
(lines 294–298 — unchanged, already correct).

### Finding 4 — `analysis.show_fit_summary()` bypasses display facade

**Verdict: partial — substantively resolved in reply 1; documenting
current state here.**

Reply 1 removed the new `analysis.show_fit_summary()` method and
extended the existing `project.display.fit.results()` entry point
instead. Current ADR state:

- Lines 255–262: §4 says "A small UX win is added under the accepted
  display facade ([`display-ux.md`](../accepted/display-ux.md)): the
  existing `project.display.fit.results()` entry point gains a
  'Settings used' table above the existing results tables, populated
  from `analysis.minimizer.*`. No new `Analysis`-level display method
  is added".
- Line 313–314: §"Trade-offs" cites `project.display.fit.results()`
  as the mitigation (not `analysis.show_fit_summary()`).
- Lines 352–356: `display-ux.md` is listed under "ADRs amended" with
  the explicit extension text.

`grep -n show_fit_summary
docs/dev/adrs/suggestions/minimizer-input-output-split.md` returns
zero hits. The cited line numbers (`:255-258`, `:304-307`,
`:320-333`) do not match the corresponding ranges in the current
file. No further ADR change.

**Plan section:** §4 (lines 245–262), §"Trade-offs" (line 313),
§"ADRs amended" (lines 352–356) — all carry the reply-1 edits.

## Verification

This is a static reply only. No `pixi run`, lint, build, formatter,
or test command was executed.

## Summary of files touched by this reply

- [`docs/dev/adrs/suggestions/minimizer-input-output-split.md`](minimizer-input-output-split.md)
  — ADR updated for F2 (demote credible intervals back to outputs) and
  the §Context half of F3 (table phrasing).
- [`docs/dev/adrs/suggestions/minimizer-input-output-split_reply-2.md`](minimizer-input-output-split_reply-2.md)
  — this reply.
