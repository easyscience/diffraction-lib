# Powder Chart Y-Range Fix Plan

**Date:** 2026-05-06 **Status:** Phase 2 verified — complete

---

## 1. Goal

Fix the Plotly composite powder measured-vs-calculated chart so the main
intensity row is not anchored to zero. The y-axis range should be
derived from all displayed main-row intensity series: measured
(`Imeas`), calculated (`Icalc`), and background (`Ibkg`) when present.

The intended display range is:

```text
lower = min(Imeas, Icalc, Ibkg) - margin
upper = max(Imeas, Icalc, Ibkg) + margin
```

where `margin` is controlled by a dedicated constant of about 5% of the
main intensity span. The lower bound must use `min - margin`, not
`min + margin`, so the lowest displayed point remains visible with
padding below it.

---

## 2. Current Findings

- The affected code is `PlotlyPlotter._get_main_intensity_range()` in
  `src/easydiffraction/display/plotters/plotly.py`.
- It currently uses only `y_meas` and `y_calc`, then forces
  `lower_limit = min(0.0, main_y_min)`. That explains positive powder
  charts being truncated to a `0..max` range.
- `PowderMeasVsCalcSpec` already carries optional `y_bkg`, and
  `Plotter._plot_meas_vs_calc_data()` already filters
  `pattern.intensity_bkg` into the spec for powder Bragg plots.
- Existing Plotly unit tests assert the current `0.0..max` y-range in
  the residual scale-match tests, so those expectations must change.
- Repository memory notes confirm the background line is part of the
  composite powder plot and should be considered display data.

---

## 3. Scope

### In Scope

- Add a module-level constant in
  `src/easydiffraction/display/plotters/plotly.py`, likely
  `MAIN_INTENSITY_RANGE_MARGIN_FRACTION = 0.05`.
- Update `_get_main_intensity_range()` to compute min/max over `y_meas`,
  `y_calc`, and non-empty `y_bkg` when present.
- Apply symmetric visual padding outside the data range using the new
  constant.
- Preserve the existing empty-filtered-range behavior: empty required
  series should still return a harmless fallback range.
- Preserve residual scale matching by letting `_get_residual_limit()`
  use the newly padded main range and the existing
  `residual_height_fraction`, so the residual row remains adjusted to
  the main row size as it is now.
- Add/update focused unit tests for range calculation and affected
  residual-scale expectations.

### Out of Scope

- No public plotting API changes.
- No user-configurable y-axis margin in this step.
- No changes to ASCII plotting unless a later review shows the same main
  view problem exists there.
- No refactor of plot layout, Bragg tick sizing, hover templates, or
  facade routing.

---

## 4. Decisions

- Use `min(Imeas, Icalc, Ibkg) - margin` for the lower y-axis bound and
  `max(Imeas, Icalc, Ibkg) + margin` for the upper y-axis bound.
- Keep the residual plot scaled to the main intensity row, preserving
  the current matched-scale behavior after the main range gains padding.

---

## 5. Implementation Checklist

- [ ] Create branch `feature/powder-chart-y-range` if requested.
- [x] In `src/easydiffraction/display/plotters/plotly.py`, add the
      dedicated 5% y-range margin constant near the other Plotly layout
      constants.
- [x] Update `_get_main_intensity_range()` so it includes background
      intensity when available and uses the padded min/max range instead
      of anchoring positive data to zero.
- [x] Keep zero-span data explicit and stable, using a small fallback
      range around the datum because a percentage margin is undefined.
- [x] Confirm `_get_residual_limit()` continues to scale the residual
      row from the updated main y-range and existing residual height
      fraction.
- [x] Stop after Phase 1 and request review before adding or running
      tests, following the repo workflow.

---

## 6. Phase 2 Verification Checklist

- [x] Add or update tests in
      `tests/unit/easydiffraction/display/plotters/test_plotly.py` for:
  - positive-only `Imeas`/`Icalc` data no longer starting at zero;
  - `Ibkg` lowering or raising the main y-range when present;
  - 5% padding on both ends of the main row;
  - residual scale-match expectations after padding changes the main row
    span;
  - empty filtered arrays retaining the existing fallback behavior.
- [x] Keep the existing facade propagation test in
      `tests/unit/easydiffraction/display/test_plotting.py` unless the
      implementation reveals a missing background handoff case.
- [x] Run `pixi run fix`.
- [x] Run `pixi run check` until clean.
- [x] Run `pixi run unit-tests`.
- [x] Run `pixi run integration-tests`.
- [x] Run `pixi run script-tests`.

---

## 7. Likely Files

- `src/easydiffraction/display/plotters/plotly.py`
- `tests/unit/easydiffraction/display/plotters/test_plotly.py`
- `tests/unit/easydiffraction/display/test_plotting.py` only if a
  facade-level test gap is discovered during verification.

---

## 8. Suggested Commit Message

```text
Fix powder chart y-axis range
```
