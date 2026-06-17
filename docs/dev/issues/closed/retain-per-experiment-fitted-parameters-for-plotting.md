# 85. Retain Per-Experiment Fitted Parameters for Plotting

**Type:** Correctness / UX

**Status:** Closed.

In `single` fit mode, only the last experiment's fit results were
retained because the shared structure parameters were overwritten on
each iteration of the multi-experiment loop (`single`-with-N), so
earlier experiments could not be plotted correctly after fitting.

**Resolution:** the bug is removed by construction rather than patched
with per-experiment snapshots. Under the
[`dataset-driven-fit-modes`](../../adrs/accepted/dataset-driven-fit-modes.md)
ADR, `single` mode is restricted to **exactly one** loaded experiment
(fit-mode availability is now driven by the loaded-experiment count:
`single`/`sequential` for one experiment, `joint` for two or more). With
no multi-experiment `single` loop, there is no shared structure to
overwrite and no earlier experiment to mis-plot.

The legacy in-memory `_parameter_snapshots` store and the
`plot_param_series_from_snapshots` fallback that existed only for the
`single`-with-N path were removed as dead code. Parameter-evolution
plotting across a series is served by `sequential` fitting via
`analysis/results.csv` (`plot_param_series` / `plot_all_param_series`).

**Related:** issue 78 (resolved).
