# Plan: Plotting & Docs Performance for Interactive Figures

This plan follows [`AGENTS.md`](../../../AGENTS.md). It applies the
two-phase workflow (Phase 1 implementation, Phase 2 verification) and
the per-step commit discipline described there. No deliberate exceptions
to `AGENTS.md` are taken.

## ADR

This plan **owns** the ADR
[`plotting-docs-performance.md`](../adrs/suggestions/plotting-docs-performance.md)
(drafted via `/draft-adr`; Status: Proposed, not yet committed). It also
references these accepted ADRs (no change to them is intended):

- [`project-summary-rendering.md`](../adrs/accepted/project-summary-rendering.md)
  — the report `offline` contract stays authoritative.
- [`crysview-structure-visualization.md`](../adrs/accepted/crysview-structure-visualization.md)
  — the Three.js renderer this plan extends.
- [`display-ux.md`](../adrs/accepted/display-ux.md) — display facade.
- [`enum-backed-closed-values.md`](../adrs/accepted/enum-backed-closed-values.md)
  — `FigureEmbedMode` is a `(str, Enum)`.
- [`notebook-generation.md`](../adrs/accepted/notebook-generation.md) —
  tutorial `.py` are sources, notebooks are generated.

**For `/draft-impl-1` Phase A:** the ADR is owned by this plan. Remove
the design-phase `plotting-docs-performance_review-*.md` / `_reply-*.md`
siblings, **promote** the ADR (set Status to `Accepted`, `git mv` it to
`docs/dev/adrs/accepted/`), add a matching row to
[`docs/dev/adrs/index.md`](../adrs/index.md) (Group: Documentation), and
commit with message `Promote plotting-docs-performance ADR to accepted`.

## Branch and PR

- Intended branch: **`plotting-docs-performance`** (flat slug off
  `develop`, no `feature/` prefix). PR targets `develop`.
- Per the shortcut preamble, implementation stays on the **current**
  branch; do not switch or create branches. (The working tree is
  currently on `space-group-database`; the maintainer decides when to
  rebranch.)
- Do not push the branch unless asked.

## Decisions (from the ADR)

1. **Self-hosted, pinned, committed runtime snapshots; no runtime CDN.**
   Three.js canonical home stays
   `src/easydiffraction/display/structure/renderers/vendor/threejs` (the
   wheel needs it); its docs **serving** copy is **generated at build**
   (git-ignored) by a new `docs-sync-vendored-js` task. The Plotly
   `plotly-cartesian` partial bundle is **docs-only** and **committed**
   under `docs/docs/assets/javascripts/vendor/plotly/`.
2. **`FigureEmbedMode` `(str, Enum)`** — `INLINE` (live Jupyter,
   default), `SHARED` (docs: placeholder + JSON payload + lazy), and
   `STANDALONE` (reports: eager fragment, delivery via existing
   `offline` flag). Resolved centrally from
   `EASYDIFFRACTION_FIGURE_EMBED_MODE` in `utils/environment.py`.
3. **One shared `ed-figures.js`** loaded once per page: lazy
   `IntersectionObserver` activation behind a themed "Loading…"
   skeleton, plus centralized theme-sync / resize / legend logic.
4. **Reports unchanged** — keep the `offline` contract from
   `project-summary-rendering.md`; `SHARED`/lazy is docs-only.
5. **`tools/bump_vendored_js.py` + `vendor-update-js` task** — pinned
   table (versions, URLs, SHA-256), `pooch` fetch with `known_hash`,
   regenerates each `LICENSES.md`, `--check` drift mode. No new
   dependency (`pooch` already present).
6. **Page-level Three.js importmap** injected via
   `{% block extrahead %}` in `docs/overrides/main.html`, paths resolved
   against `{{ base_url }}`; `SHARED` scenes drop their per-scene
   importmap.

## No new dependencies

This plan adds **no** Python runtime or dev dependency. `plotly` and
`pooch` are already declared; Three.js and the Plotly partial bundle are
**vendored static JS assets**, not packages. Edits to `pixi.toml` are
**task definitions only** (not `[dependencies]`/`[pypi-dependencies]`),
and `pyproject.toml` is **not** modified. If any Phase 2 fix appears to
need a new dependency, stop and ask per `AGENTS.md` §Planning.

## Open questions (leans recorded; resolve during implementation)

