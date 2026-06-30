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

**Current choice:** Option 2 (keeps the live-notebook extras). Revisit
Option 1 if the loader proves fragile across notebook frontends or the
maintenance cost outweighs the three behaviours.

**Depends on:** nothing.

**Recommended-priority note:** Marked **lowest**: records a settled
delivery decision (Option 2); no action required unless the loader
proves fragile.
