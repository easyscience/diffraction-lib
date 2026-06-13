# 116. Add a Static Type Checker to the Quality Gate

**Priority:** `[priority] high`

**Type:** Tooling / Correctness

The project type-annotates public signatures but runs no static type
checker (only ruff's `TC` import-placement rules). A genuine bug slipped
through as a result:
`Plotter._plot_single_crystal_posterior_predictive_summary` called
`PlotlyPlotter._get_diagonal_shape()` with no arguments while the method
requires `(minimum, maximum)`, so the single-crystal posterior-
predictive plot raised `TypeError` whenever reached. A type checker
would have flagged the wrong-arity call at lint time, without needing a
test to exercise the path — and would catch the whole class of such
errors.

**Fix:** add a checker (mypy, pyright, or `ty`) as a `pixi` task wired
into `check` and the lint CI workflow, alongside the existing ruff /
pydoclint / interrogate gates. Roll out incrementally to manage the
initial error backlog: start lenient (e.g. `--follow-imports=silent` or
a per-package allowlist) and gate only new/changed code first, then
tighten. The codebase already annotates public signatures, so it is
well-positioned.

**Depends on:** nothing. Best landed as its own focused effort because
enabling a checker on an existing codebase surfaces a backlog that needs
a baseline-cleanup plan.

**Recommended-priority note:** A real wrong-arity `TypeError` already shipped because nothing catches it; high leverage — land as its own baseline-cleanup effort. **Tier 2 (tooling that prevents whole bug classes).**
