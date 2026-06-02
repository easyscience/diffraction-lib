# ADR: Plotting & Docs Performance for Interactive Figures

**Status:** Proposed **Date:** 2026-06-02

## Group

Documentation.

> This ADR follows [`AGENTS.md`](../../../../AGENTS.md). It spans the
> documentation build (MkDocs) and the display serialization contract,
> so it also relates to the User-facing API ADRs
> [`display-ux.md`](../accepted/display-ux.md) and
> [`crysview-structure-visualization.md`](../accepted/crysview-structure-visualization.md).
> No public Python API change is intended; the change is in how figure
> HTML and its JavaScript runtime are delivered.

## Context

### Symptom

Generated tutorial pages that contain many interactive figures (mostly
Plotly, plus the occasional Three.js crystal-structure view) can take
from several to a few dozen seconds before the page becomes responsive.
The plots are valuable and should stay interactive; the goal is to keep
interactivity while making the page usable immediately and letting plots
appear progressively.

### How figures reach a docs page today

1. Tutorial sources are `docs/docs/tutorials/ed-*.py`; notebooks are
   generated artifacts (per
   [`notebook-generation.md`](../accepted/notebook-generation.md)) and
   are committed with **outputs stripped** (`notebook-strip`).
2. The docs CI
   ([`.github/workflows/docs.yml`](../../../../.github/workflows/docs.yml))
   runs `notebook-exec-ci` to **execute** every notebook, baking the
   rendered cell outputs into the `.ipynb`, then `mkdocs build` with
   `mkdocs-jupyter` configured `execute: false` simply embeds those
   pre-rendered outputs into the HTML.
3. Each Plotly figure is emitted by `PlotlyPlotter._show_figure`
   ([`src/easydiffraction/display/plotters/plotly.py`](../../../../src/easydiffraction/display/plotters/plotly.py))
   as a `text/html` output via
   `serialize_html(fig, include_plotlyjs='cdn')` wrapped in
   `IPython.display.HTML`. The resulting HTML, **per figure**, carries:
   - a `<div>` plus an inline `<script>` calling `Plotly.newPlot(...)`
     with the full trace JSON,
   - a `<script src="https://cdn.plot.ly/plotly-*.min.js">` tag (from
     `include_plotlyjs='cdn'`),
   - roughly 15 KB of post-scripts (theme-sync + resize + legend toggle)
     **duplicated in every figure**.
4. `mkdocs.yml` additionally loads **RequireJS from a second CDN**
   (`include_requirejs: true`, commented "Required for Plotly").
5. Three.js structure views are produced by
   `ThreeJsStructureRenderer.render`
   ([`src/easydiffraction/display/structure/renderers/threejs.py`](../../../../src/easydiffraction/display/structure/renderers/threejs.py))
   with `offline=True` by default, which **base64-inlines the entire
   Three.js module set (~1.5 MB) into the HTML of every scene** and
   injects a per-scene `<script type="importmap">`.

### Why it is slow — two independent bottlenecks

- **Network / cold start.** A plot-heavy page depends on up to three
  external CDNs at view time: `cdn.plot.ly` (full Plotly bundle, ~3–4 MB
  minified, ~1 MB gzipped), `cdnjs` (RequireJS), and `jsdelivr`
  (Three.js, when not offline). For a scientific audience often behind
  slow or filtered institutional networks, this alone produces the
  multi-second-to-stall behavior. The Plotly bundle is fetched once and
  cached, but the page still blocks on it.
- **CPU / eager render.** Every `Plotly.newPlot` runs **synchronously as
  the page parses**. Fifteen to twenty figures means fifteen to twenty
  back-to-back layout+draw passes on the main thread before the page is
  interactive, regardless of whether a figure is on screen.

### Blast radius: one serializer, three delivery targets

The same serialization paths feed three contexts with **conflicting**
runtime needs, which is the crux of any robust fix:

| Target                | Who                                                                                         | Runtime requirement                                                                                                                                                                                                          |
| --------------------- | ------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Live notebook**     | `_show_figure` in Jupyter                                                                   | Runtime must be reachable from the running kernel/browser (today: Plotly via CDN; Three.js inlined).                                                                                                                         |
| **MkDocs site**       | executed-notebook HTML embedded by `mkdocs-jupyter`                                         | Wants the runtime loaded **once per page** and figures rendered **lazily**.                                                                                                                                                  |
| **Standalone report** | `report/html_renderer.py` → `PlotlyPlotter.serialize_html` / Three.js `render(offline=...)` | Delivery set by the existing `offline` flag — embedded/self-contained when `offline=True`, CDN when `offline=False` (default). Authoritative per [`project-summary-rendering.md`](../accepted/project-summary-rendering.md). |

