# 176. Reuse Reflection Record Objects Across Fit Iterations

**Priority:** `[priority] low`

**Type:** Performance

The post-cache minimizer profile shows per-reflection record object
construction each iteration (`refln/bragg_pd.py:__init__`,
`refln/bragg_sc.py:__init__`), rebuilding the reflection table from
scratch every step. While the unit cell is fixed, the reflection list
(hkl, multiplicity, d-spacing) does not change; only the intensities do.

**Fix:** reuse the reflection record objects across iterations when the
hkl set is unchanged, updating only the per-reflection calculated
quantities, instead of constructing new record objects each step.

**TODOs / locations:**

- `experiment.refln` replacement path
  (`_replace_from_records`) and the record `__init__`s in
  `src/easydiffraction/datablocks/experiment/categories/refln/`.
- Invalidate the reused table when the unit cell or space group changes.
- Add a test that the reused-table path matches a fresh rebuild.

**Depends on:** nothing external.

**Recommended-priority note:** Marked **low** — a modest per-iteration
saving, smaller than issues 172-174.
