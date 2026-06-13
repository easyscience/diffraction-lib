# 118. Plotly Figures Show Empty Rows in the VISA JupyterLab

**Priority:** `[priority] lowest`

**Type:** Display / Environment

**Symptom.** In the **VISA-hosted, iframe-embedded** JupyterLab
(`visa.ess.eu/.../jupyter/.../lab`), every interactive Plotly figure is
preceded by several empty rows that fill in over ~1–2 s, and the plot
often renders collapsed. On a **standard local JupyterLab the branch is
fine** — the only issue there is the CDN race (issue addressed by the
self-hosted runtime; see below). So this is **specific to the VISA
environment**, not the library.

**Root cause (from a DOM inspection in VISA).** The plot element renders
at **height 0**, nested under
`div.jp-WindowedPanel-viewport.jp-content-visibility-mode`. VISA's
JupyterLab runs notebooks in **windowed mode** (`content-visibility`
virtualization). The output container is **0×0 at the moment Plotly
draws**, and because the figure config is `responsive: true`, Plotly
sizes to that 0×0 container and renders a zero-size plot that does not
recover. The "empty rows" are that collapsed zero-height output as the
viewport re-measures. This is a known Plotly ✕ JupyterLab-windowing
interaction.

**Workaround (user side).** JupyterLab → Settings → Notebook →
**Windowing mode = `defer`/`none`** disables the virtualization. (The
user reported this alone did **not** resolve it in VISA, so VISA may
force or wrap the setting — needs confirmation.)

**Attempts that did NOT resolve it in VISA** (all reverted to keep the
code minimal; recorded so they are not retried blindly):

- Self-hosted runtime instead of CDN, delivered as a single HTML output,
  as a `display(Javascript(...))` output, and as multiple/one inline
  `<script>` tags. (The self-hosting itself **is** kept — it fixes the
  real CDN race — but none of the delivery variants changed the VISA
  empty rows.)
- Removing the loading skeleton; removing then restoring the
  `min-height` reservation.
- Trimming the figure top margin + `title.automargin` (chasing a misread
  "default margin" theory).
- Preloading the runtime on `import easydiffraction` (regressed: added a
  visible empty output line on the import cell).
- Skipping the resize `ResizeObserver` for live figures.
- Reserving an explicit container height for windowing.
- Deferring the render until the container reports a non-zero size
  (`requestAnimationFrame` poll). This **did** get the plot to render at
  full height in VISA (DOM showed `h=565` instead of `0`), but the user
  still reported empty rows visually — so it is necessary-but-not-
  sufficient there.

**Promising future directions.** Set `responsive: false` with an
explicit width/height for live figures so Plotly never depends on the
0×0 container; or render the figure off-screen and swap it in once
sized; or detect the VISA/windowed environment and special-case it.
Needs to be developed and tested **inside VISA**, since it does not
reproduce on a standard JupyterLab.

**Depends on:** nothing. Lower priority — affects only the VISA
deployment, and a user-side windowing-mode change may suffice.

**Recommended-priority note:** Marked **lowest**: affects only the VISA-hosted JupyterLab, and a user-side windowing-mode change may suffice.
