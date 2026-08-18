# 117. Live-Notebook Plotly Delivery: Loader vs Native Mimetype

**Priority:** `[priority] lowest`

**Type:** Display / Architecture

Records the two viable strategies for rendering interactive Plotly
figures in live notebooks, so the trade-off is not re-litigated. See
[`plotting-docs-performance.md`](../../adrs/accepted/plotting-docs-performance.md).

**Background.** Live notebooks historically rendered via
`display(HTML(pio.to_html(..., include_plotlyjs='cdn')))`, which caused
an empty first plot after kernel restart (the CDN `<script src>` loaded
asynchronously while `Plotly.newPlot` ran immediately) and a loading
gap. Two ways to fix it:

- **Option 1 — Native mimetype renderer (`fig.show()`).** Emit the
  `application/vnd.plotly.v1+json` mime bundle and let the JupyterLab
  Plotly extension render it. Pros: simplest, lowest maintenance,
  officially supported, no CDN, no script-in-output artifacts. Cons:
  live notebooks lose the three custom post-script behaviours (dynamic
  theme-sync on JupyterLab light/dark toggle, hidden-tab resize, the
  modebar legend-toggle button); a saved `.ipynb`'s plot output is the
  spec JSON, not self-contained HTML.

- **Option 2 — Self-hosted loader (current).** Ship the vendored Plotly
  bundle + the shared `ed-figures.js` loader in the wheel; the first
  figure injects them once per kernel session and each figure renders
  via `window.edFigures.renderSpec(id, spec)` delivered as a
  `display(Javascript(...))` output, so the HTML output is just the plot
  div (no `<script>` tags some hosts render as empty rows). Pros: keeps
  all three custom behaviours; CDN-free/archival; unified with the docs
  delivery. Cons: more moving parts; depends on the notebook being
  **trusted** for a reopened (not re-run) notebook to re-render.

- **Colab transport — versioned frame-local assets.** Colab isolates
  every cell output in its own iframe, so the once-per-kernel browser
  state assumed by Option 2 cannot cross cells. In Colab only, every
  figure output loads the version-matched Plotly bundle and
  `ed-figures.js` from the published documentation assets in parallel
  (the loader only needs Plotly once it renders), then calls the same
  `renderSpec` entry point. `google.colab.output.pauseOutputUntil` holds
  the output frame until the figure — or a visible error message — is on
  screen. Colab pauses outputframe auto-resizing (and the cell's later
  outputs) while that promise is pending, so the bootstrap asks for a
  remeasure just after it resolves; otherwise the height taken before
  the plot replaced its placeholder stays as blank space below the
  chart. That request is scheduled on the next paint with a timer
  backstop, because a hidden browser tab never paints. Where that API is
  absent, the fallback measures Colab's output area — every output of
  the cell, so siblings are not clipped — rather than the root scroll
  height, which is clamped to the frame viewport and so can only grow
  it. Concurrent outputs in one cell share frame-global loading
  promises, so each asset is fetched and parsed only once. An immutable,
  exact-release-tag jsDelivr URL is the fallback while a new
  documentation version is deploying or if that deployment fails. Dev
  builds intentionally use only `/dev/` to avoid mixing arbitrary local
  code with the loader from another revision. The browser cache avoids
  embedding or repeatedly transferring the runtime, while all
  loader-owned theme, resize, and legend behaviour remains intact.
  Documentation `SHARED` mode is selected first and is unaffected.

  Saved Colab outputs still depend on the host restoring their dynamic
  scripts. Until that behaviour is confirmed manually, reopen-and-view
  without re-running is not guaranteed; re-run a cell if its restored
  output remains at the loading placeholder. An end-to-end test of a dev
  build likewise requires its matching loader to have reached `/dev/`.

**Current choice:** Option 2 for JupyterLab, with the frame-local asset
transport for Colab. Revisit Option 1 if the loader proves fragile
across notebook frontends or the maintenance cost outweighs the three
behaviours.

**Depends on:** nothing.

**Recommended-priority note:** Marked **lowest**: records a settled
delivery decision (Option 2); no action required unless the loader
proves fragile.
