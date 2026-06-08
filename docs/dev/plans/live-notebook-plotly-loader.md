# Plan: Reliable live-notebook Plotly rendering (shared loader)

Follows [`AGENTS.md`](../../../AGENTS.md). Implements the live-notebook
half of the embedding strategy in
[`plotting-docs-performance.md`](../adrs/accepted/plotting-docs-performance.md)
— that ADR self-hosts the runtime and adds a lazy loader for the **docs
site (SHARED mode)** but explicitly leaves the **live notebook** path on
`include_plotlyjs='cdn'`. This plan brings the same self-hosted,
loader-driven rendering to live notebooks.

## Problem

In JupyterLab the live path is
`PlotlyPlotter._show_figure` → `display(HTML(serialize_html(fig,
include_plotlyjs='cdn', mode=INLINE)))`. Two user-visible bugs:

1. **Empty first plot after kernel restart.** The CDN `<script src>`
   loads `plotly.js` asynchronously while the inline `Plotly.newPlot`
   runs immediately on HTML injection → the first render races ahead of
   the library and draws nothing; re-running the cell works because the
   library is now cached.
2. **Loading gap / "blank lines fill in one by one."** The figure div
   reserves its layout height while empty during the async load, so a
   tall blank block sits above the plot until plotly.js arrives.

Both stem from the INLINE/CDN delivery. The docs site does not have
this because SHARED mode loads one self-hosted runtime + the
`ed-figures.js` loader once per page.

## Approach (Option 2 — chosen)

Reuse the **existing SHARED loader** for live notebooks instead of
inventing per-figure scripts:

- `ed-figures.js` already does idempotent (`data-ed-rendered`) lazy
  render via `IntersectionObserver`, plus theme-sync, resize, and the
  modebar legend-toggle (`render()`/`activate()` at
  `docs/docs/assets/javascripts/ed-figures.js:340-401`). Driving live
  figures through it **keeps every feature** — nothing is lost relative
  to today's per-figure post-scripts.
- Emit each live figure as the **SHARED placeholder** (spec JSON in a
  `<script type="application/json" class="ed-figure-spec">` + a
  `min-height` target div), exactly like `_serialize_html_shared`.
- Inject the **runtime + loader once per kernel session**; re-trigger
  the loader for figures that appear after the initial page load (new
  notebook cells).

This is CDN-free (archival, works on filtered institutional networks),
matches the docs delivery, and removes the race (render only fires from
the loader, which only runs once `window.Plotly` exists).

## Decisions

- **D1 — Reuse `ed-figures.js`; do not duplicate post-scripts.** Refactor
  it to expose a re-callable global (e.g.
  `window.edFigures.activate()`), idempotent and safe to call after
  every cell. Keep the IIFE auto-activate on `DOMContentLoaded` for
  docs.
- **D2 — Ship the loader and runtime in the wheel.** `ed-figures.js`
  becomes a vendored asset under `src/easydiffraction/display/` (single
  source of truth) and the docs copy is synced from `src/` (mirror the
  Three.js arrangement in `tools/sync_docs_vendored_js.py`), instead of
  the docs holding the only copy.
- **D3 — Runtime source = the vendored cartesian bundle**
  (`plotly-cartesian.min.js`, ~1.4 MB), packaged into the wheel and
  injected **once per session**. Rationale: CDN-free + archival per the
  ADR, byte-identical to the docs runtime. (Alternative considered:
  `plotly.io.get_plotlyjs()` — no new vendored file, but ~3.5 MB and a
  different bundle than docs. See Open question O1.)
- **D4 — Session-scoped injection.** A module/class flag tracks whether
  the runtime+loader were injected for the current kernel. First INLINE
  `_show_figure` emits them; subsequent figures emit only the
  placeholder + a tiny idempotent `<script>` that calls
  `window.edFigures.activate()` (which no-ops already-rendered figures
  and renders new ones).
- **D5 — Scope unchanged elsewhere.** SHARED (docs) and STANDALONE
  (report) paths are untouched. PyCharm/`fig.show()` fallback unchanged.

## Open questions (resolved)

