# 15. Validate Joint-Fit Weights Before Residual Normalisation

**Priority:** `[priority] highest`

**Type:** Correctness

Joint-fit weights currently allow invalid numeric values such as
negatives or an all-zero set. The residual code then normalises by the
total weight and applies `sqrt(weight)`, which can produce
division-by-zero or `nan` residuals.

**Fix:** require weights to be strictly positive, or at minimum validate
that all weights are non-negative and their total is greater than zero
before normalisation. This should fail with a clear user-facing error
instead of letting invalid floating-point values propagate into the
minimiser.

**Depends on:** related to issue 3, but independent.

**Recommended-priority note:** Joint-fit weight safety (paired with #3): validate weights before residual normalisation so invalid/all-zero sets cannot reach the minimiser as `nan`/division-by-zero. **Tier 1 (do first).**
