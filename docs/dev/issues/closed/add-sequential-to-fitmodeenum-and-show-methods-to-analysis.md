# 78. Add `SEQUENTIAL` to `FitModeEnum` and Show Methods to Analysis

Added `SEQUENTIAL = 'sequential'` to `FitModeEnum`. `fit_sequential()`
now sets `fit_mode.mode = 'sequential'` internally so the mode is
persisted in CIF. Added `show_fit_mode_types()` (filters by experiment
count: ≤1 → only `single`; >1 → all three) and `show_fit_mode_types()`
on `Analysis`. If `fit()` is called while mode is `'sequential'`, it
logs an error directing the user to `fit_sequential()`. Promoted
`fit_mode` from a pure single-type category to one with show methods.

---

## Persist Per-Experiment Calculator Selection

Calculator selection now lives in the experiment-side `calculation`
category and is persisted in experiment CIF via
`_calculation.calculator_type`. Loading restores the explicit backend
selection before dependent experiment categories are populated, so saved
projects keep the exact active calculator configuration instead of
falling back to auto-resolution.