A useful precedent already lives in the report renderer
([`src/easydiffraction/report/html_renderer.py`](../../../../src/easydiffraction/report/html_renderer.py)):
it embeds Plotly in the **first** figure and then passes
`include_plotlyjs=False` for the rest, so a multi-figure report ships
the runtime once. Docs do not get this because each notebook cell is
serialized independently with `'cdn'`. The robust direction is to
**generalize that "load once, reference after" idea across a whole docs
page**, and add lazy activation on top.

### Long-term-support constraint: versioned docs outlive CDNs

Docs are published with `mike` (versioned). A page built today that
links a moving CDN URL can silently break years later when the CDN drops
or changes that asset, leaving **old, frozen doc versions** unable to
render their figures. Pinning and self-hosting the runtime **per doc
version** makes each published version self-consistent and archival — a
strong reason to prefer self-hosting over any CDN for the long term.

### Known latent bug surfaced while investigating

Each Three.js scene injects its own `<script type="importmap">`. A page
with **two** structure views therefore emits two importmaps; multiple
importmaps are not reliably supported across browsers, so a second
structure view on one page can fail to load its modules. Hoisting a
single page-level importmap on docs pages (Decision 6) also fixes this;
standalone reports that render multiple scenes share the same latent bug
and are noted in **Deferred work**.

## Decision

Adopt **Option B: a shared, self-hosted figure runtime with lazy,
progressive activation**, driven by an explicit _embedding mode_ on the
serialization path. The following sub-choices were selected in
discussion on 2026-06-02 (see **Resolved decisions** below): a themed
"Loading…" **skeleton** placeholder (not static-image-first);
**committed canonical vendored snapshots** — only the Three.js
docs-serving copy is generated at build, while Plotly's docs-only
partial bundle is committed (Decision 1); and **Plotly and Three.js
delivered together** in one change. Concretely:

1. **Self-host pinned runtimes, no runtime CDN; committed canonical
   snapshots with an explicit docs-sync contract.** Each vendored
   runtime is a committed snapshot (as `src/.../vendor/threejs` is
   today) with exactly one canonical home, and the way it reaches the
   served site is named, not implicit:
   - **Three.js** — canonical at
     `src/.../display/structure/renderers/vendor/threejs` (the installed
     wheel needs it for offline reports and notebooks). MkDocs can only
     serve files under `docs/docs`, so the docs **serving** copy is
     **generated at build, not committed** (git-ignored under
     `docs/docs/assets/javascripts/vendor/`) by a new
     `docs-sync-vendored-js` pixi task that copies the canonical bytes.
     Wire that task as a `depends-on` of `docs-build` and `docs-serve`,
     and run it before `mkdocs build` in `docs.yml`, so local serve,
     local build, and CI stay in lockstep with one source of truth.
   - **Plotly** — a partial `plotly-cartesian` bundle (covers `Scatter`,
     `Heatmap`, bars, error bars, shapes, annotations, text; excludes
     unused WebGL/3D/maps). This runtime is **docs-only** — offline
     reports embed the full Plotly bundle from the installed `plotly`
     package, so no wheel copy exists — so its canonical home is the
     **committed** docs vendor dir
     `docs/docs/assets/javascripts/vendor/plotly/`, which is also where
     MkDocs serves it (no sync step needed).

   So the committed-vs-generated split is decided: vendored snapshots
   are committed at their canonical home; only the Three.js docs
   _serving_ copy is generated by `docs-sync-vendored-js`. Drift between
   a canonical snapshot and its pinned version is caught by
   `bump_vendored_js.py --check` (Decision 5), not by comparing two
   committed copies. Each runtime loads **once per page**: Plotly and
   the shared figure loader via `extra_javascript`, Three.js via a
   single page-level importmap. Drop the RequireJS CDN and
   `include_requirejs` if verification confirms it is no longer needed.

