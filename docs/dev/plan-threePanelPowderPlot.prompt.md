## Plan: Three-Panel Powder Plot

Extend `project.display.plotter.plot_meas_vs_calc()` so powder Bragg
plots render as three vertically stacked, X-synced Plotly subplots by
default: measured/calculated pattern, Bragg peak tick rows, and residual
curve. The plotter will consume a future experiment peak-position
category, but this change should not calculate or populate peak
positions itself.

**Status**

- [x] Step 1 confirmed. Peak-position data will come from a future
      experiment category and is out of scope for this implementation.
- [x] Step 2 completed. Added a display-specific Bragg tick DTO in
      `src/easydiffraction/display/plotters/base.py`.
- [x] Step 3 completed. Powder Bragg `plot_meas_vs_calc()` now routes
      through a composite plotting path, with residuals enabled by
      default only for the powder-Bragg composite branch.
- [x] Step 4 completed. Added a helper that consumes the future
      `experiment.bragg_peaks` arrays when present and otherwise logs a
      clear warning while rendering an empty Bragg row.
- [x] Step 5 completed. Added `plot_powder_meas_vs_calc(...)` to the
      plotting backend contract and routed powder Bragg plots to it.
- [x] Step 6 completed. Plotly now renders stacked subplots with shared
      x axes and configurable row-height fractions.
- [x] Step 7 completed. The residual row now uses a scale-aware,
      symmetric y range with exactly three ticks and no extra colored
      zero line.
- [x] Step 8 completed. The Bragg row renders one hover-capable tick
      trace per structure or phase row.
- [x] Step 9 completed. The composite Plotly figure explicitly matches x
      axes across the main, Bragg, and residual rows.
- [x] Step 10 completed. The ASCII backend now falls back to the
      measured/calculated/residual chart and announces the Plotly-only
      Bragg row.
- [x] Step 11 completed for the targeted tutorial source. Updated
      `docs/docs/tutorials/ed-2.py` to rely on the new default plot
      call.
- [x] Step 12 completed. Added focused facade/backend tests, regenerated
      `docs/docs/tutorials/ed-2.ipynb`, and ran the targeted Phase 2
      verification commands.
- [x] Follow-up review fixes completed. Empty filtered powder ranges no
      longer render stray Bragg rows, and Bragg grouping now preserves
      raw structure ids before converting labels for display.

**Atomic Change Log**

1. Added `BraggTickSet` in
   `src/easydiffraction/display/plotters/base.py` so future
   experiment-category peak arrays can be passed to plotting backends
   without coupling them to datablock internals.
2. Routed powder Bragg `plot_meas_vs_calc()` through a dedicated
   composite backend method, added Plotly three-row subplot rendering,
   and added an ASCII fallback while tolerating the still-missing
   `experiment.bragg_peaks` category.
3. Updated `docs/docs/tutorials/ed-2.py` so the tutorial now uses the
   default three-panel powder plot without explicitly passing
   `show_residual=True`.
4. Added focused display tests for composite powder routing, Bragg tick
   extraction, Plotly subplot rendering, and the ASCII fallback, then
   regenerated `docs/docs/tutorials/ed-2.ipynb`.
5. Refined the residual subplot axis so its physical y scale follows the
   main chart, its ticks are symmetric about zero, and the extra green
   zero line is removed.
6. Locked the composite plot x axis to the actual data minimum and
   maximum so Plotly no longer adds autorange padding around the scan.
7. Refactored the composite plot so the Bragg subplot is created only
   when tick data exists; otherwise the figure collapses to the main and
   residual rows without a no-data warning.
8. Refactored the composite powder plotting path around a typed spec
   object so the backend contract, facade routing, and Bragg DTO stay
   within the repository's lint-complexity limits while preserving the
   same three-panel behavior.
9. Removed residual-axis rounding after the physical scale match so the
   residual panel now preserves the intended pixel-per-unit alignment
   for positive-background datasets such as the HRPT tutorial case.
10. Kept the exact residual range for scale matching but moved the
    visible residual y-axis ticks to cleaner symmetric display values so
    the subplot no longer shows awkward endpoint labels such as
    `78.8649` or `439.109`.
11. Stopped expanding the residual y-axis to fit outlier spikes when the
    main plot has a real y range, so oversized residuals are now clipped
    within the scale-matched subplot instead of breaking the intended
    physical alignment.
