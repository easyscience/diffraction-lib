# Reply to Review 4: Minimizer Input/Output Split

Reply to
[`minimizer-input-output-split_review-4.md`](minimizer-input-output-split_review-4.md)
for the ADR at
[`minimizer-input-output-split.md`](minimizer-input-output-split.md).

This reply follows
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).

## Context note on the review

Review 4 records that it follows reply 1, but the three findings
match review 3 verbatim and reference the same pre-reply-2 text
(credible intervals "promoted" to user-writable settings; §Context
table presenting all three rows as duplicates). Reply 2 demoted the
credible intervals back to outputs, and reply 3 fixed the §Context
list and the §Context table. All three findings here describe text
that is no longer in the current ADR.

No ADR edits are required for review 4. The current state matches the
reviewer's "or" branch in each case. Each finding is documented below
with line numbers verified by `grep` against the current file.

## Findings

### Finding 1 — Writable arbitrary credible interval levels

**Verdict: confirmed addressed in reply 2 (no further change).**

The reviewer's "or" branch reads: "Please either constrain these
settings to the fixed 0.68 / 0.95 values until generalized columns
are accepted, or make the generalized persistence shape part of this
ADR." Reply 2 took the first branch. Current ADR state (verified by
`grep -n credible_interval
docs/dev/adrs/suggestions/minimizer-input-output-split.md`):

- Line 140: §2 paragraph reads: "`credible_interval_inner` and
  `credible_interval_outer` **stay on the output side** in this ADR,
  attached to `BayesianFitResult` (see below). They are persisted
  with the fixed values `0.68` and `0.95`, matching the per-parameter
  interval columns".
- Line 163: `BayesianFitResult` field list owns both fields.
- Lines 236–237: Bayesian CIF example shows
  `_fit_result.credible_interval_inner 0.68` /
  `_fit_result.credible_interval_outer 0.95` under `_fit_result.*`,
  not `_minimizer.*`.
- §"Deferred Work" carries the combined level+naming follow-on,
  explicitly saying doing one without the other is unsafe.

The data-integrity hole the reviewer is concerned about cannot occur
under the current ADR — the levels are fixed at the values that match
the column names. The cited line range (`:138-153`) maps to text
saying the levels are fixed, not the prior text saying they are
user-writable.

**Plan section:** §2 (lines 138–151), §3 Bayesian CIF example
(lines 236–237), §"Deferred Work".

### Finding 2 — Context list still describes credible-interval levels as currently writable

**Verdict: confirmed addressed in reply 3 (no further change).**

Reply 3 moved `credible_interval_inner` and `credible_interval_outer`
from the "Writable inputs" bullet to the "Fit-filled outputs" bullet
in the §Context list. Current ADR state (verified by `grep -n -A 2
"Writable inputs"`):

- Line 28–31 "Writable inputs": `max_iterations` (LSQ);
  `sampling_steps`, `burn_in_steps`, `thinning_interval`,
  `population_size`, `parallel_workers`, `initialization_method`,
  `random_seed` (Bayesian).
- Line 32–38 "Fit-filled outputs": …Bayesian list includes
  `point_estimate_name`, `sampler_completed`,
  `credible_interval_inner`, `credible_interval_outer`,
  `acceptance_rate_mean`, ….

The §Context list now matches the live code at
[`bayesian_base.py`](../../../src/easydiffraction/analysis/categories/minimizer/bayesian_base.py)
where the two fields appear in `_result_descriptor_names` and have
only internal `_set_*` methods.

**Plan section:** §Context lists (lines 26–38).

### Finding 3 — Context still presents `objective_value` and `reduced_chi_square` as a duplicate pair

**Verdict: confirmed addressed in reply 2 (no further change).**

Reply 2 rewrote the §Context table to add a "Relationship" column.
Current ADR state (verified by `sed -n '43,47p'`):

```
| Output concept | Field on `analysis.minimizer` | Field on `analysis.fit_result` | Relationship |
| -------------- | ----------------------------- | ------------------------------ | ------------ |
| Wall time | `runtime_seconds` | `fitting_time` | Real duplication — same scalar in two places. |
| Iteration count | `iterations_performed` (LSQ) | `iterations` | Real duplication — same scalar in two places. |
| Objective vs reduced χ² | `objective_value` (raw χ²) | `reduced_chi_square` (χ² / dof) | Cross-category misplacement — two related but distinct scalars where the raw value sits on `minimizer` instead of with the rest of the fit outputs. |
```

The third row no longer claims they are duplicates; it classifies the
relationship as cross-category misplacement of two distinct scalars.
The surrounding sentence at lines 49–53 reads "fit-output content
split across `minimizer` and `fit_result` (whether the two scalars
per row are the same value or not). §2 resolves each row above
explicitly."

**Plan section:** §Context table (lines 43–47).

## Process note

This is the third consecutive review whose findings describe text
that has been edited away by an earlier reply. If the review process
is not picking up replies, the most useful next step is to confirm
each reply file is being read alongside the ADR — every reply lists
its own files-touched section with the exact paths, and reading them
in order resolves the apparent regression in each round. The ADR
text after reply 3 already takes the "or" branch the reviewer
recommends in every finding above; the next review can profitably
focus on issues not yet raised.

## Verification

This is a static reply only. No `pixi run`, lint, build, formatter,
or test command was executed. No ADR edits were made in this round.

## Summary of files touched by this reply

- [`docs/dev/adrs/suggestions/minimizer-input-output-split_reply-4.md`](minimizer-input-output-split_reply-4.md)
  — this reply.