2. **Introduce a figure _embedding mode_** (a `(str, Enum)` per
   [`enum-backed-closed-values.md`](../accepted/enum-backed-closed-values.md))
   threaded through `serialize_html` and the Three.js `render`:
   - `INLINE` — live Jupyter: render eagerly with the runtime reachable
     as today. **Default.**
   - `SHARED` — docs: emit a **placeholder** (reserved aspect ratio,
     themed "Loading…" skeleton, no layout shift) plus the figure spec
     as a `<script type="application/json">` payload and a
     `data-ed-figure` hook; reference the page-shared runtime. **No**
     per-figure runtime, **no** per-figure post-scripts.
   - `STANDALONE` — reports: render eagerly into a self-contained
     fragment. Runtime delivery is **not** decided here but by the
     caller's existing `offline` flag (see Decision 4).

   **Mode routing (the central decision).** Tutorial figures are
   serialized during notebook _execution_ (`notebook-exec-ci`), before
   MkDocs sees them, and `mkdocs-jupyter` runs `execute: false` — so the
   already-baked cell HTML must itself carry `SHARED` output; no
   `extra_javascript` or downstream step can retrofit it. The active
   mode is therefore resolved **centrally** from an environment variable
   (`EASYDIFFRACTION_FIGURE_EMBED_MODE`) by one helper alongside
   `in_jupyter`/`in_pycharm` in `utils/environment.py`, validated to the
   enum and defaulting to `INLINE`. The docs notebook-execution tasks
   (`notebook-exec-ci`, and `notebook-exec` for local docs preview) set
   it to `shared`; ordinary Jupyter sessions leave it unset and stay
   `INLINE`. Reports never consult the variable — the report API passes
   `STANDALONE` explicitly. Because `SHARED` output is an inert
   placeholder plus JSON, notebook execution does **not** need the
   runtime present; MkDocs serves the runtime at view time (Decision 1).

3. **One shared `ed-figures.js`, loaded once per page**, owns what is
   currently duplicated per figure: it discovers `data-ed-figure`
   placeholders, lazily calls `Plotly.newPlot` (and boots Three.js
   scenes) via `IntersectionObserver` when each scrolls near the
   viewport, and centralizes theme-sync, resize, and legend-toggle
   logic. Eager fallback when `IntersectionObserver` is absent or when
   printing.

4. **Reports keep their existing `offline` contract, authoritative and
   unchanged.** Per
   [`project-summary-rendering.md`](../accepted/project-summary-rendering.md),
   `render_html_report(offline=...)` already decides runtime delivery:
   `offline=True` embeds a self-contained runtime; `offline=False` (the
   default) links the CDN, embedding Plotly in the first figure and
   referencing it thereafter. The embedding mode does **not** touch this
   — reports render `STANDALONE` (eager, self-contained _fragment_) and
   still pick embed-vs-CDN solely via `offline`. The `SHARED`/lazy
   shared-runtime mechanism is **docs-only** and never applies to
   reports. "Self-contained" is thus the `offline=True` report case, not
   a new blanket requirement on every report.

5. **A version-bump script + pixi task for the vendored runtimes.** Add
   `tools/bump_vendored_js.py`, mirroring the existing
   `tools/update_docs_assets.py` (same `pooch`-based fetch — `pooch` is
   already a dependency, so **no new dependency** is introduced). It
   reads a **single pinned table** (Plotly + Three.js versions, source
   URLs, and expected SHA-256 hashes), fetches each file from
   jsDelivr/npm with `pooch`'s `known_hash` integrity check, writes each
   into its canonical vendor home (Decision 1: `src/.../vendor/threejs`
   for Three.js, the committed docs vendor dir for Plotly), and
   **regenerates that home's `LICENSES.md`** in the existing format
   (`vendor/threejs/LICENSES.md`: file→source-URL table, version line,
   licence). Wire it as a pixi task alongside `docs-update-assets` (e.g.
   `vendor-update-js`). Bumping a runtime then becomes: edit the pinned
   version + hash, run one task, commit the refreshed snapshot and
   regenerated license. A `--check` mode (re-hash the vendored files
   against the pinned table without writing) can guard against drift or
   accidental edits in CI, complementing the `pyproject.toml` exclusion
   of vendored paths from lint/format. The pinned table is the single
   source of truth for the versions that the Three.js renderer
   (`_CDN`/import map) and the Plotly bundle reference, so `src` and
   docs cannot drift.

