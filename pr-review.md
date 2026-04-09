# PR Review: `param-correlations` → `develop`

## Summary

54 files changed, +1494/−118 lines. Adds correlation matrix plotting
(heatmap via Plotly, ASCII table via asciichartpy), data extraction from
fit results, triangle masking, threshold filtering, and comprehensive
tests.

---

## Issues

### Issue #1 (Medium) — `triangle` parameter uses raw strings instead of Enum

**Rule**: §9.6 — every finite, closed set of values must use a
`(str, Enum)`.

`plot_param_correlations(triangle='lower')` accepts raw strings
`'lower'`, `'upper'`, `'full'` and compares them with `==` inside
`_mask_correlation_triangle` and `_trim_correlation_display_dataframe`.

**Status**: ✅ FIXED — `CorrelationTriangleEnum` was created. **Updated
status**: User decided to remove `show_diagonal` and `triangle`
parameters entirely, keeping only the default behavior (lower triangle,
no diagonal). This eliminates the need for the enum altogether.

---

### Issue #2 (Low-Medium) — `plot_correlation_heatmap` not declared on `PlotterBase`; facade uses `isinstance` dispatch

**Rule**: §9.4 — backends should share a common interface via the base
class.

`plotting.py` used `isinstance(self._backend, PlotlyPlotter)` to decide
whether to call `plot_correlation_heatmap`. This couples the facade to a
concrete backend.

**Fix**:

- Add `_supports_graphical_heatmap: bool = False` on `PlotterBase`,
  override to `True` on `PlotlyPlotter`.
- Add a concrete no-op `plot_correlation_heatmap()` on `PlotterBase`.
- Replace `isinstance` check with
  `self._backend._supports_graphical_heatmap`.

**Status**: ✅ FIXED — `_supports_graphical_heatmap` flag added, `isinstance`
replaced, no-op method on `PlotterBase` uses `del` pattern to consume
unused args (matching `PlotlyPlotter` convention).

---

### Issue #3 (Low) — Missing `from __future__ import annotations`

**Rule**: Code style — use `from __future__ import annotations` in every
module.

Pre-existing in several files. Not in scope for this PR.

**Status**: ⏭️ SKIPPED (pre-existing, out of scope)

---

### Issue #4 (Medium) — `_plot_param_series_from_snapshots` is dead copy-paste

Pre-existing dead code that duplicates `_plot_param_series_from_csv`.

**Status**: ⏭️ SKIPPED (pre-existing, out of scope)

---

### Issue #5 (Informational) — Coverage threshold lowered 75 → 70

Aligns with architecture.md §10 which states 70%.

**Status**: ✅ OK

---

### Issue #6 (Informational) — `_get_layout` uses `**kwargs`

Pre-existing pattern. Not in scope for this PR.

**Status**: ⏭️ SKIPPED (pre-existing, out of scope)

---

## Completed Actions

1. ✅ Remove `CorrelationTriangleEnum` from `plotting.py`
2. ✅ Remove `show_diagonal` and `triangle` params from
   `plot_param_correlations`
3. ✅ Simplify `_mask_correlation_triangle` → hardcode lower triangle, no
   diagonal
4. ✅ Simplify `_trim_correlation_display_dataframe` → hardcode lower
   triangle trim
5. ✅ Fix `PlotterBase.plot_correlation_heatmap` lint errors (PLR6301,
   ARG002)
6. ✅ Remove tests for diagonal/full/triangle validation
7. ✅ Update remaining tests
8. ✅ `pixi run fix` + `pixi run check` + `pixi run unit-tests` (683
   passed)
9. ✅ `pixi run integration-tests` (98 passed) +
   `pixi run script-tests` (18 passed)
