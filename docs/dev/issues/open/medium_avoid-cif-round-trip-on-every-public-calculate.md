# 175. Avoid the CIF Round-Trip on Every Public `calculate()`

**Priority:** `[priority] medium`

**Type:** Performance

The cryspy calculator has two paths
(`src/easydiffraction/analysis/calculators/cryspy.py`): the minimizer
fast path (`_recreate_cryspy_dict`, a cached-dict deep-copy plus
parameter update) and the public path
(`called_by_minimizer=False` -> `_recreate_cryspy_obj`), which rebuilds
the whole cryspy object from a serialized CIF string
(`str_to_globaln` + `get_dictionary`) on **every** call. Profiling a
single `project.analysis.calculate()` shows this round-trip dominating,
including cryspy's `get_dictionary` recomputing the X-ray atomic
form-factor table via slow Slater-orbital integrals (`calc_transs`),
which for neutron data is never used.

Interactive use (repeated `calculate()` / `display`) therefore pays the
full CIF parse + form-factor build each time, even when only a parameter
changed.

**Fix:** let the public `calculate()` reuse the cached cryspy dict and
in-place parameter update (the fast-path machinery) when the structural
topology is unchanged, rebuilding the object only when the model
topology actually changes (atoms added/removed, space group changed,
calculator switched). Optionally also memoize the form-factor table in
the cryspy dict so it is not recomputed when the object is rebuilt.

**TODOs / locations:**

- `_recreate_cryspy_obj` / `_recreate_cryspy_dict` /
  `calculate_pattern` invalidation logic in `calculators/cryspy.py`.
- Define and test the invalidation triggers (topology vs parameter
  change) so a stale object is never reused.
- Cross-reference the cryspy-side form-factor memoization noted in the
  upstream PR guide (`tmp/cryspy_pr/PR_GUIDE.md`).

**Depends on:** nothing in EasyDiffraction; the optional form-factor
memoization is an upstream cryspy change.

**Recommended-priority note:** Marked **medium** — the largest cost of a
single public `calculate()`; affects interactive/scripted use rather
than the already-optimized minimizer loop.