1. **Activation trigger.** Scroll-near lazy only (lean: yes);
   click-to-activate deferred unless a page proves pathological.
2. **RequireJS.** Keep `include_requirejs: true` through Phase 1; in
   Phase 2, after confirming the self-hosted `include_plotlyjs=False`
   output renders under `mkdocs-jupyter`, remove it. If removal breaks
   rendering, keep it and note why.

## Concrete files likely to change

**Source (`src/`)**

- `utils/environment.py` — add `FigureEmbedMode` enum +
  `resolve_figure_embed_mode()` (reads
  `EASYDIFFRACTION_FIGURE_EMBED_MODE`, default `INLINE`, validated to
  the enum).
- `utils/__init__.py` — export the new symbols if they need to be
  public.
- `display/plotters/plotly.py` — thread mode through `serialize_html`
  and `_show_figure`; `SHARED` emits placeholder + `application/json`
  payload + `data-ed-figure` hook with `include_plotlyjs=False` and no
  per-figure post-scripts; `INLINE`/`STANDALONE` keep current output.
- `display/structure/renderers/threejs.py` +
  `display/structure/templates/structure.html.j2` — add mode; `SHARED`
  drops the per-scene importmap (bare specifiers), emits a placeholder +
  `data-ed-figure` lazy boot; `STANDALONE` keeps the inline data-URL
  importmap.
- `display/structure/viewing.py` — pass the resolved mode into
  `render(...)`.
- `report/html_renderer.py` — pass `STANDALONE` explicitly in
  `_fit_figure_html_context` / `_structure_figure_html_context`,
  preserving the `offline` contract.

**Docs (`docs/`)**

- `docs/docs/assets/javascripts/ed-figures.js` — new shared loader.
- `docs/docs/assets/javascripts/vendor/plotly/plotly-cartesian.min.js`
  - `LICENSES.md` — committed vendored Plotly bundle.
- `docs/docs/assets/javascripts/vendor/threejs/` — **generated**
  (git-ignored) docs copy of the canonical Three.js.
- `docs/docs/assets/stylesheets/extra.css` — skeleton placeholder
  styles.
- `docs/mkdocs.yml` — `extra_javascript` (Plotly bundle +
  `ed-figures.js`), `extra_css` if separate; RequireJS removal in
  Phase 2.
- `docs/overrides/main.html` — `{% block extrahead %}` importmap.

**Tooling / build**

- `tools/bump_vendored_js.py` — new bump/`--check` script.
- `pixi.toml` — new `vendor-update-js` and `docs-sync-vendored-js`
  tasks; wire `docs-sync-vendored-js` as `depends-on` of `docs-build`
  and `docs-serve`; set `EASYDIFFRACTION_FIGURE_EMBED_MODE=shared` on
  `notebook-exec-ci` and `notebook-exec`.
- `.gitignore` — ignore the generated
  `docs/docs/assets/javascripts/vendor/threejs/`.
- `.github/workflows/docs.yml` — run `docs-sync-vendored-js` before
  `mkdocs build` (belt-and-braces with the `depends-on`).
- `src/.../vendor/threejs/LICENSES.md` — regenerated by the bump script.

## Implementation steps (Phase 1)

Phase 1 is **code and docs only — no tests** (tests are added in Phase
2). After completing each step, stage the step's files **with explicit
paths** and commit locally with the given message **before** starting
the next step (per `AGENTS.md` §Commits). Keep commits atomic and
single-purpose. If a step uncovers a serious design gap or a need for a
dependency the plan does not name, **stop and ask**.

- [x] **P1.1 — Add `FigureEmbedMode` enum and env resolver.** In
      `utils/environment.py`, add the `(str, Enum)` with `INLINE` /
      `SHARED` / `STANDALONE` and `resolve_figure_embed_mode()` reading
      `EASYDIFFRACTION_FIGURE_EMBED_MODE`. **Strict validation:** an
      unset or empty variable resolves to `INLINE`; any other non-empty
      value that is not an enum member raises a clear `ValueError`
      naming the bad value and listing the supported values (`inline`,
      `shared`, `standalone`) — never a silent fallback, so a typo in a
      docs/CI env fails the build loudly instead of baking eager CDN
      HTML. Export from `utils/__init__.py` if needed. Commit:
      `Add FigureEmbedMode enum and env resolver`

