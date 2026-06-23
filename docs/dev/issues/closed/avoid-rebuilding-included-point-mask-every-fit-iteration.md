# 173. Avoid Rebuilding the Included-Point Mask Every Fit Iteration

Closed by skipping the redundant excluded-region re-apply during
refinement and caching the included-point mask/list.

After the Wyckoff orbit-template cache (issue 172), profiling showed the
remaining minimizer-iteration cost was EasyDiffraction's per-point data
plumbing: `excluded_regions._update` rebuilt the full excluded mask
every iteration — an `unfiltered_x` build plus an all-point
`_set_calc_status` write — and `_calc_mask` / `_calc_items` then rebuilt
the full `calc_status` array on every access. The included/excluded
split depends only on the x-grid and the region bounds, both fixed
during a fit.

Two coordinated changes:

- `excluded_regions._update` now skips the re-apply on minimizer
  iterations when its signature `(point count, region bounds)` is
  unchanged. A non-minimizer update (public `calculate`, data reload, or
  a region edit) always re-applies, so changes are never missed.
- `PdDataBase._calc_mask` / `_calc_items` are cached, invalidated by
  `_set_calc_status` (calc-status change) and by point-set creation.
  With the per-iteration re-apply gone, the cache stays valid across a
  fit, so the filtered-array properties (`x`, `d_spacing`,
  `intensity_meas`, …) no longer rebuild the full `calc_status` array
  each iteration.

Validated: the minimizer-path calculation is bit-identical to a fresh
public `calculate()` at the same parameters with excluded regions
present (max |Icalc| difference 0.0, identical `calc_status`, 793/793
included points). The minimizer iteration dropped a further ~1.9×
(cProfile total for the NCAF case 2.61 s → 1.37 s over 20 iterations),
~3.5× cumulative with issue 172. Regression tests in
`tests/unit/easydiffraction/datablocks/experiment/categories/test_excluded_regions.py`
cover skip-when-unchanged, always-reapply on non-minimizer updates, and
re-apply when a region bound or the grid changes. The full unit-test
slice (experiment + analysis) and the FullProf verification suite
(including the excluded-region cases NCAF and LaB6) pass unchanged.

Follows the same "cache what is invariant during a fit" pattern as
issue 172.
