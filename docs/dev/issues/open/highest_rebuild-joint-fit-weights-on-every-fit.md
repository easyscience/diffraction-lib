# 3. Rebuild Joint-Fit Weights on Every Fit

**Priority:** `[priority] highest`

**Type:** Fragility

`joint_fit` is created once when `fit.mode` becomes `'joint'`. If
experiments are added, removed, or renamed afterwards, the weight
collection is stale. Joint fitting can fail with missing keys or run
with incorrect weights.

**Fix:** rebuild or validate `joint_fit` at the start of every joint
fit. At minimum, `fit()` should assert that the weight keys exactly
match `project.experiments.names`.

**Depends on:** nothing.

**Recommended-priority note:** Joint-fit weight safety (paired with #15): invalid or all-zero weights currently produce `nan` / division-by-zero straight into the minimiser — a crash plus silent corruption; self-contained. **Tier 1 (do first)** in the 2026-06-10 recommended-priorities analysis.
