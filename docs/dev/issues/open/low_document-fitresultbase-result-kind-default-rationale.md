# 106. Document `FitResultBase.result_kind` Default Rationale

**Priority:** `[priority] low`

**Type:** Code readability **Source:** `minimizer-input-output-split`
review 6.

Most `FitResultBase` descriptors use `default=None, allow_none=True` so
pre-fit CIF output serializes unknown values as `?`. `result_kind`
intentionally keeps a valid enum default because it drives deterministic
versus Bayesian projection handling, but that exception is not
documented in code.

**TODOs:**

- [base.py](../../../../src/easydiffraction/analysis/categories/fit_result/base.py#L44)

**Fix:** add a short code comment near the `result_kind` descriptor
explaining why it keeps a concrete default while unknown result values
use `None`.

**Depends on:** nothing.
