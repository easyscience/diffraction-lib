# 177. Reduce Per-Point Data-Model Overhead in Fits

**Priority:** `[priority] low`

**Type:** Performance

Powder data is stored as a collection of per-point Python objects, each
holding guarded descriptors. The hot-path array properties (`x`,
`d_spacing`, `intensity_meas`, ...) rebuild numpy arrays from those
objects with `np.fromiter` over per-descriptor `.value` access on every
call, and the post-cache minimizer profile is dominated by
`core/variable.py:value` and `core/guard.py:__setattr__` (hundreds of
thousands of calls per iteration).

The fit-invariant inputs are already cheaper after issue 173, but the
per-point object round-trip itself remains the structural cost.

**Fix:** hold the invariant per-point inputs as backing numpy arrays (x,
measured intensity, sigma, d-spacing) and expose the per-point objects
as views, so array extraction is O(1) instead of an object-by-object
rebuild. This is a larger data-model change; capture it here as the
umbrella for the remaining per-point overhead.

**TODOs / locations:**

- `PdDataBase` array properties and per-point classes in
  `src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py`.
- Preserve CIF round-trip, restore, and the public per-point API.
- Benchmark against the current model before/after.

**Depends on:** related to issues 173 and 174; this is the broader
data-model refactor behind them.

**Recommended-priority note:** Marked **low** — biggest conceptual
change with diminishing returns after issues 172-174; worth doing only
if fit throughput remains a bottleneck.