12. Addressed review regressions by normalizing Bragg filtering bounds
    before masking future `bragg_peaks` data, keeping the residual
    default scoped to the powder-Bragg composite path, and guarding the
    composite Plotly backend against empty filtered x ranges.
13. Fixed follow-up review gaps by suppressing Bragg ticks when the
    filtered main pattern is empty and by grouping Bragg rows on raw
    structure ids so numeric identifiers still produce populated tick
    rows with string labels.

**Steps**

1. Confirm the future peak-position category contract before
   implementation. It should be a powder experiment category similar to
   `data`, exposing array-like peak data in the experiment's active x
   coordinate: structure/phase id, x position, Miller indices h/k/l, and
   peak intensity. Optional peak id can be included for hover text. This
   is a prerequisite for real Bragg tick content, but can land as a
   separate change.
2. Add a small plotting data transfer object for Bragg tick sets in
   `src/easydiffraction/display/plotters/base.py`, for example a frozen
   dataclass containing `structure_id`, `x`, `h`, `k`, `l`, and
   `intensity`. Keep it display-specific so the plotting backend does
   not depend on experiment category internals.
3. Extend `Plotter.plot_meas_vs_calc()` in
   `src/easydiffraction/display/plotting.py` so powder Bragg plots
   include residuals by default. Recommended API: make residual display
   the default without requiring `show_residual=True`; keep or repurpose
   `show_residual` only after confirming whether public removal is
   acceptable. Single-crystal behavior remains unchanged.
4. Add helper logic in `src/easydiffraction/display/plotting.py` to
   extract Bragg tick sets from the future category when present. The
   helper should group peaks by structure/phase id, filter x positions
   to the displayed `x_min`/`x_max`, and build hover fields. If the
   category is absent or empty, log a clear warning and render the Bragg
   axis rectangle empty rather than silently failing.
5. Route powder Bragg `plot_meas_vs_calc()` calls to a new backend
   method dedicated to this composite plot, such as
   `plot_powder_meas_vs_calc(...)`, instead of overloading the generic
   `plot_powder()` used by `plot_meas()` and `plot_calc()`. The method
   should receive x, measured y, calculated y, residual y, axes labels,
   Bragg tick sets, residual height fraction, Bragg height fraction,
   title, and height.
6. Implement the new backend method in
   `src/easydiffraction/display/plotters/plotly.py` using Plotly
   subplots with `shared_xaxes=True` plus explicit `matches='x'` on all
   x axes. Row heights should be normalized from main = 1, Bragg =
   configurable value, residual = `residual_height_fraction` with
   default 0.25, so the residual row is 25% of the main row height.
7. In the Plotly main row, render measured and calculated traces using
   the existing `SERIES_CONFIG` colors and names. In the residual row,
   render `Imeas - Icalc` in the same intensity units with a symmetric,
   scale-aware y range derived from the main chart height ratio. Show
   exactly three residual-axis ticks (`min`, `0`, `max`) and do not add
   a separate colored zero line.
8. In the Bragg row, render one trace per structure/phase. Each peak
   should appear as a vertical tick at its x position and at a
   per-structure y row. Use a hover-capable trace representation, not
   layout shapes, so hovering shows structure/phase, peak id if
   available, hkl, x position, and intensity. Keep numeric y-axis labels
   hidden or replace them with structure labels if that remains
   readable. When no Bragg tick data exists, omit the Bragg subplot
   entirely.
9. Make X synchronization explicit: zooming or panning the main pattern
   must update the Bragg tick row and residual row, and the shared
   x-axis range should start at the filtered data minimum and end at the
   filtered data maximum instead of using Plotly autorange padding. Y
   axes should remain independent: the main y-axis reflects intensity,
   the Bragg y-axis is arbitrary row placement, and the residual y-axis
   auto-ranges in intensity-difference units.
10. Implement an ASCII backend fallback in
    `src/easydiffraction/display/plotters/ascii.py` for the new method.
    It can render measured/calculated/residual using the existing single
    ASCII chart behavior and print a clear note that Bragg tick subplots
    are only available in graphical Plotly output.
11. Update docs and examples after the implementation shape is approved.
    Edit `docs/docs/tutorials/ed-2.py`, not the generated notebook,
    replacing calls that currently pass `show_residual=True` with the
    new default call. Run `pixi run notebook-prepare` in verification to
    regenerate notebooks.
