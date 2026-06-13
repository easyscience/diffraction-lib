# 85. Retain Per-Experiment Fitted Parameters for Plotting

**Priority:** `[priority] highest`

**Type:** Correctness / UX

In `single` fit mode, only the last experiment's fit results are
retained because structure parameters are overwritten on each iteration.
This means earlier experiments cannot be plotted correctly after
fitting.

**Fix:** after fitting each experiment, store a snapshot of its fitted
parameters (both structure and experiment) so that any experiment can be
re-plotted or inspected later. Also clarify: does `fit_results` need to
keep the last mutable parameter set after adding a snapshot?

**Depends on:** nothing (issue 78 resolved).

**Recommended-priority note:** In `single` mode only the last experiment's results survive, so earlier experiments plot incorrectly after fitting. **Tier 1 (do first).**
