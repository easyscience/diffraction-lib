# Plan: Pattern Display Unification

Follows [`AGENTS.md`](../../../AGENTS.md). No deliberate exceptions.

## ADR

Recorded as the
[`pattern-display-unification`](../adrs/accepted/pattern-display-unification.md)
ADR (Accepted), which supersedes the `include`-based pattern design in
[`display-ux.md`](../adrs/accepted/display-ux.md). Relates to
[`plotting-docs-performance.md`](../adrs/accepted/plotting-docs-performance.md)
(the lazy figure skeleton that exposed the height bug) and open issue
#93 (future of `show_residual`).

## Branch / PR

Feature slug `pattern-display-unification`. PR targets `develop`.
**Open:** confirm whether to branch off the current
`tutorial-project-outputs` working branch or start a fresh
`pattern-display-unification` branch before committing.

## Background

Four user-reported issues, all rooted in the split between the
single-panel path (`plot_meas`/`plot_calc` → `plot_powder`) and the
composite path (`build_powder_meas_vs_calc_figure`):

1. **HTML height** — the single-panel Plotly figure sets no explicit
   height, so the docs' lazy skeleton falls back to
   `DEFAULT_HEIGHT * PLOTLY_HEIGHT_PER_UNIT = 600px` (the full 3-panel
   height) instead of the ~458px main panel.
2. **X-axis offsets** — the single-panel path sets no x-range, so Plotly
   auto-pads; the composite pins `(min, max)`.
3. **`include=('measured','excluded')` redundancy** — excluded regions
   are a property of the experiment, not a viewing choice.
4. **Structure top margin** — the 3D scene sits flush under its header
   line.

## Decisions

- **Drop `include` entirely.**
  `pattern(expt_name, x_min=None, x_max=None, *, x=None)` always renders
  all available content (the former `include='auto'` behaviour, which is
  already proven). The cost — losing strict-subset views such as
  measured-only once a calc exists — is accepted; `x_min`/`x_max` and
  `x` still work. Can be re-added later only on a concrete need.
- **Excluded regions always shade** when defined on the experiment, in
  every view; skipped only when a custom `x` axis is selected (the
  overlay can't be mapped). The `'excluded'` token is removed.
- **Common rendering base via shared primitives.** The single-panel
  `plot_powder` derives its figure height from
  `_single_main_panel_height_pixels(...)` and its x-range from
  `_composite_x_range(...)` — the same helpers the composite uses.
  Because `_get_layout` already uses the composite margins
  (`r:30, t:40, b:45`), a 1-panel view becomes the composite's main row
  pixel-for-pixel. No builder merge (the composite hard-requires
  `y_calc`); the shared helpers are the single source of truth.
- **Keep the internal availability engine** (`_pattern_option_statuses`,
  `_auto_include`, `PatternOptionStatus`); only the user-facing
  selection/validation/discovery layer is removed.
- The residual-fraction default moves to `plotters/base.py` so both the
  facade (`plotting.py`) and backend (`plotly.py`) can import it without
  a circular dependency.

## Open questions

- Branch choice (above).
- Should `pattern()` keep accepting a custom `x` axis variable? Assumed
  **yes** (separate from `include`).

## Concrete files likely to change

- `src/easydiffraction/display/plotters/base.py` — add
  `DEFAULT_RESIDUAL_HEIGHT_FRACTION`.
- `src/easydiffraction/display/plotters/plotly.py` — `plot_powder`
  explicit height + tight x-range.
- `src/easydiffraction/display/plotting.py` — import the moved constant.
- `src/easydiffraction/project/display.py` — rewrite `pattern()`; remove
  `include`, `_normalize_include`, `_validate_requested_include`,
  `show_pattern_options`; simplify `_show_point_estimate_pattern`.
- `src/easydiffraction/display/structure/templates/structure.html.j2` —
  scene top margin (done).
- `docs/dev/adrs/accepted/display-ux.md` — amend Pattern Display.
- `docs/dev/adrs/accepted/crysview-structure-visualization.md`,
  `docs/docs/quick-reference/index.md` — drop stale
  `show_pattern_options` references.
- `docs/docs/tutorials/ed-3.py`, `ed-9.py`, `ed-11.py`, `ed-13.py` (+
  regenerated `.ipynb`) — remove `include=`.
- Phase 2: `tests/unit/easydiffraction/project/test_display.py`,
  `tests/integration/fitting/test_plotting.py`.

## Implementation steps (Phase 1)

- [x] **P1.1 — Unify single-panel sizing/x-range.** Move
      `DEFAULT_RESIDUAL_HEIGHT_FRACTION` to `base.py`; `plot_powder`
      sets explicit main-panel height and tight `(min,max)` x-range.
      Fixes issues #1 and #2. Commit:
      `Match single-panel pattern height and x-range to composite`
- [x] **P1.2 — Drop `include`; always render available content.**
      Rewrite `pattern()`; remove the selection/validation/discovery
      layer; always-shade excluded. Fixes issue #3. Commit:
      `Always render available pattern content; drop include`
- [x] **P1.3 — Structure scene top margin.** Fixes issue #4. Commit:
      `Add top margin above structure scene rectangle`
- [x] **P1.4 — Amend ADR and docs.** Update `display-ux.md`; drop stale
      `show_pattern_options` references. Commit:
      `Amend display-ux ADR for always-on pattern view`
- [x] **P1.5 — Update tutorials.** Remove `include=` from tutorial
      sources; `pixi run notebook-prepare`. Commit:
      `Drop include= from tutorials for unified pattern view`
- [x] **P1.6 — Phase 1 review gate.** Commit:
      `Reach Phase 1 review gate`

Each completed P1 step is staged with explicit paths and committed
locally before the next step (per `AGENTS.md` Commits). Stop after Phase
1 for review before Phase 2.

## Phase 2 — Verification

```bash
pixi run fix
pixi run check > /tmp/easydiffraction-check.log 2>&1; check_exit_code=$?; tail -n 200 /tmp/easydiffraction-check.log; exit $check_exit_code
pixi run unit-tests > /tmp/easydiffraction-unit.log 2>&1; unit_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-unit.log; exit $unit_tests_exit_code
pixi run integration-tests
pixi run script-tests
```

Test updates: remove `include=`/`show_pattern_options` tests; add
coverage for always-shown excluded regions, single-panel height + tight
x-range matching the composite main row, and the nothing-to-plot error.

## Status checklist

- [x] Phase 1 implementation complete
- [ ] Phase 1 reviewed
- [x] Phase 2 verification complete

## Suggested Pull Request

**Title:** Simplify and unify the experiment pattern view

**Description:** `project.display.pattern()` now always shows everything
the data supports — measured and calculated curves, the residual, Bragg
ticks, background, excluded regions, and uncertainty bands — so you no
longer pass `include=...` to assemble a view; just call
`pattern(expt_name=...)` and zoom with `x_min`/`x_max`. Excluded regions
are always shaded when defined. Single-panel and full three-panel charts
now share one layout, so a measured-only plot is exactly the top panel
of the full view — fixing the oversized height in the HTML docs and the
stray left/right margins. The 3D structure view also gains a little
breathing room below its title.
