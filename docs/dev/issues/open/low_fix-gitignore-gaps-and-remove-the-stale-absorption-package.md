# 163. Fix `.gitignore` Gaps and Remove the Stale `absorption/` Package

**Priority:** `[priority] low`

**Type:** Hygiene

Several small repository-hygiene gaps:

- `.gitignore` line `.pyc` ignores only a file literally named `.pyc`,
  not `*.pyc` (intended). `__pycache__/` covers the common case, so the
  rule as written does nothing.
- The `benchmarks` pixi task writes `benchmark.json` to the repo root,
  but `.gitignore` has no entry for it, so it can be staged
  accidentally.
- `src/easydiffraction/datablocks/experiment/categories/absorption/`
  contains **no tracked source** (only a stale `__pycache__/`); the
  category has no implementation yet (see issue 119). Remove the empty
  package directory until the absorption category is implemented.

**Fix:** correct the `.pyc` pattern to `*.pyc`, add `benchmark.json`,
and delete the empty `absorption/` package.

**Depends on:** nothing (absorption implementation tracked by issue
119).
