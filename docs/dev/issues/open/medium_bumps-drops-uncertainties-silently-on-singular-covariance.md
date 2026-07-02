# 141. BUMPS Drops Uncertainties Silently on Singular Covariance

**Priority:** `[priority] medium`

**Type:** Correctness / Silent failure

`_compute_covariance` catches `np.linalg.LinAlgError` and returns
`(None, None)`; `_sync_result_to_parameters` then sets every parameter
`uncertainty = None`. A successful BUMPS fit whose Jacobian is
rank-deficient therefore reports parameter values with blank
uncertainties and no message explaining why, so a non-programmer
scientist cannot distinguish "no uncertainty computed" from a bug.

**Fix:** emit a deferred warning (via `_warn_after_tracking`) when
covariance computation fails, so the missing uncertainties are
explained.

**TODOs / locations:**

- [bumps.py](../../../../src/easydiffraction/analysis/minimizers/bumps.py#L433)
- [bumps.py](../../../../src/easydiffraction/analysis/minimizers/bumps.py#L466)

**Depends on:** nothing.
