# 154. Remove Dead Auto-Populate Branch in `_run_joint`

**Priority:** `[priority] low`

**Type:** Dead code

`_run_fit_mode` always calls `_prepare_joint_fit()` (which populates all
`joint_fit` rows with `weight=1.0`) immediately before `_run_joint()`,
so by the time `_run_joint` runs `len(self._joint_fit)` is never 0 and
its `if not len(self._joint_fit): ... create(weight=0.5)` block is
unreachable. It also disagrees with the live default weight (0.5 vs
1.0).

**Fix:** remove the dead block (or, if it must stay as a guard, align
the default weight to 1.0).

**TODOs / locations:**

- [analysis.py](../../../../src/easydiffraction/analysis/analysis.py#L2761)

**Depends on:** related to issues 3, 15.
