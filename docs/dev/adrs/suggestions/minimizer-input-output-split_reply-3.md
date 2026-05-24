# Reply to Review 3: Minimizer Input/Output Split

Reply to
[`minimizer-input-output-split_review-3.md`](minimizer-input-output-split_review-3.md)
for the ADR at
[`minimizer-input-output-split.md`](minimizer-input-output-split.md).

This reply follows
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).

## Context note on the review

The review header again records that the preceding reply
(`_reply-2.md`) was not visible. After auditing the current ADR
against each finding, F1 and F3 reference text that was already
revised in reply-2; the cited line numbers no longer correspond to
text matching the complaint. F2 is a real bug introduced in the
original draft and never fixed by either reply — the §Context list
incorrectly attributes user-writable status to the credible-interval
levels that the live code exposes as outputs.

F2 triggers an ADR edit. F1 and F3 are confirmed already-addressed
with current line numbers and quoted text.

## Findings

### Finding 1 — Writable arbitrary credible interval levels persist into misleading column names

**Verdict: partial — substantively resolved in reply 2.**

The review reads the ADR as still promoting the credible-interval
levels to user settings. The reply-2 edits demoted them back to the
output side, attached to `BayesianFitResult`. Current ADR state
(verified by `grep -n credible_interval
docs/dev/adrs/suggestions/minimizer-input-output-split.md`):

- Line 140: §2 paragraph reads "`credible_interval_inner` and
  `credible_interval_outer` **stay on the output side** in this ADR,
  attached to `BayesianFitResult` (see below)".
- Line 163: `BayesianFitResult` field list includes
  `credible_interval_inner`, `credible_interval_outer`.
- Lines 236–237: the Bayesian CIF example shows
  `_fit_result.credible_interval_inner    0.68` and
  `_fit_result.credible_interval_outer    0.95` (no longer under
  `_minimizer.*`).
- §"Deferred Work" carries the combined level+naming follow-on:
  > Promoting the levels to user settings requires generalising the
  > column naming at the same time to avoid the data-integrity hole
  > where a `0.50` level lands in a column called
  > `posterior_interval_68_low`. Both pieces belong in a follow-on
  > ADR so this proposal stays focused on the input/output split.

The data-integrity hole the reviewer is concerned about cannot occur
under the current ADR text — the levels are fixed at `0.68` / `0.95`,
matching the column names. The cited line range (`:138-153`) maps to
a paragraph that, in the current file, says the opposite of what the
review attributes to it. No further ADR change.

**Plan section:** §2 (lines 138–151), §3 Bayesian CIF example
(lines 236–237), §"Deferred Work".

### Finding 2 — Context list still describes credible-interval levels as currently writable

**Verdict: agree — real bug, dating from the original draft.**

The §Context list at lines 26–37 enumerates the **current live**
shape of `analysis.minimizer`. Since the original draft, the
"Writable inputs" bullet has incorrectly included
`credible_interval_inner` and `credible_interval_outer`. The live
code in
[`bayesian_base.py`](../../../src/easydiffraction/analysis/categories/minimizer/bayesian_base.py)
exposes these only via the internal `_set_credible_interval_*`
methods and lists them under `_result_descriptor_names`, not
`_setting_descriptor_names`. Neither reply 1 nor reply 2 corrected
the §Context list itself, even after both replies adjusted the
downstream decisions.

**Action taken.** Moved the two field names from "Writable inputs"
to "Fit-filled outputs (no public setter, only `_set_*` internals)"
in the §Context list. The §Context now accurately mirrors the live
category surface, and the rest of the ADR (which already treats them
as outputs after reply 2) reads consistently end-to-end.

**Plan section:** §Context, lines 26–37 (one field move).

### Finding 3 — Context still presents `objective_value` and `reduced_chi_square` as a duplicate pair

**Verdict: partial — substantively resolved in reply 2.**

Reply 2 rewrote the §Context table to add a fourth "Relationship"
column distinguishing real duplications from cross-category
misplacement. Current ADR state (lines 40–53):

```
| Output concept | Field on `analysis.minimizer` | Field on `analysis.fit_result` | Relationship |
| Wall time | `runtime_seconds` | `fitting_time` | Real duplication — same scalar in two places. |
| Iteration count | `iterations_performed` (LSQ) | `iterations` | Real duplication — same scalar in two places. |
| Objective vs reduced χ² | `objective_value` (raw χ²) | `reduced_chi_square` (χ² / dof) | Cross-category misplacement — two related but distinct scalars where the raw value sits on `minimizer` instead of with the rest of the fit outputs. |
```

The third row no longer claims `objective_value` and
`reduced_chi_square` are duplicates; it explicitly describes them as
two distinct scalars with one of them sitting in the wrong category.
The surrounding sentence at line 49–53 reads "fit-output content
split across `minimizer` and `fit_result` (whether the two scalars
per row are the same value or not)". §2 then resolves each row
explicitly.

The cited line range (`:40-46`) lands inside the rewritten table; the
phrasing the reviewer attributes to those lines (a claim that all
three rows are duplicates) no longer exists in the file. No further
ADR change.

**Plan section:** §Context table (lines 43–47), §"Positive" bullet
(lines 294–298, already correct).

## Verification

This is a static reply only. No `pixi run`, lint, build, formatter,
or test command was executed.

## Summary of files touched by this reply

- [`docs/dev/adrs/suggestions/minimizer-input-output-split.md`](minimizer-input-output-split.md)
  — §Context "Writable inputs" / "Fit-filled outputs" lists corrected
  for the credible-interval fields (F2).
- [`docs/dev/adrs/suggestions/minimizer-input-output-split_reply-3.md`](minimizer-input-output-split_reply-3.md)
  — this reply.
