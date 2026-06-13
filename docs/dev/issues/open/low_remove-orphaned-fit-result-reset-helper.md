# 105. Remove Orphaned Fit-Result Reset Helper

**Priority:** `[priority] low`

**Type:** Cleanup **Source:** `minimizer-input-output-split` review 6.

`Analysis._clear_fit_result_projection` is a private method with no
callers after `_clear_persisted_fit_state` switched to replacing
`self._fit_result` with a fresh paired result instance.

**TODOs:**

- [analysis.py](src/easydiffraction/analysis/analysis.py#L1217)

**Fix:** delete the unused helper, or reintroduce a caller only if a
future fit-result reset path genuinely needs to preserve the active
instance.

**Depends on:** nothing.