12. Follow the repository's two-phase workflow. Phase 1: implement code
    and docs only; do not add tests or run tests. Phase 2 after
    approval: add/update focused tests and run verification commands.

**Relevant files**

- `src/easydiffraction/display/plotting.py` — public
  `Plotter.plot_meas_vs_calc()`, `_plot_meas_vs_calc_data()`, and new
  helper for consuming future peak-position category data.
- `src/easydiffraction/display/plotters/base.py` — `PlotterBase`, shared
  plotting DTO/constants, and backend method contract.
- `src/easydiffraction/display/plotters/plotly.py` — Plotly
  implementation with three synced subplot rows, hoverable Bragg ticks,
  residual row sizing, and x-axis matching.
- `src/easydiffraction/display/plotters/ascii.py` — fallback
  implementation for the new composite plot method.
- `src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py`
  — reference pattern for array-like powder data category behavior; not
  modified unless the peak-position category lands in the same
  implementation cycle.
- `src/easydiffraction/datablocks/experiment/item/base.py` and
  `src/easydiffraction/datablocks/experiment/item/bragg_pd.py` — future
  category wiring reference if the peak-position category is implemented
  in this change.
- `docs/docs/tutorials/ed-2.py` — tutorial source to update;
  `docs/docs/tutorials/ed-2.ipynb` is generated by
  `pixi run notebook-prepare`.
- `tests/unit/easydiffraction/display/test_plotting.py` and
  `tests/unit/easydiffraction/display/test_plotting_coverage.py` —
  facade tests to update with fake peak-position category data.
- `tests/unit/easydiffraction/display/plotters/test_plotly.py` — Plotly
  backend tests for row heights, x-axis matching, hover data, and trace
  routing.
- `tests/integration/fitting/test_plotting.py` — integration test once a
  real peak-position category exists on fitted projects.

**Verification**

1. Unit-test the facade with a fake powder Bragg experiment exposing a
   fake peak-position category. Verify residual is included by default,
   Bragg peaks are grouped by structure id, x filtering is applied to
   all three plot rows, and single-crystal routing is unchanged.
2. Unit-test the Plotly backend by monkeypatching Plotly figure/subplot
   creation or inspecting a real figure object before display. Verify
   three rows, matched x axes, residual row height fraction 0.25
   relative to main, hover templates include hkl and intensity, and one
   Bragg tick trace exists per structure.
3. Unit-test the ASCII fallback to ensure calls do not fail and the user
   gets a clear note about graphical-only Bragg tick rows.
4. After the future peak-position category exists, add category/unit
   round-trip tests for peak x positions, h/k/l, intensity, and
   structure id, plus an integration plotting test using
   `lbco_fitted_project`.
5. Phase 2 commands:
   `pixi run unit-tests tests/unit/easydiffraction/display/`,
   `pixi run integration-tests tests/integration/fitting/test_plotting.py`,
   `pixi run notebook-prepare`, and then the project-prescribed
   `pixi run fix`, `pixi run check`, `pixi run unit-tests`,
   `pixi run integration-tests`, `pixi run script-tests` when the full
   verification pass is requested.

**Decisions**

- The Bragg tick data source is a future experiment category, not an ad
  hoc calculation inside the plotter.
- `plot_meas_vs_calc()` should show the three-panel powder Bragg layout
  by default; tutorial calls should no longer need `show_residual=True`.
- Residual y-axis uses the same intensity units but auto-ranges
  independently from the main y-axis.
- X axes are synchronized across all three rows; y axes are
  intentionally independent.
- Bragg tick y positions are arbitrary row offsets used only to separate
  structures/phases.
- Tick hover text must show peak identity/hkl and intensity.

**Further Considerations**

1. Public API cleanup: decide during implementation approval whether to
   remove `show_residual`, change its default to true, or keep it as a
   compatibility option. Removing it is a public API change and should
   be explicit.
2. Peak-position category naming: recommended names are `bragg_peaks`
   for the category and `structure_id` or `phase_id` for grouping. This
   should be finalized when that category is implemented.
3. Coordinate contract: the category should expose peak x positions in
   the same coordinate as `experiment.data.x`; if multiple x axes are
   later supported, it should expose enough metadata or arrays to match
   `x='two_theta'`, `x='time_of_flight'`, or `x='d_spacing'`
   unambiguously.