1. **O1 — runtime bundle. RESOLVED: vendored cartesian bundle in the
   wheel.** Ship the 1.4 MB `plotly-cartesian.min.js` as wheel data and
   inject once per session — CDN-free, docs-identical, archival per the
   ADR. (+1.4 MB wheel accepted.)
2. **O2 — reopened-notebook trust. RESOLVED: accept + document.** A
   reopened `.ipynb` renders on reload only when the notebook is
   **trusted** (JupyterLab re-runs output `<script>`s only then).
   Untrusted notebooks show nothing — the same constraint as today's CDN
   output. Documented as a known limitation.
3. **O3 — branch. RESOLVED: current branch
   (`more-validation-notebooks`).**

## Concrete files likely to change

- `src/easydiffraction/display/plotters/plotly.py` — `_show_figure`
  INLINE branch: emit SHARED-style placeholder; inject runtime+loader
  once per session; per-figure activate script. New session-flag helper.
- `ed-figures.js` — refactor to expose `window.edFigures.activate()`
  (idempotent, re-callable); move canonical copy to
  `src/easydiffraction/display/.../vendor/` and sync to docs.
- `tools/bump_vendored_js.py` / `tools/sync_docs_vendored_js.py` —
  treat Plotly bundle (and `ed-figures.js`) as wheel-shipped, synced to
  docs like Three.js.
- `pyproject.toml` — package-data / force-include for the vendored
  `*.js` (loader + plotly bundle) so they ship in the wheel; exclude
  from lint/format/coverage like other vendored JS (already covered by
  `*/vendor/*`).
- `docs/mkdocs.yml` — point `extra_javascript` at the synced asset
  paths if they move; otherwise unchanged.
- `tests/unit/easydiffraction/display/plotters/test_plotly_coverage.py`
  — assert INLINE output is placeholder-shaped, runtime injected exactly
  once per session, subsequent figures reference-only.

## Implementation steps (Phase 1)

- [ ] **P1.1 — Vendor the loader into `src/` and sync to docs.** Move
  `ed-figures.js` to a `src/easydiffraction/display/` vendor folder;
  update `sync_docs_vendored_js.py` to copy it (and Plotly) to docs;
  regenerate the docs copy. Commit: `Vendor ed-figures loader into the
  package`.
- [ ] **P1.2 — Expose a re-callable loader global.** Refactor
  `ed-figures.js` so `activate()` is reachable as
  `window.edFigures.activate()` and safe to call repeatedly; keep
  auto-activate for docs. Commit: `Expose re-callable edFigures.activate`.
- [ ] **P1.3 — Package the Plotly runtime in the wheel.** Add the
  vendored `plotly-cartesian.min.js` as wheel data; wire
  `bump_vendored_js.py`. Commit: `Ship vendored Plotly bundle in the
  wheel`.
- [ ] **P1.4 — Session-scoped runtime/loader injection.** Add the
  per-kernel flag + a helper that returns the one-time
  runtime+loader `<script>` block. Commit: `Inject Plotly runtime once
  per kernel session`.
- [ ] **P1.5 — Switch the INLINE path to the shared placeholder.**
  `_show_figure` INLINE emits the SHARED-style placeholder + an
  idempotent activate script; drop `include_plotlyjs='cdn'` for live.
  Commit: `Render live figures through the shared loader`.
- [ ] **P1.6 — Phase 1 review gate.** No-code checklist close-out.

## Phase 2 — Verification

```
pixi run fix
pixi run check > /tmp/ed-check.log 2>&1; check_exit_code=$?; tail -n 80 /tmp/ed-check.log; exit $check_exit_code
pixi run unit-tests
pixi run notebook-tests   # executes notebooks; confirms figures still serialize
```

Manual JupyterLab smoke test (cannot be automated here): kernel
restart → first plot renders (no empty/no race); no loading gap;
multiple plots; reopen trusted notebook → all figures render.

## Suggested Pull Request

**Title:** Make interactive plots render reliably in JupyterLab

**Description:** Fixes two annoyances when using EasyDiffraction in
JupyterLab: the first plot after a kernel restart sometimes came up
blank until you re-ran the cell, and plots could appear below a
flickering empty gap while loading. Plots now use the same fast,
self-hosted plot runtime the documentation site uses — no external
download — so they appear reliably and without the gap.
