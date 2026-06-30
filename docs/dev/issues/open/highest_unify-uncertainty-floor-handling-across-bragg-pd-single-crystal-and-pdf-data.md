# 140. Unify Uncertainty-Floor Handling Across Bragg PD, Single-Crystal, and PDF Data

**Priority:** `[priority] highest`

**Type:** Correctness / Robustness

The minimizer residual divides by the measured-uncertainty array, so a
zero/NaN/negative uncertainty produces `inf`/`NaN` residuals fed
silently to the minimiser. The floor is applied inconsistently:

- Bragg powder replaces near-zero uncertainties with `1.0`, but its
  guard is `original < _MIN_UNCERTAINTY`, which does **not** catch `NaN`
  (NaN comparisons are False) or negative values.
- Single-crystal `intensity_meas_su` has **no** guard at all.
- Total-scattering (PDF) `g_r_meas_su` has **no** guard, and the PDF
  ASCII loader never applies the `< _MIN_UNCERTAINTY → 1.0` substitution
  that the Bragg loader does.
- `_MIN_UNCERTAINTY = 0.0001` is duplicated in two modules, and the PDF
  ASCII default `0.03` is a third independent literal.

**Fix:** centralize a single finite-positive uncertainty-floor policy on
the descriptor (per the existing TODO) and apply it uniformly to all
three data families and all loaders; reject/clamp non-finite and
non-positive values at the boundary.

**TODOs / locations:**

- [bragg_pd.py](../../../../src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L648)
- [bragg_pd.py](../../../../src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L673)
- [total_pd.py](../../../../src/easydiffraction/datablocks/experiment/categories/data/total_pd.py#L324)
- [bragg_sc.py](../../../../src/easydiffraction/datablocks/experiment/categories/refln/bragg_sc.py#L466)
- [fitting.py](../../../../src/easydiffraction/analysis/fitting.py#L449)

**Depends on:** supersedes the narrower issue 27 (Bragg PD zero
uncertainty). Related to issue 15 (joint-fit weights).

**Recommended-priority note:** Promoted to **highest** by the 2026-06-13
audit: inconsistent uncertainty-floor handling yields silent NaN/inf
residuals — the same residual-safety class as the Tier 1 joint-fit
weight issues (#3 / #15).

**Audit note (2026-06-23):** within Bragg PD the near-zero clamp itself
is duplicated — the CIF-read `intensity_meas_su` property and the ASCII
loader (`bragg_pd.py:163`) each apply their own
`np.where(su < _MIN_UNCERTAINTY, 1.0, …)`. Centralising the floor on
`NumericDescriptor` (the planned fix) removes this duplication too, so
CIF and ASCII inputs cannot diverge.
