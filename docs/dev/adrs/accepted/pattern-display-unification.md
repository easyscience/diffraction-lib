# ADR: Unified Pattern View

## Status

Accepted and implemented.

## Date

2026-06-04

## Context

`project.display.pattern()` was originally specified by the
[Display UX Facade](display-ux.md) ADR with an `include=` argument that
assembled a view from named layers (`measured`, `calculated`,
`background`, `residual`, `bragg`, `excluded`, `uncertainty`), plus a
`show_pattern_options()` discovery table. `include='auto'` already chose
the most informative combination from project state.

In practice this surfaced several problems:

- The single-panel path (`plot_meas`/`plot_calc` → `plot_powder`) and
  the composite path (`build_powder_meas_vs_calc_figure`) computed
  figure height and x-range independently, so they drifted. A
  measured-only view rendered at the full three-panel height in the lazy
  docs runtime — the
  [Plotting & Docs Performance](plotting-docs-performance.md) skeleton
  fell back to `DEFAULT_HEIGHT * PLOTLY_HEIGHT_PER_UNIT` — and gained
  stray left/right autoscale padding the composite did not have.
- `'excluded'` was an opt-in overlay, but excluded regions are a
  property of the experiment, not a viewing choice; `include='measured'`
  and `include=('measured', 'excluded')` produced different plots of the
  same data, which read as redundant.
- For a scientist audience, choosing layers is friction. The project
  state already determines what is meaningful to show, which is exactly
  what `include='auto'` computed.

## Decision

`pattern(expt_name, x_min=None, x_max=None, *, x=None)` always renders
every kind of data the project state supports — the former
`include='auto'` behaviour is now the only behaviour. The `include`
parameter, the `show_pattern_options()` method, and the option-status
discovery table are removed. Strict-subset views (for example
measured-only once a calculation exists) are intentionally no longer
offered; zooming (`x_min`/`x_max`) and the x-axis variable (`x`) remain.

Excluded regions are always shaded when defined on the experiment,
skipped only when a custom `x` axis variable is selected, because the
overlay cannot be mapped onto an arbitrary axis.

Single-panel and composite charts share one figure-sizing and x-range
core. `plot_powder` builds its layout with the same
`_single_main_panel_height_pixels(...)` height and tight
`_composite_x_range(...)` as the composite main row, and `_get_layout`
already applies the composite margins. A one-row chart is therefore the
top row of the multi-row chart pixel for pixel, by construction, so the
two paths cannot diverge again.

This supersedes the `include`-based pattern design in the
[Display UX Facade](display-ux.md) ADR. The remainder of that ADR — the
facade grouping, renderer categories, and naming rules — still stands.

## Consequences

- `pattern(expt_name=...)` is the whole pattern API surface; tutorials,
  docs, and tests no longer pass `include=`.
- The project is in beta, so this replaces the previous API with no
  compatibility shim; tutorials and tests are updated to the current
  API.
- Sizing and range differences between one- and three-panel views are
  prevented structurally, not patched per call.
- `structure(include=...)` and `show_structure_options()` are
  unaffected: choosing which 3D features to draw remains a genuine
  viewing choice (see
  [Crystal Structure 3D Visualization](crysview-structure-visualization.md)).

## Alternatives Considered

Keeping `include` as the view-selection vocabulary (the original
design). `include` had been chosen over `layers`, `components`,
`content`, `view`, `series`, and boolean flags because it read as user
intent and fit residual rows and Bragg ticks. It is removed now because
the only combination users reached for in practice was the automatic
"show everything available" view; the subset combinations added API
surface and a discovery table without a matching workflow, and the
parallel single-panel rendering path was the source of the sizing and
range divergence.

Keeping `'excluded'` as an opt-in overlay, or as a redundant no-op
token, was rejected: excluded regions belong to the experiment, so
shading them is automatic whenever they are present.
