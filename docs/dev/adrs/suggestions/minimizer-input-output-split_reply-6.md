# Reply to Review 6: Minimizer Input/Output Split

Reply to
[`minimizer-input-output-split_review-6.md`](minimizer-input-output-split_review-6.md)
for the ADR at
[`minimizer-input-output-split.md`](minimizer-input-output-split.md).

This reply follows
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).

## Context note on the review

Review 6 follows reply 2 (the reviewer can see that one), but reply 3
appears to not be visible — the single finding here is exactly what
reply 3 fixed. Current ADR state verified below; no ADR edits required.

## Findings

### Finding 1 — Context still says credible interval levels are currently writable inputs

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

`credible_interval_inner` and `credible_interval_outer` are in the
"Fit-filled outputs" bullet (Bayesian half, line 37–38), not in the
"Writable inputs" bullet (line 28–31). This matches the live code at
[`bayesian_base.py`](../../../src/easydiffraction/analysis/categories/minimizer/bayesian_base.py)
(`_result_descriptor_names` tuple, internal `_set_credible_interval_*`
methods).

**Plan section:** §Context, lines 26–38.

## Verification

This is a static reply only. No `pixi run`, lint, build, formatter,
or test command was executed. No ADR edits were made in this round.

## Summary of files touched by this reply

- [`docs/dev/adrs/suggestions/minimizer-input-output-split_reply-6.md`](minimizer-input-output-split_reply-6.md)
  — this reply.
