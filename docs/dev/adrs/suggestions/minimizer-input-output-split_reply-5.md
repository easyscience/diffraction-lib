# Reply to Review 5: Minimizer Input/Output Split

Reply to
[`minimizer-input-output-split_review-5.md`](minimizer-input-output-split_review-5.md)
for the ADR at
[`minimizer-input-output-split.md`](minimizer-input-output-split.md).

This reply follows
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).

## Context note on the review

Review 5 records that `_reply-2.md` was not visible. Both findings
repeat issues that were resolved by reply 3 (F1, §Context list move
of credible intervals from "Writable inputs" to "Fit-filled outputs")
and reply 2 (F2, §Context table gaining the "Relationship" column).
Current line numbers verified below by `sed`/`grep`. No ADR edits are
required for review 5.

## Findings

### Finding 1 — Context still says credible intervals are currently writable

**Verdict: confirmed addressed in reply 3 (no further change).**

`sed -n '26,38p' docs/dev/adrs/suggestions/minimizer-input-output-split.md`
returns:

```
The current shape on the live category surfaces:

- **Writable inputs:** `max_iterations` (LSQ); `sampling_steps`,
  `burn_in_steps`, `thinning_interval`, `population_size`,
  `parallel_workers`, `initialization_method`, `random_seed`
  (Bayesian).
- **Fit-filled outputs (no public setter, only `_set_*` internals):**
  `objective_name`, `objective_value`, `n_data_points`, `n_parameters`,
  `n_free_parameters`, `degrees_of_freedom`, `covariance_available`,
  `correlation_available`, `runtime_seconds`, `iterations_performed`,
  `exit_reason` (LSQ); `runtime_seconds`, `point_estimate_name`,
  `sampler_completed`, `credible_interval_inner`,
  `credible_interval_outer`, `acceptance_rate_mean`,
```

`credible_interval_inner` and `credible_interval_outer` appear under
"Fit-filled outputs" (line 37–38), not under "Writable inputs"
(line 28–31). This matches the live code in
[`bayesian_base.py`](../../../src/easydiffraction/analysis/categories/minimizer/bayesian_base.py)
where the two fields appear in `_result_descriptor_names` and expose
only internal `_set_credible_interval_*` methods.

**Plan section:** §Context lists, lines 26–38.

### Finding 2 — Context still presents `objective_value` / `reduced_chi_square` as a duplicate pair

**Verdict: confirmed addressed in reply 2 (no further change).**

`sed -n '40,47p' docs/dev/adrs/suggestions/minimizer-input-output-split.md`
returns:

```
Three current output fields straddle `analysis.minimizer` and
`analysis.fit_result`:

| Output concept | Field on `analysis.minimizer` | Field on `analysis.fit_result` | Relationship |
| -------------- | ----------------------------- | ------------------------------ | ------------ |
| Wall time | `runtime_seconds` | `fitting_time` | Real duplication — same scalar in two places. |
| Iteration count | `iterations_performed` (LSQ) | `iterations` | Real duplication — same scalar in two places. |
| Objective vs reduced χ² | `objective_value` (raw χ²) | `reduced_chi_square` (χ² / dof) | Cross-category misplacement — two related but distinct scalars where the raw value sits on `minimizer` instead of with the rest of the fit outputs. |
```

The third row classifies the χ² pair as "Cross-category misplacement
— two related but distinct scalars", not as a duplication. The
intro sentence reads "Three current output fields straddle …", not
"Three of the output fields already overlap" as in the original.

**Plan section:** §Context table, lines 43–47.

## Process note

Both findings here describe text that no longer appears in the file
after reply 2 and reply 3. If the reviewer cannot see the reply
files, the easiest signal is that every reply file lists a "Summary
of files touched" section with the exact ADR sections and line
ranges it edited; reading the most recent `_reply-N.md` alongside the
ADR resolves the apparent regression.

## Verification

This is a static reply only. No `pixi run`, lint, build, formatter,
or test command was executed. No ADR edits were made in this round.

## Summary of files touched by this reply

- [`docs/dev/adrs/suggestions/minimizer-input-output-split_reply-5.md`](minimizer-input-output-split_reply-5.md)
  — this reply.
