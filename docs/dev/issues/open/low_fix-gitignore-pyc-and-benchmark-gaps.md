# 163. Fix `.gitignore` Gaps (`.pyc` Pattern and `benchmark.json`)

**Priority:** `[priority] low`

**Type:** Hygiene

Two small `.gitignore` gaps:

- `.gitignore` line `.pyc` ignores only a file literally named `.pyc`,
  not `*.pyc` (intended). `__pycache__/` covers the common case, so the
  rule as written does nothing.
- The `benchmarks` pixi task writes `benchmark.json` to the repo root,
  but `.gitignore` has no entry for it, so it can be staged
  accidentally.

**Fix:** correct the `.pyc` pattern to `*.pyc` and add `benchmark.json`.

**Note:** an earlier version of this issue also asked to delete the
`absorption/` package as an empty stub. That is now **obsolete** — the
package contains implemented source (`base.py`, `cylinder_hewat.py`,
`none.py`, `factory.py`) from the sample-absorption feature (issue 119),
so it must **not** be removed.
