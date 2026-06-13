# 111. Add Test Coverage for `list_tutorials` Two-Line Rendering

**Priority:** `[priority] low`

**Type:** Test coverage

The `list_tutorials` table gained a styled two-line cell (colored title
plus dimmed description), a terminal-only `in_jupyter()` gate that falls
back to the plain title, and a new optional `width` parameter on the
table render path. Existing tests only assert that titles appear in the
output.

**Fix:** add unit tests for the description line appearing in the
terminal (non-Jupyter) path, the Jupyter-gated path showing the plain
title with no literal Rich markup, and the `width` parameter sizing the
rendered Rich table. Run `pixi run fix` / `check` / `unit-tests` to
confirm the shared-renderer signature change.

**Depends on:** nothing.