6. **Inject the page-level Three.js importmap via the Material theme
   override.** A page may hold several structure views, but a document
   can carry only one reliable `<script type="importmap">`, and it must
   precede any module script — so `extra_javascript` (which links plain
   `.js` files) cannot deliver it. Decision: emit **one** static
   importmap from the existing `docs/overrides/main.html` by adding an
   `{% block extrahead %}` that renders it into `<head>`, with entries
   resolved against `{{ base_url }}` so they stay correct under `mike`'s
   versioned subpaths:

   ```jinja
   {% block extrahead %}
     {{ super() }}
     <script type="importmap">
     {"imports": {
       "three": "{{ base_url }}/assets/javascripts/vendor/threejs/three.module.js",
       "three/addons/controls/OrbitControls.js": "{{ base_url }}/assets/javascripts/vendor/threejs/OrbitControls.js",
       "three/addons/renderers/CSS2DRenderer.js": "{{ base_url }}/assets/javascripts/vendor/threejs/CSS2DRenderer.js"
     }}
     </script>
   {% endblock %}
   ```

   In `SHARED` mode the Three.js renderer then emits **only** the module
   bootstrap (bare `three` / `three/addons/...` specifiers) and **no**
   per-scene importmap, so every scene on a page resolves against this
   single head-level map. `STANDALONE` reports are unaffected — they
   keep their self-contained inline importmap (a standalone file has no
   theme override). Injecting the map on every page is harmless where no
   scene consumes it (the tiny JSON is inert), keeping the override
   simple.

This pays the network bill once per page from the same origin, removes
the per-figure JS duplication, and turns first paint from "render every
figure" into "render nothing until seen" — addressing both bottlenecks
while keeping every plot fully interactive.

## Options considered

### Option A — Tactical: lazy activation only

Keep each figure's self-contained, CDN-loaded HTML exactly as today, but
wrap the existing per-figure post-script so `Plotly.newPlot` fires from
an `IntersectionObserver` behind a "Loading…" placeholder.

- **Pros:** smallest change; isolated to the post-script; delivers the
  "plots appear one by one" UX the request asked for.
- **Cons:** does **not** fix the network bottleneck (still CDN, still
  RequireJS, Three.js still inlined per scene, importmap bug remains);
  keeps ~15 KB × N duplicated post-scripts; leaves the long-term CDN
  fragility for versioned docs. Robustness: low.

### Option B — Shared self-hosted runtime + lazy activation _(recommended)_

As in **Decision** above: self-host pinned runtimes loaded once per
page, an explicit embedding mode, and a shared lazy loader.

- **Pros:** fixes **both** bottlenecks; firewall-proof and archival
  (versioned docs stay self-consistent); de-duplicates and centralizes
  figure JS (maintainability); fixes the importmap bug; generalizes the
  pattern reports already use; keeps reports self-contained.
- **Cons:** the most work now — touches `serialize_html`, the Three.js
  renderer, `mkdocs.yml`, a vendoring/build step, and a new shared JS
  asset; requires careful handling of the three delivery targets and of
  the live-notebook experience. Robustness: high. **Matches the stated
  preference to accept more work now for long-term robustness.**

### Option C — MkDocs post-processing plugin

Leave the Python serialization mostly as-is and add a custom MkDocs
plugin (or adopt `mkdocs-plotly-plugin`, already eyed in a `docs.yml`
comment) that post-processes built pages to strip duplicate runtimes,
inject one shared runtime, and add the lazy loader globally.

- **Pros:** centralizes behavior in the build; minimal Python display
  changes.
- **Cons:** adds a bespoke build dependency to maintain against MkDocs
  and Plotly upgrades; "spooky action" in a post-build pass that is
  harder to test than deterministic serialization;
  `mkdocs-plotly-plugin` targets `.plotly` JSON files in Markdown, not
  executed-notebook outputs, so it is not a drop-in. Robustness: medium,
  but with ongoing maintenance cost and weaker testability than B.

### Comparison

| Concern                                     | A — tactical | B — shared+lazy | C — plugin             |
| ------------------------------------------- | ------------ | --------------- | ---------------------- |
| Plots appear progressively                  | ✅           | ✅              | ✅                     |
| Removes runtime-CDN dependency              | ❌           | ✅              | ✅                     |
| Smaller runtime (partial bundle)            | ❌           | ✅              | possible               |
| De-duplicates per-figure JS                 | ❌           | ✅              | ✅                     |
| Fixes Three.js importmap bug                | ❌           | ✅              | maybe                  |
| Archival / version-frozen docs              | ❌           | ✅              | ✅                     |
| Reports keep `offline` contract (unchanged) | ✅           | ✅              | ✅                     |
| Implementation cost now                     | low          | high            | medium                 |
| Long-term maintenance cost                  | low          | low             | higher (custom plugin) |
| Testable in unit tests                      | partial      | ✅              | weak                   |

## Consequences

### Positive

- Page is responsive immediately; figures render on demand, one by one.
- One same-origin runtime fetch per page, cached across the site;
  partial bundle roughly halves the Plotly download.
