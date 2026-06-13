# 110. Render Styled Multi-Line Table Cells in the HTML Backend

**Priority:** `[priority] low`

**Type:** Display / Notebook parity

`list_tutorials` shows a two-line cell in the terminal — a colored title
on the first line and a dimmed description on the second — using Rich
markup and an embedded newline. The Jupyter table backend
(`PandasTableBackend`) cannot render this: `_strip_rich_markup` only
matches a single full-cell `[color]text[/color]`, and HTML collapses the
newline, so the markup would show as literal text. `list_tutorials` is
therefore gated via `in_jupyter()` to show only the plain title in
notebooks, which drops the description and the color there.

**Fix:** teach the HTML backend to render the same styling — translate
embedded newlines to `<br>`, map `[dim]` to reduced opacity, and accept
multiple/mixed markup tags per cell — then remove the terminal-only gate
in `list_tutorials` so notebooks also get the styled two-line entry.

**Depends on:** related to issue 62.
