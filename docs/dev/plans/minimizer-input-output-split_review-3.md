# Review 3: Minimizer Input/Output Split Plan

## Findings

No issues found.

Review 2's remaining concerns are addressed in the current plan:

- P1.1 adds `_result_descriptor_names` and `_reset_result_descriptors()`
  to `FitResultBase` before P1.6 retargets reset calls.
- P1.15 and P2.1 now include an explicit migration table for collapsed
  field names (`runtime_seconds` → `fitting_time`,
  `iterations_performed` → `iterations`) and moved fields.
- P1.11 now explicitly preserves the existing conditional
  `_fit_state_categories()` emission path and says no
  `_serializable_categories()` reordering is performed, so pre-fit
  projects keep emitting no `_fit_result.*` block.

## Checks

Skipped by instruction: this is a static plan review only. I did not run
tests, `pixi run fix`, `pixi run check`, or any other build or
verification command.