- Per-figure HTML shrinks substantially (no embedded runtime, no
  duplicated post-scripts), so executed `.ipynb` artifacts and built
  pages are smaller.
- Versioned docs become self-consistent and archival; no runtime CDN.
- Theme-sync / resize / legend logic lives in one auditable place.
- The multiple-importmap Three.js bug is fixed.

### Negative / cost

- Larger change across display, report (verification only), docs build,
  and a new vendored asset + build step.
- Vendored runtimes must be kept current, but the bump script + pixi
  task (Decision 5) reduce this to editing a pinned version + hash and
  running one task; licenses regenerate and an optional `--check` mode
  guards against drift.
- The shared loader is now load-bearing for docs rendering; it needs its
  own tests and a no-/failed-JS fallback story.

### Neutral

- No intended change to public Python API or to how authors write
  tutorials; the figures look and behave the same, only faster.

## Risks and mitigations

- **Live-notebook rendering.** `SHARED` placeholders need the docs
  loader, so they must never reach a live Jupyter session. Settled by
  the env-var routing (Decision 2): only the docs notebook-execution
  tasks request `SHARED`; an unset variable resolves to `INLINE`. Cover
  the resolver with a unit test asserting both the default and the
  docs-build override.
- **Report `offline` contract.** Keep
  [`project-summary-rendering.md`](../accepted/project-summary-rendering.md)
  authoritative (Decision 4); the existing `offline=True` /
  `offline=False` report tests must stay green and gain no `SHARED`
  behavior.
- **Partial bundle missing a trace type.** Audit every trace/type used
  across tutorials and reports before pinning `plotly-cartesian`; fall
  back to the full bundle if any `scattergl`/3D/map usage exists.
- **`IntersectionObserver` / no-JS / print.** Provide eager fallback
  when the observer is unavailable and when `matchMedia('print')`
  matches, plus a `<noscript>` note.
- **RequireJS coupling.** `include_requirejs: true` exists for Plotly
  today; only drop it after confirming the self-hosted, `False`-mode
  output renders without it under `mkdocs-jupyter`.

## Resolved decisions

Settled in discussion on 2026-06-02:

1. **Placeholder fidelity → skeleton.** Use a themed "Loading…" skeleton
   with the figure's reserved aspect ratio (no layout shift). A
   static-image-first variant (kaleido/SVG pre-render upgrading to
   interactive) is **deferred**, not adopted now.
2. **Vendoring → committed canonical snapshots; only Three.js synced.**
   Three.js stays canonical in `src/.../vendor/threejs`; its docs
   _serving_ copy is generated at build by `docs-sync-vendored-js`. The
   Plotly partial bundle is docs-only and committed at its docs vendor
   home (offline reports use the full Plotly bundle from the `plotly`
   package, so it needs no wheel copy). One source of truth per runtime,
   drift-guarded by `bump_vendored_js.py --check` (Decisions 1 and 5).
3. **Scope/sequencing → both engines together.** Plotly and Three.js are
   delivered in one ADR/plan/change rather than staged.

## Remaining open questions

1. **Activation trigger.** Lazy on scroll-near only, or also a
   click-to-activate mode for the very heaviest figures? _Lean:
   scroll-near now; click-to-activate deferred unless a page proves
   pathological._
2. **RequireJS.** Remove `include_requirejs` outright, or keep it for
   safety during migration and drop it once the `False`-mode,
   self-hosted output is confirmed to render under `mkdocs-jupyter`?
   _Lean: keep during migration, remove in the same change after
   verification._

## Deferred work

- Static-image-first placeholders (kaleido) if skeletons prove
  insufficient on the heaviest pages.
- Trace downsampling for very dense series in the docs view (smaller
  payload + faster draw) — a separate, data-side optimization.
- A docs CI budget check (page weight / figure count) to catch
  regressions, aligning with
  [`documentation-ci-build.md`](suggestions/documentation-ci-build.md).
- Hoist a single importmap into the **report** template `<head>` for
  standalone reports that render multiple Three.js scenes (the same
  per-scene-importmap bug as docs, but governed by
  [`project-summary-rendering.md`](../accepted/project-summary-rendering.md)).
  Out of scope here since it touches the report contract; flagged so it
  is not lost.

## Alternatives considered

See **Options A and C** above; both are rejected in favor of B for
long-term robustness, though A is a viable fast first step if a staged
rollout is preferred (it is a strict subset of B's lazy-activation
work).