- [x] **P1.2 — Add the vendored-JS bump script and task.** Create
      `tools/bump_vendored_js.py` (pinned table of Plotly + Three.js
      versions/URLs/SHA-256, `pooch` fetch with `known_hash`, regenerate
      `LICENSES.md`, `--check` mode). Add the `vendor-update-js` pixi
      task. Do not run network fetches in CI/tests. Commit:
      `Add vendored-JS bump script and pixi task`

- [ ] **P1.3 — Vendor Plotly and refresh Three.js.** Run
      `pixi run vendor-update-js` to fetch `plotly-cartesian.min.js`
      into the committed docs vendor dir and refresh the Three.js
      snapshot + regenerate both `LICENSES.md`. Stage the vendored
      assets explicitly. Commit:
      `Vendor plotly-cartesian and refresh three.js`

- [ ] **P1.4 — Add `docs-sync-vendored-js` and wire it.** Add the pixi
      task copying canonical Three.js →
      `docs/docs/assets/javascripts/ vendor/threejs/`; git-ignore that
      path; add `depends-on` on `docs-build` and `docs-serve`; add a
      sync step before `mkdocs build` in `docs.yml`. Commit:
      `Add docs-sync-vendored-js task and wiring`

- [ ] **P1.5 — Add the shared `ed-figures.js` loader + skeleton CSS.**
      Implement `IntersectionObserver` lazy activation for
      `data-ed-figure` placeholders (Plotly `newPlot` + Three.js boot),
      centralized theme-sync / resize / legend logic, eager fallback
      when no observer or when printing; add the "Loading…" skeleton
      styles to `extra.css`. Commit:
      `Add shared ed-figures.js lazy figure loader`

- [ ] **P1.6 — Wire docs runtime assets and the page importmap.** Add
      the Plotly bundle + `ed-figures.js` to `extra_javascript` (and
      skeleton CSS to `extra_css` if separate) in `mkdocs.yml`; add the
      `{% block extrahead %}` importmap to `overrides/main.html`. (Leave
      `include_requirejs` in place for now — Phase 2 removes it.)
      Commit: `Wire docs runtime assets and page importmap`

- [ ] **P1.7 — Add `SHARED` mode to the Plotly serializer.** Thread the
      mode through `serialize_html` and `_show_figure`; in `SHARED` emit
      placeholder + `application/json` payload + `data-ed-figure`,
      `include_plotlyjs=False`, no per-figure post-scripts.
      `_show_figure` resolves the mode via
      `resolve_figure_embed_mode()`. Commit:
      `Add SHARED embedding mode to Plotly serializer`

- [ ] **P1.8 — Add `SHARED` mode to the Three.js renderer.** Thread the
      mode through `render(...)` (`viewing.py` + `threejs.py`) and
      `structure.html.j2`; `SHARED` drops the per-scene importmap (bare
      specifiers) and emits a placeholder + lazy boot; `STANDALONE`
      keeps the inline data-URL importmap. Commit:
      `Add SHARED embedding mode to Three.js renderer`

- [ ] **P1.9 — Pass `STANDALONE` from the report renderer.** Update
      `report/html_renderer.py` to pass `STANDALONE` into
      `serialize_html` / `render`, preserving the `offline` contract
      exactly. Commit: `Pass STANDALONE mode from report renderer`

- [ ] **P1.10 — Route docs notebook execution to `SHARED`.** Set
      `EASYDIFFRACTION_FIGURE_EMBED_MODE=shared` on `notebook-exec-ci`
      and `notebook-exec` in `pixi.toml`. This is the switch that makes
      baked cell HTML carry `SHARED` output; live Jupyter stays
      `INLINE`. Commit: `Route docs notebook execution to SHARED mode`

- [ ] **P1.11 — Phase 1 review gate (no code).** Mark this item `[x]`,
      commit the checklist update alone, then hand off to
      `/review-impl-1`. Commit: `Reach Phase 1 review gate`

## Verification (Phase 2)

Add/update tests first (mirroring the source tree; verify with
`pixi run test-structure-check`), then run the task suite. Capture logs
with the zsh-safe pattern and preserve the exit code.

**Tests to add/update**

- `tests/unit/easydiffraction/utils/test_environment*.py` —
  `resolve_figure_embed_mode()`: unset/empty → `INLINE`; `shared` →
  `SHARED`; `standalone` → `STANDALONE`; and an unknown non-empty value
  raises `ValueError` whose message contains both the bad value and the
  supported values.
