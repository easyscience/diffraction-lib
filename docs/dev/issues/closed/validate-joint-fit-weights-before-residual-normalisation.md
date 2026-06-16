# 15. Validate Joint-Fit Weights Before Residual Normalisation

**Type:** Correctness

**Status:** Closed.

Joint-fit weights previously allowed invalid numeric values such as
negatives or an all-zero set. The residual code normalises by the total
weight and applies `sqrt(weight)`, so such inputs could produce
division-by-zero or `nan` residuals that propagated silently into the
minimiser.

**Resolution:** `Fitter.fit` now validates joint-fit weights up front,
before the objective function runs, via a new
`Fitter._require_valid_weights` guard (mirroring the existing
`_require_measured_data` idiom). When weights are supplied it rejects,
with a clear user-facing `ValueError`:

- a non-1-D array or a length that does not match the experiments;
- any non-finite (`nan`/`inf`) element;
- any negative element;
- a total that is not finite and strictly positive — catching both the
  all-zero set and finite inputs whose sum overflows to `inf`.

Equal-weight fits (`weights is None`) skip the check.

The rule is non-negative weights with a finite positive total rather
than strictly-positive-per-element, so a single `0` weight stays valid
(that experiment contributes zero residuals). Defining the full
supported range and validator semantics for `joint_fit.weight` —
including whether `0` formally means exclusion and whether an upper
bound exists — remains with issue 122 (`Define joint_fit.weight
Bounds`); this fix deliberately leaves the descriptor-level
`RangeValidator()` untouched.

**Related:** issue 3 (rebuild joint-fit weights on every fit), issue 122
(define `joint_fit.weight` bounds).