- `tests/unit/easydiffraction/display/plotters/test_plotly*.py` —
  `SHARED` output contains the placeholder + `application/json`
  payload + `data-ed-figure`, **no** inline Plotly runtime and **no**
  per-figure post-scripts; `INLINE`/`STANDALONE` output unchanged.
- `tests/unit/easydiffraction/display/structure/renderers/test_threejs*.py`
  — `SHARED` emits bare-specifier bootstrap and **no** per-scene
  importmap; `STANDALONE`/offline keeps the inline importmap.
- Report tests — existing `offline=True`/`offline=False` behavior stays
  green and now asserts `STANDALONE` is used.
- A `tools/` test for `bump_vendored_js.py --check` drift detection (no
  network — monkeypatch/`pooch` fixture), mirroring
  `tools/test_structure_check.py`.

**Trace-type audit** — confirm no WebGL/3D/map trace types are used
anywhere; if any are found, switch the vendored bundle from
`plotly-cartesian` to the full bundle and re-vendor. Run this single
line:

```bash
git grep -nE "go\.(Scattergl|Scatter3d|Surface|Mesh3d|Cone|Streamtube|Volume|Isosurface|Scattermapbox|Choroplethmapbox|Densitymapbox|Scattergeo|Choropleth)" -- src docs || echo "no gl/3d/map traces; plotly-cartesian suffices"
```

**RequireJS** — after confirming docs render with the self-hosted
`include_plotlyjs=False` output, remove `include_requirejs: true` from
`mkdocs.yml` (open question 2). Commit separately.

**Command suite** (run in order; fix → commit → re-run until clean):

```bash
pixi run fix
pixi run test-structure-check > /tmp/easydiffraction-structure.log 2>&1; structure_check_exit_code=$?; tail -n 200 /tmp/easydiffraction-structure.log; exit $structure_check_exit_code
pixi run check > /tmp/easydiffraction-check.log 2>&1; check_exit_code=$?; tail -n 200 /tmp/easydiffraction-check.log; exit $check_exit_code
pixi run unit-tests > /tmp/easydiffraction-unit.log 2>&1; unit_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-unit.log; exit $unit_tests_exit_code
pixi run integration-tests > /tmp/easydiffraction-integration.log 2>&1; integration_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-integration.log; exit $integration_tests_exit_code
pixi run script-tests > /tmp/easydiffraction-script.log 2>&1; script_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-script.log; exit $script_tests_exit_code
```

**Docs build smoke** (not a unit test — confirms sync + importmap +
assets resolve, and that figures lazy-load):

```bash
pixi run docs-sync-vendored-js && pixi run docs-build-local > /tmp/easydiffraction-docs.log 2>&1; docs_exit_code=$?; tail -n 120 /tmp/easydiffraction-docs.log; exit $docs_exit_code
```

Notes: `pixi run fix` regenerates `docs/dev/package-structure/*.md`
automatically — accept and include them. Leave generated benchmark CSVs
and `docs/site/` untracked. For tutorial project-path collisions in
`script-tests`, fix the tutorial **source** and
`pixi run notebook-prepare`.

## Status checklist

- [ ] Phase 1 complete (P1.1–P1.11 committed)
- [ ] Phase 1 review cycle closed (`/review-impl-1` sentinel)
- [ ] Phase 2 tests added; `test-structure-check` + the five task
      commands clean
- [ ] Docs build smoke passes; figures load lazily
- [ ] RequireJS decision applied
- [ ] Phase 2 review cycle closed (`/review-impl-2` sentinel)
- [ ] ADR promoted to `accepted/` and indexed
- [ ] PR opened against `develop`

## Suggested Pull Request

**Title:** Faster, progressively-loading tutorial and documentation
pages

**Description (for users):** Documentation pages that contain many
interactive charts — especially the tutorials — now become usable almost
immediately instead of pausing for several seconds while every plot
draws at once. Plots now appear progressively as you scroll, each
showing a brief "Loading…" placeholder, and they stay **fully
interactive** as before. The charting libraries (Plotly and the 3D
structure viewer) are now served directly from the documentation site
rather than fetched from external servers, so pages also load reliably
on restricted or slow institutional networks and keep working for older,
archived documentation versions. A simple maintenance command keeps
those bundled libraries up to date. Nothing changes about how tutorials
are written.
